from wxauto import WeChat
from wxauto.msgs import *

wx = WeChat()

sessions = wx.GetSession()
for session in sessions:
    print(session.info)
    
session = sessions[2] 

session.click()

info = wx.ChatInfo()
print(info)

messages = wx.GetAllMessage()

from wxauto.msgs import FriendMessage
import time

# 消息处理函数
def on_message(msg, chat):
    # 示例1：将消息记录到本地文件
    content=msg.content
    if(content=="以下为新消息"):
        return
    else:
        print(content)
    
    

# 添加监听，监听到的消息用on_message函数进行处理
wx.AddListenChat(nickname="Ace", callback=on_message)



# 保持程序运行
wx.KeepRunning()