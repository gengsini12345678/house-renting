from ronglian_sms_sdk import SmsSDK
import json

accId = '8a216da85741a1b901574fb0b1210982'
accToken = '15fb1a43ed5c4ddb83531b7e544448c5'
appId = '8a216da85741a1b901574fb0b17d0987'


class CCP(object):
    """ 发送短信的单例类 """
    # _instance = None
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance.sdk = SmsSDK(accId, accToken, appId)
        return cls._instance
# c = CCP()
# print(id(c))
# d = CCP()
# print(id(d))
# 2670685622848
# 2670685622848
# 两个id 相同，说明只实例化一次

    def send_message(self, mobile, datas, tid=1):
        # sdk = SmsSDK(accId, accToken, appId)
        sdk = self._instance.sdk
        # tid = '1'
        # mobile = '18646175116'
        # datas  验证码   过期时间 单位是分钟
        # datas = ('1234', '5')
        resp = sdk.sendMessage(tid, mobile, datas)
        result = json.loads(resp)
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1
        # print(type(resp))
        # print(resp)


if __name__ == '__main__':

    # send_message()
    c = CCP()
    c.send_message('15109295586', ('1234', '5'), 1)