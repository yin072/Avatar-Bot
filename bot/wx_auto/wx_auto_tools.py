from wxauto import WeChat
from wxauto.msgs import *
from bot.agent.Agent import Avatar
import pythoncom
import time
import asyncio
from bot.wx_auto.message_queue import MessageQueue

class WxAutoTools:
    def __init__(self):
        pythoncom.CoInitialize()  # 初始化COM
        try:
            self.wx = WeChat()  
        finally:
            pythoncom.CoUninitialize() 
        self.agent = Avatar() # 初始化agnet
        self.global_queue=MessageQueue(merge_window=8.5) #初始化全局消息队列


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
    
    #TODO BUG:同步异步等待问题？解答：只有添加了 await 的代码才会让当前协程暂停等待，不加await的任务会被立刻丢进线程池中独立运行，与主协程并发执行
    async def begin_auto_reply(self, friend_name):
        """完全版的异步自动回复实现"""
        loop = asyncio.get_running_loop()
    
        # 启动监听任务（线程池执行同步方法）
        listen_task = loop.run_in_executor(None, self.wx.AddListenChat, friend_name, self.on_message)
        keep_task = loop.run_in_executor(None, self.wx.KeepRunning)


        try:
            while True:
                await asyncio.sleep(3)  # 异步等待
                # 检查窗口状态（线程池执行同步方法）
                if not await loop.run_in_executor(None, self.wx.GetSubWindow, friend_name):
                    listen_task.cancel()
                    keep_task.cancel()
                    await loop.run_in_executor(None, self.wx.StopListening)
                    return "子窗口被关闭"
                
        finally:
            await loop.run_in_executor(None, self.wx.StopListening)
  
        
    # 消息处理函数
    def on_message(self, msg, chat):
        """处理接收到的消息"""
        # 将消息推入全局队列，指定处理回调
        if isinstance(msg, FriendMessage):
            self.global_queue.add_message(
                user_id=msg.sender,
                message=msg.content,
                callback=lambda user_id, merged_msg: self._process_merged(user_id, merged_msg, chat)
        )

    # _开头代表私有函数
    def _process_merged(self, user_id: str, merged_message: str, chat):
        """非阻塞方式处理合并消息"""
        def _async_agent_call():
            print("处理消息:", merged_message)
            self.agent.MemoryId = user_id
            reply = self.agent.run(merged_message)  # 同步调用Agent
            chat.SendMsg(reply.get("output"))
    
        # 使用线程池执行Agent调用
        self.global_queue.executor.submit(_async_agent_call)
    
    def stop_auto_reply(self,friend_name):
        """停止自动回复"""
        # 移除监听
        chat = self.wx.GetSubWindow(nickname=friend_name)
        chat.Show()
        messages=chat.GetAllMessage()
        new_messages = [
        {msg.attr: msg.content} 
        for msg in messages 
        if msg.attr != "time"]
        self.wx.StopListening()
        return new_messages
