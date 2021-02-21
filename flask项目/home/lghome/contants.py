# 图片验证码的redis有效期，单位：秒

IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的reidis有效期，单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 短信验证码的过期时间 单位：秒
SEND_SMS_CODE_EXPIRES = 60

# 登录次数的最大值
LOGIN_ERROR_MAX_TIME = 5

# 登录次数验证时间间隔
LOGIN_ERROR_FORBID_TIMES = 600

# 七牛云域名
QINIU_URL_DOMAIN = 'http://qkgi1wsiz.hd-bkt.clouddn.com/'

# 地区有效期过期时间
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 展示房屋的最大数
HOME_PAGE_MAX_NUMX = 5

# 首页房屋轮播图过期时间
HOME_PAGE_DATE_REDIS_EXPIRES = 7200

# 详情房屋的过期时间
HOUSE_DETAIL_REDIS_EXPIRES = 7200

# 每页显示的数据量
HOUSE_LIST_PAGE_NUMS = 2

# 搜索页面缓存时间
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

# 详情页面评论数量
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 2
