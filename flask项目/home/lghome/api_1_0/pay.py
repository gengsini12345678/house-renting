# @ Time    : 2020/12/10 20:43
# @ Author  : JuRan

from . import api
from lghome.utils.comments import login_required
from flask import g, request, jsonify
from lghome.response_code import RET
import logging
from lghome.models import Order
from lghome import db
from alipay import AliPay
import os

from alipay import AliPay, DCAliPay, ISVAliPay
from alipay.utils import AliPayConfig


@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
    """
    发起支付宝支付
    :param order_id: 订单ID
    :return:
    """
    user_id = g.user_id
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_PAYMENT", Order.user_id == user_id).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if order is None:
        return jsonify(errno=RET.NODATA, errmsg='订单数据有误')

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()

    alipay = AliPay(
        appid="2021000116684514",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=False,  # 默认False
    )

    # https://openapi.alipaydev.com/gateway.do
    # 电脑网站支付，需要跳转到 https://openapi.alipay.com/gateway.do? + order_string
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order.id,    # 订单编号
        total_amount=order.amount/100,      # 总金额
        subject='租房 %s' % order.id,           # 订单的标题
        return_url="http://127.0.0.1:5000/payComplete.html",       # 返回的连接地址
        notify_url=None  # 可选, 不填则使用默认notify url
    )
    pay_url = "https://openapi.alipaydev.com/gateway.do?" + order_string
    print(pay_url)
    return jsonify(errno=RET.OK, errmsg='OK', data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
@login_required
def save_order_payment_result():
    """
    保存订单结果
    :return: json
    """
    data = request.form.to_dict()
    # sign 不能参与签名验证
    signature = data.pop("sign")

    app_private_key_string = open(os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem")).read()
    alipay_public_key_string = open(os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem")).read()

    alipay = AliPay(
        appid="2021000116684514",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=app_private_key_string,
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        alipay_public_key_string=alipay_public_key_string,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=False,  # 默认False
    )

    success = alipay.verify(data, signature)
    if success:
        # print(data)
        order_id = data.get('out_trade_no')
        trade_no = data.get('trade_no')     # 支付宝的交易号

        try:
            Order.query.filter(Order.id == order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            logging.error(e)
            db.session.rollback()

    return jsonify(errno=RET.OK, errmsg='OK')


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """
    保存订单的评论信息
    :param order_id:
    :return: json
    """
    # 接收参数
    user_id = g.user_id
    request_data = request.get_json()
    comment = request_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        order = Order.query.filter(Order.id==order_id, Order.status=="WAIT_COMMENT", Order.user_id==user_id).first()
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order:
        return jsonify(errno=RET.DBERR, errmsg='操作无效')

    try:
        order.comment = comment
        order.status = "COMPLETE"

        # 将房屋订单加1
        house.order_count += 1
        db.session.add(house)
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.PARAMERR, errmsg='操作失败')
    return jsonify(errno=RET.OK, errmsg='OK')



