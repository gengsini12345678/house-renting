
from celery import Celery

celery_app = Celery("home")


# 加载配置文件
celery_app.config_from_object("lghome.tasks.config")

# 注册任务
celery_app.autodiscover_tasks(["lghome.tasks.sms"])





