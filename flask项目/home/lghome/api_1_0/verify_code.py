
from . import api
from lghome.utils.captcha.captcha import captcha
from lghome import redis_store
import logging
from flask import jsonify, make_response, request
from lghome import contants
from lghome.response_code import RET
from lghome.models import User
import random
from lghome.libs.ronglianyun.ccp_sms import CCP
"""
REST 风格
/add_goods
/update_goods
/delete_goods
请求的方式
get : 查询
post: 保存
put: 修改
"""

# UUID  image_code_id
# get 请求  127.0.0.1/api/v1.0/image_codes<image_code_id>
# redis 中数据类型很多
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id: 图片的编号
    :return: 验证码  图像
    """
    # 验证参数
    # 业务逻辑处理
    # 生成验证码图片
    text, image_data = captcha.generate_captcha()
    # 保存验证码 redis
    # redis_store.set()
    # redis_store.expire()
    try:
        redis_store.setex('image_code_%s' % image_code_id,
                          contants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.OK, errmsg='保存图片验证码失败')
    # 返回值
    reponse = make_response(image_data)
    reponse.headers['Content-Type'] = 'image/jpg'
    return reponse


# 默认是GET  请求
@api.route("/sms_codes/<re(r'1[358]\d{9}'):mobile>")
def get_sms_code(mobile):
    """
    获取短信验证码
    :param mobile:
    :return:
    """
    # 获取参数
    # 图片验证
    image_code = request.args.get('image_code')
    # uuid
    image_code_id = request.args.get('image_code_id')
    # 校验参数
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 从redis中取出验证码
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg = 'redis数据库异常')

    # 判断图片验证码是否过期
    if  real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码失效')

    # 删除redis中的图片验证码
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)

    # print(real_image_code)
    # 与用户填写的图片验证码对比
    print(real_image_code)
    print(image_code)
    real_image_code = real_image_code.decode()
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    # 判断手机号的操作
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
    except Exception as e:
        logging.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg='请求过于频繁')


    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
    else:
        if user is not None:
            # 手机号存在
            return jsonify(errno=RET.DATAEXIST, errmsg = '手机号存在')

    # 生成短信验证码
    sms_code ="%06d" % random.randint(0,999999)


    # 保存真实的短信验证码到redis
    try:
        # redis的管道
        pl = redis_store.pipeline()
        pl.setex("sms_code_%s" % mobile,contants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送这个手机号的记录
        pl.setex("send_sms_code_%s" % mobile,contants.SEND_SMS_CODE_EXPIRES, 1)
        pl.execute()

    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg = '保存短信验证码异常')

    # 发送短信
    # try:
    #     ccp = CCP()
    #     result = ccp.send_message(mobile,(sms_code,
    #                                   int(contants.SMS_CODE_REDIS_EXPIRES/60)), 1)
    # except Exception as e:
    #     logging.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送异常')

    # from lghome.tasks.task_sms import send_sms
    from lghome.tasks.sms.tasks import send_sms
    send_sms.delay(mobile, (sms_code,int(contants.SMS_CODE_REDIS_EXPIRES/60)), 1)

    #

    # 返回值
    # if result == 0:
    return jsonify(errno=RET.OK, errmsg='发送成功')
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送失败')


