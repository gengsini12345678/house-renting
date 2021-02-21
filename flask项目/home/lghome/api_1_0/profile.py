
from . import api
from lghome.utils.comments import login_required
from flask import g, request, jsonify, session
from lghome.response_code import RET
from lghome.libs.image_store import storage
from sqlalchemy.exc import IntegrityError
import logging
from lghome.models import User
from lghome import db
from lghome import contants


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """
    设置用户头像
    :return: avatar_url 头像地址
    """
    # 接收参数
    user_id = g.user_id

    image_file = request.files.get('avatar')
    # print(image_file)
    # print(type(image_file))
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图片')
    # 图片的二进制数据
    image_data = image_file.read()

    # 上传到七牛云
    try:
        file_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图片失败')

    # 保存到数据库中
    try:
        User.query.filter_by(id=user_id).update({"avatar_url":file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片信息失败')

    avatar_url = contants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg='保存成功',data={"avatar_url":avatar_url})

"""
用户头像图片保存的位置:
1. 服务器
2. 第三方平台  七牛云
"""


@api.route("/users/name", methods=['PUT'])
@login_required
def change_user_name():
    """
    修改用户名
    :return: 修改用户名成功与失败
    """
    user_id = g.user_id
    # 获取用户提交的用户名
    request_data = request.get_json()
    if not request_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    name = request_data.get("name")

    user = User.query.filter_by(name=name).first()
    if user:
        return jsonify(errno=RET.DBERR, errmsg='用户名已经存在')

    print("用户名：", name)
    print("用户id：", user_id)
    # 修改用户名
    try:
        User.query.filter_by(id=user_id).update({"name":name})
        db.session.commit()
    # except IntegrityError as e:
    #     db.session.rollback()
    #     logging.error(e)
    #     return jsonify(errno=RET.DATAEXIST, errmsg = '用户名已经存在')
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='设置用户名错误')

    # 更新session数据
    session['name'] = name
    return jsonify(errno=RET.OK, errmsg='OK')


@api.route("/user", methods=['GET'])
@login_required
def get_user_profile():
    """
    获取个人信息
    :return: 用户名  用户头像
    """
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')
    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='获取用户信息失败')
    return jsonify(errno=RET.OK, errmsg='OK', data=user.to_dict())


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """
    获取用户的实名认证信息
    :return:
    """
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')
    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='获取用户信息失败')
    return jsonify(errno=RET.OK, errmsg='OK', data=user.auth_to_dict())


@api.route("/users/auth", methods=['POST'])
@login_required
def set_user_auth():
    """
    保存实名认证
    :return:
    """
    user_id = g.user_id
    # 第一次修改
    # User.query.filter_by(id=g.user_id, real_name=None, id_card=None).update({"real_name":real_name, "id_card":id_card})
