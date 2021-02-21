
from celery import Celery
from lghome.libs.ronglianyun.ccp_sms import CCP


# 创建celery对象  redis 默认16个数据库 0-15

celery_app = Celery("home", broker="redis://127.0.0.1:6379/1")


@celery_app.task
def send_sms(mobile, datas, tid):
    """
    发送短信的异步任务
    :return:
    """
    ccp = CCP()
    ccp.send_message(mobile, datas, tid)

# celery 启动
# celery -A lghome.tasks.task_sms worker -l info

