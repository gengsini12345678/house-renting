# 提供静态资源文件的蓝图

from flask import Blueprint, current_app, make_response
from flask_wtf import csrf

html = Blueprint('web_html', __name__)

# 127.0.0.1:5000/  访问首页
# 127.0.0.1:5000/index.html  访问首页
# 路由转换

@html.route("/<re('.*'):html_file_name>")
# /<re(r'.*'):html_file_name>
def get_html(html_file_name):
    """
    提供html文件
    :param html_file_name:
    :return:
    """
    if not html_file_name:
        html_file_name = 'index.html'
    html_file_name = 'html/' + html_file_name
    # current_app.send_static_file(html_file_name)

    csrf_token = csrf.generate_csrf()
    response = make_response(current_app.send_static_file(html_file_name))
    # return current_app.send_static_file(html_file_name)
    response.set_cookie('csrf_token', csrf_token)
    return  response















