

from . import api
from flask import request, jsonify, session
from lghome.response_code import RET
from lghome import redis_store
from lghome.models import User
import re
import logging
from lghome import db
from sqlalchemy.exc import IntegrityError
from lghome import contants


@api.route("/users", methods=["POST"])
def register():
    """
    注册
    :param: 手机号， 短信验证码  密码确认密码
    :return: json
    """
    # 接收参数
    request_dict = request.get_json()
    mobile = request_dict.get("mobile")
    sms_code = request_dict.get("sms_code")
    password = request_dict.get("password")
    password2 = request_dict.get("password2")

    # 验证
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 判断手机格式
    if not re.match(r'1[358]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

    # 业务逻辑处理
    # 从redis里取短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="读取短信验证码异常")
    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg="读取短信验证码失效")

    # 删除redis中的短信验证码
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        logging.error(e)

    # 判断用户填写的验证码的正确性
    real_sms_code = real_sms_code.decode()
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg="读取短信验证码错误")
    # 手机号是否被注册过
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     logging.error(e)
    # else:
    #     if user is not None:
    #         # 手机号存在
    #         return jsonify(errno=RET.DATAEXIST, errmsg = '手机号存在')
    # 保存数据

    user = User(name=mobile, mobile=mobile)

    user.password = password

    # user.pwd_hash(password)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg = '手机号已经存在')
    except Exception as e:
        # 回滚
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='插入数据库异常')

    # user.password_hash()
    # 加密密码
    # md5 加密

    # 保存登录状态到session中
    session['name'] = mobile
    session['mobile'] = mobile
    session['user_id'] = user.id
    # 返回结果
    return jsonify(errno=RET.OK, errmsg = '注册成功')
    # print(request_dict)


@api.route("/sessions", methods=["POST"])
def login():
    """
    登录
    :param:mobile 和密码
    :return: json
    """
    # 获取参数
    request_dict = request.get_json()
    mobile = request_dict.get("mobile")
    password = request_dict.get("password")
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg = '参数不完整')
    # 判断手机格式
    if not re.match(r'1[358]\d{9}',mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机号格式错误")

    # 业务逻辑处理
    # 判断错误次数是否超过限制，如果超过限制直接返回
    # redis 用户的ip地址：次数
    user_ip = request.remote_addr
    try:
        access_nums = redis_store.get("user_ip_%s" % user_ip)
    except Exception as e:
        logging.error(e)
    else:
        if access_nums is not None and int(access_nums) >= contants.LOGIN_ERROR_MAX_TIME:
            return jsonify(errno=RET.REQERR, errmsg="错误次数太多，请稍后重试")

    # 从数据库中查询手机是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        # 查询数据库错误
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")
    # 验证密码
    if user is None or not user.check_pwd_hash(password):
        try:
            redis_store.incr("user_ip_%s" % user_ip)
            redis_store.expire("user_ip_%s" % user_ip, contants.LOGIN_ERROR_FORBID_TIMES)
        except Exception as e:
            logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="账号密码不匹配")

    # 保存登录状态
    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    # 返回
    return jsonify(errno=RET.OK, errmsg='登录成功')


@api.route("/session", methods=["GET"])
def check_login():
    """
    检查登录状态
    :return: 用户的信息或者返回错误信息
    """
    name = session.get('name')
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={'name':name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')


@api.route("/session", methods=["DELETE"])
def logout():
    """
    退出登录
    :return:
    """
    # 清空session
    session.clear()
    return jsonify(errno=RET.OK, errmsg='ok')




