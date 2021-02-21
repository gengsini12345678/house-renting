# Date: 2020/11/21
# Author : zzs

import redis


class Config(object):
    """
    配置信息
    """
    # 123 md5 加密
    SECRET_KEY = 'WEWERER12312%%3'
    USERNAME = 'root'
    PASSWORD = '123456'
    HOST = '127.0.0.1'
    PORT = 3306
    DATABASE = 'home'

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask_session
    SESSION_TYPE = 'redis'
    # 不同的服务器
    SESSION_REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24
    # 数据库 mysql+pymysql://{}:{}@{}:{}/{}
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD,
                                                                      HOST, PORT, DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(Config):
    """
    开发环境
    """
    DEBUG = True


class ProConfig(Config):
    """
    生产环境
    """


config_map = {
    "dev": DevConfig,
    "pro": ProConfig

}
