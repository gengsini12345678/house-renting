# 定义蓝图
from flask import Blueprint

api = Blueprint('api_1_0', __name__, url_prefix='/api/v1.0')
from . import verify_code
from . import demo, passport, profile, houses, orders, pay


