from . import api
from lghome.utils.comments import login_required
from flask import g, request, jsonify, session
from lghome.response_code import RET
from lghome.libs.image_store import storage
from sqlalchemy.exc import IntegrityError
from lghome.libs.image_store import storage
import logging
from lghome.models import Area, House, Facility, HouseImage, User, Order
from lghome import db, redis_store
from lghome import contants
from datetime import datetime
import json


@api.route("/areas")
def get_area_info():
    """
    获取城区信息
    :return:
    """
    # 从redis里读取数据
    try:
        response_json = redis_store.get("area_info")
    except Exception as e:
        logging.error(e)
    else:
        # redis 有缓存数据
        if response_json is not None:
            response_json = json.loads(response_json)
            # print(response_json)
            # print("--",type(response_json['data']))
            return jsonify(errno=RET.OK, errmsg='OK', data=response_json['data'])

    # 查询数据库 获取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    area_dict_li = []
    for area in area_li:
        area_dict_li.append(area.to_dict())
    # 将数据转成json字符串
    response_dict = dict(data=area_dict_li)
    # response_dict = dict(area_dict_li)
    response_json = json.dumps(response_dict)
    try:
        redis_store.setex("area_info", contants.AREA_INFO_REDIS_CACHE_EXPIRES, response_json)
    except Exception as e:
        logging.error(e)
    # print("--",type(area_dict_li))
    return jsonify(errno=RET.OK, errmsg='ok', data=area_dict_li)


@api.route("/houses/info", methods=['POST'])
@login_required
def save_house_info():
    """
    保存房屋的基本信息
    :return: 保存失败/成功
    """
    """
    title: "1",
    price: "111",
    area_id: "1",
    address: "11",
    room_count: "1",
    acreage: "12",
    unit: "212",…}
    facility:["2", "10", "12"]
    """
    # 发布房源信息
    user_id = g.user_id

    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数 2
    max_days = house_data.get("max_days")  # 最大入住天数 1
    # facility = house_data.get("facility")  # 设备信息

    # 校验参数
    if not all([title, price, area_id, address, acreage, room_count, unit]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 判断价格是否正确
    try:
        price = int(float(price) * 100)  # 分
        deposit = int(float(deposit) * 100)  # 分
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数参数错误')

    # 判断区域id
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='数据库异常')

    if area is None:
        return jsonify(errno=RET.PARAMERR, errmsg='城区信息有误')

    # 保存房屋信息
    house = House(
            user_id=user_id,
            area_id=area_id,
            title=title,
            price=price,
            address=address,
            room_count=room_count,
            acreage=acreage,
            unit=unit,
            capacity=capacity,
            beds=beds,
            deposit=deposit,
            min_days=min_days,
            max_days=max_days
    )
    # 设施信息
    facility_ids = house_data.get("facility")

    if facility_ids:
        # ['23', '44']
        # 查看是否存在
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常')

        if facilities:
            # 表示有合法的设备
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK', data={"house_id": house.id})


@api.route("/houses/image", methods=['POST'])
@login_required
def save_house_image():
    """
    保存房源图片
    ：param: house_id 房屋的id  house_image 房屋的图片
    :return: iamge_url  图片的地址
    """
    # 接收参数
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    # 校验
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 图片上床到七牛云你
    image_data = image_file.read()
    try:
        filename = storage(image_data)
    except Exception as e:
        logging.error(e)

        return jsonify(errno=RET.THIRDERR, errmsg='图片保存失败')

    # 保存图片信息到数据库
    house_image = HouseImage(house_id=house_id, url=filename)
    db.session.add(house_image)

    # 处理房屋的主图
    if not house.index_image_url:
        house.index_image_url = filename
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    image_url = contants.QINIU_URL_DOMAIN + filename
    return jsonify(errno=RET.OK, errmsg='OK', data={"image_url": image_url})


@api.route("/user/houses", methods=['GET'])
@login_required
def get_user_house():
    """
    获取用户发布的房源
    :return:发布的房源信息
    """
    # 获取当前用户
    user_id = g.user_id
    # print("id:",user_id)
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')

    # 转成字典存放在列表
    # print(houses)
    house_list = []
    if houses:
        for house in houses:
            house_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg='OK', data={'houses': house_list})


@api.route("/houses/index", methods=['GET'])
def get_house_index():
    """
    获取首页房屋信息
    :return: 排序后房屋信息
    """
    # 先查询缓存
    try:
        # print("wrwerwerwer")
        result = redis_store.get("home_page_data")
    except Exception as e:
        logging.error(e)
        result = None

    if result:
        return result.decode(), 200, {"Content-Type": "pplication/json"}
    else:
        # 查询数据库，房屋订单最多的5条
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(contants.HOME_PAGE_MAX_NUMX).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg='没有数据')

        # print(houses)
        # print(type(houses))

        houses_list = []
        for house in houses:
            houses_list.append(house.to_basic_dict())

        house_dict = dict(errno=RET.OK, errmsg="ok", data=houses_list)
        json_houses = json.dumps(house_dict)
        try:
            redis_store.setex("home_page_data", contants.HOME_PAGE_DATE_REDIS_EXPIRES, json_houses)
        except Exception as e:
            logging.error(e)

        return json_houses, 200, {"Content-Type": "pplication/json"}
        # print("---", houses_list)
        # return jsonify(errno=RET.OK, errmsg='OK', data=houses_list)


