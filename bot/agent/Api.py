from fastapi import FastAPI 
from Agent import Avatar  # 导入 Avatar 类
from bot.wx_auto.wx_auto_tools import WxAutoTools# 导入 WxAutoTools 类
from typing import List, Dict 


app = FastAPI()  # 创建 FastAPI 实例

@app.get("/")  # 定义根路径的 GET 请求
def read_root():
    return {"message": "Hello, FastAPI!"}

@app.post("/chatPage/chat")
def chat(query:str):
    """聊天接口"""
    avatar = Avatar()
    msg = avatar.run(query)
    return {"msg":msg}


@app.get("/chatpage/getWxListFriendAndMessage")
def getWxListFriendAndMessage():
    """获取当前微信列表好友与聊天记录接口"""
    tool= WxAutoTools()
    msg = tool.get_list_friend_and_message()
    return {"msg":msg}

@app.post("/chatpage/forwardMessage")
def stream_message(data: List[Dict[str, str]]):  # 改用 List[Dict]
    """转发消息至微信接口接口，返回当前聊天窗口的所有消息"""
    tool = WxAutoTools()
    for item in data:
        for key, value in item.items():
            messages = tool.send_friend_message(key, value)
    return messages # 返回所有消息

'''
1. __name__ 的本质
所有 Python 模块（文件）都有一个 __name__ 属性。
它的值由 Python 解释器自动设置，取决于模块的运行方式：
直接运行时：__name__ 被设为 "__main__"。
被导入时：__name__ 被设为模块的文件名（不含 .py 后缀）
'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)