from wxauto import WeChat
from wxauto.msgs import *

class WxAutoTools:
    def __init__(self):
        self.wx = WeChat()

    def get_sessions(self):
        sessions = self.wx.GetSession()
        for session in sessions:
            print(session.info)
        return sessions

    def get_list_friend(self):
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

    def get_all_messages(self):
        """获取当前聊天窗口的所有消息"""
        messages = self.wx.GetAllMessage()
        return messages
    
WxAutoTools = WxAutoTools()
list=WxAutoTools.get_list_friend()