@api.route("/houses/<int:house_id>", methods=['GET'])
def get_house_detail(house_id):
    """
    获取房屋的详情
    :param house_id: 房屋id
    :return:  房屋的详细信息
    """
    # 当前用户
    # g对象
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 查询缓存
    try:
        result = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        logging.error(e)
        # return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        result = None
    if result:
        # print("result---2:", result)
        # print("result---2:", type(result))
        # print("result---2:", result)
        print("result---3:", result.decode())
        return '{"errno":%s, "errmsg":"OK", "data":{"house": %s, "user_id": %s }}' % (
        RET.OK, result.decode(), user_id), 200, {"Content-Type": "pplication/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # print(house)

    house_data = house.to_full_dict()

    # 保存redis
    json_data = json.dumps(house_data)
    print("json:--", json_data)
    try:
        redis_store.setex("house_info_%s" % house_id, contants.HOUSE_DETAIL_REDIS_EXPIRES, json_data)
    except Exception as e:
        logging.error(e)
    # print("house_data---1:", house_data)
    # print("house_data---1:", type(house_data))
    print(house)
    return jsonify(errno=RET.OK, errmsg='OK', data={"house": house_data, "user_id": user_id})


# http://127.0.0.1:5000/api/v1.0/houses?aid=6&sd=2020-12-26&ed=&sk=new&p=1
# http://127.0.0.1:5000/api/v1.0/houses?aid=5&sd=2020-12-22&ed=2020-12-26&sk=new&p=1
# aid  区域id
# sd  开始时间
# ed 结束时间
# sk 排序
#  p  页码
@api.route("/houses", methods=["GET"])
def get_house_list():
    """
    房屋的搜索页面
    ：:param:aid  区域id sd  开始时间  sd  开始时间  ed 结束时间  sk 排序  p  页码
    :return:
    """

    # 接收参数
    start_date = request.args.get("sd")
    end_date = request.args.get("ed")
    area_id = request.args.get("aid")
    sort_key = request.args.get("sk")
    page = request.args.get("p")

    # 校验参数
    # print(start_date)
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        # if start_date >= end_date:
        #     return jsonify(errno=RET.PARAMERR, errmsf='日期参数有误')
        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsf='日期参数有误')

    # print(start_date)
    # 校验区域area_id
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.PARAMERR, errmsf='区域参数有误')

    try:
        page = int(page)
    except Exception as e:
        logging.error(e)
        page = 1

    # 查询缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        logging.error(e)
    else:
        if resp_json:
            print("redis---")
            return resp_json.decode(), 200, {"Content-Type": "pplication/json"}

    # 查询数据库
    conflict_order = None

    filter_params = []

    try:
        if start_date and end_date:
            # 查询冲突的订单
            # order.begin_date <= end_date and
            # order.end_date >= start_date
            conflict_order = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()

        elif start_date:
            conflict_order = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_order = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsf='查询错误')

    # print(conflict_order)
    if conflict_order:
        # 从订单中获取冲突的房屋ID
        conflict_house_id = [order.house_id for order in conflict_order]
        if conflict_house_id:
            # house是可预定的房间，即当前没有被预定
            # house = House.query.filter(House.id.notin_(conflict_house_id))
            filter_params.append(House.id.notin_(conflict_house_id))
    if area_id:
        # 查询条件
        filter_params.append(House.area_id == area_id)

    # 排序
    if sort_key == "booking":
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())

    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-desc":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页

    # print(house_query)
    page_obj = house_query.paginate(page=page, per_page=contants.HOUSE_LIST_PAGE_NUMS,
                                    error_out=False)

    # 总页数
    total_pages = page_obj.pages
    # 获取数据
    page_li = page_obj.items
    # print(page_li)
    houses = []
    for house in page_li:
        houses.append(house.to_basic_dict())

    resp = dict(errno=RET.OK, errmsf='OK', data={"total_page": total_pages,
                                                    "houses": houses})
    resp_json = json.dumps(resp)

    # 将数据保存到redis
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        # redis管道

        pipeline = redis_store.pipeline()
        pipeline.hset(redis_key, page, resp_json)
        pipeline.expire(redis_key, contants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
        pipeline.execute()
    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsf='OK', data={"total_page": total_pages,
                                                    "houses": houses})

    # print(page_list)
    # 搜索的数据放到redis中
    # house_start_end_区域id_排序_页码
    # key value
    # house_start_end_区域id_排序  ---key
    # value
    #{
        # "1" :{1 ,2, 3}
        # "2" :{1 ,2, 3}
    # }
    # hash



