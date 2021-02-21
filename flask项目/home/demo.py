n = int(input("数字"))
n = 0
def funs(n):
    a, b = 0, 1
    list = []
    list.append(a)
    list.append(b)
    while n > 0:
        a, b = b, a + b
        n = n - 1
        # list.append(a)
        list.append(b)
    return list
ll = funs(n)
# print(ll)
# ----------------------------
# 100以内的质数
list2 = []
for i in range(2,100):
    j = 2
    for j in range(j,i):
        if i % j == 0:
            break
    else:
        list2.append(i)
# print("素数：",list2)

dd = [2,4,1,0,5,3,2,3]

new_list=[]
odd = []

for i in dd:
    if i not in new_list:
        new_list.append(i)
    else:
        odd.append(i)
print(odd)


"""
# 从redis里读取数据
    try:
        response_json = redis_store.get("area_info")
    except Exception as e:
        logging.error(e)
    else:
        # redis 有缓存数据
        if response_json is not None:
            # print(response_json)
            # print(type(response_json))
            # response_json = json.loads(response_json)
            return jsonify(errno=RET.OK, errmsg='OK', data=response_json)

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
    return jsonify(errno=RET.OK, errmsg='ok', data=area_dict_li)
"""


