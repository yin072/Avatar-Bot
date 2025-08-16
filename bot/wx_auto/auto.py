from wxauto import WeChat
from wxauto.msgs import *
from wx_auto_tools import WxAutoTools

wx= WxAutoTools()
messages=wx.send_friend_message("Ace", "你好")  # 示例发送消息
for msg in messages:
    print(msg.attr)  # 打印消息属性和内容




