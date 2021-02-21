from ronglian_sms_sdk import SmsSDK

accId = '8a216da85741a1b901574fb0b1210982'
accToken = '15fb1a43ed5c4ddb83531b7e544448c5'
appId = '8a216da85741a1b901574fb0b17d0987'


def send_message():
    sdk = SmsSDK(accId, accToken, appId)
    tid = '1'
    mobile = '18646175116'
    # datas  验证码   过期时间 单位是分钟
    datas = ('1234', '5')
    resp = sdk.sendMessage(tid, mobile, datas)
    print(type(resp))
    print(resp)


send_message()