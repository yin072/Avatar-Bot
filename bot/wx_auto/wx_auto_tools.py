from wxauto import WeChat
from wxauto.msgs import *
import pythoncom

class WxAutoTools:
    def __init__(self):
        pythoncom.CoInitialize()  # 初始化COM
        try:
            self.wx = WeChat()  
        finally:
            pythoncom.CoUninitialize() 

    def get_sessions(self):
        sessions = self.wx.GetSession()
        for session in sessions:
            print(session.info)
        return sessions

    def get_list_friend_and_message(self):
        """获取当前会话列表好友和聊天记录"""
        sessions= self.wx.GetSession()
        friendsAndMessages = {}
        for session in sessions[:-1]:
            session.click()  # 点击会话以获取更多信息
            if(self.wx.chat_type != "friend"):
                continue
            allMessage = self.wx.GetAllMessage()
            message = []
            for msg in allMessage:
                if msg.attr not in ["self", "friend"]:
                    continue
                message.append({msg.attr: msg.content})
            friendsAndMessages[session.name] = message  
        print("好友列表:", friendsAndMessages)
        return friendsAndMessages

    def send_friend_message(self, friend_name, message):
        """发送消息给指定好友,获取当前最新消息列表"""
        messages=[]
        chat = self.wx.GetSubWindow(nickname=friend_name)
        if chat:
            chat.Show()
            chat.SendMsg(message)
            messages = chat.GetAllMessage()
        else:
            self.wx.SendMsg(message, friend_name)
            messages = self.wx.GetAllMessage()
        new_messages = [
        {msg.attr: msg.content} 
        for msg in messages 
        if msg.attr != "time"]
        return new_messages
    

    def get_all_messages(self):
        """获取当前聊天窗口的所有消息"""
        messages = self.wx.GetAllMessage()
        return messages
