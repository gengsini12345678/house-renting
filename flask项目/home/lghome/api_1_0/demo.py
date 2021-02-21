
from lghome import db, models
# from lghome import redis_store

from . import api
import logging


@api.route("/index")
def index():
    logging.warning("连接数据库失败")
    return "index page"