from fastapi import FastAPI, WebSocket
from Agent import Avatar  # 导入 Avatar 类
from bot.wx_auto.wx_auto_tools import WxAutoTools# 导入 WxAutoTools 类
from typing import List, Dict 
import asyncio
# 导入通用返回类型
from bot.agent.response import Response


app = FastAPI()  # 创建 FastAPI 实例


@app.post("/chatPage/chat")
def chat(query: str):
    """聊天接口"""
    try:
        avatar = Avatar()
        msg = avatar.run(query)
        return Response.success(data=msg)
    except Exception as e:
        return Response.error(message=f"聊天处理失败: {str(e)}")


@app.get("/chatpage/getWxListFriendAndMessage")
def getWxListFriendAndMessage():
    """获取当前微信列表好友与聊天记录接口"""
    try:
        wx = WxAutoTools()
        msg = wx.get_list_friend_and_message()
        return Response.success(data=msg)
    except Exception as e:
        return Response.error(message=f"获取微信好友列表失败: {str(e)}")

@app.post("/chatpage/forwardMessage")
def stream_message(data: List[Dict[str, str]]):
    """转发消息至微信接口，返回当前聊天窗口的所有消息"""
    try:
        tool = WxAutoTools()
        for item in data:
            for key, value in item.items():
                messages = tool.send_friend_message(key, value)
        return Response.success(data=messages)
    except Exception as e:
        return Response.error(message=f"转发消息失败: {str(e)}")


@app.websocket("/ws/auto_reply")
async def websocket_endpoint(websocket: WebSocket):
    """单一联系人自动回复接口"""
    await websocket.accept()
    try:
        # 1. 接收参数
        data = await websocket.receive_json()
        friend_name = data["friend_name"]
        wx = WxAutoTools()
        
        # 2. 启动自动回复并获取返回值
        return_msg = await wx.begin_auto_reply(friend_name)
        await websocket.send_json(Response.success().model_dump())
        
        # 3. 监听前端停止指令
        while True:
            try:
                # 设置1秒超时，避免永久阻塞
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                if msg.get("status") == "stopped":
                    stop_result = wx.stop_auto_reply(friend_name)
                    await websocket.send_json(Response.success(status="stopped").model_dump())
                    break
                    
            except asyncio.TimeoutError:
                # 检查自动回复任务是否意外结束
                if return_msg == "子窗口被关闭":
                    await websocket.send_json(Response.error(
                        message="子窗口被关闭"
                    ).model_dump())
                    break
                continue
                
    except KeyError:
        await websocket.send_json(Response.error(
            message="需要 friend_name 参数", 
            code=400
        ).model_dump())
    except Exception as e:
        await websocket.send_json(Response.error(
            message=f"自动回复处理失败: {str(e)}"
        ).model_dump())
    finally:
        await websocket.close()


@app.post("/mine/setting")
def setting(setting: Dict[str, str]):
    """配置基本参数接口
    
    在bot目录下创建或修改config.env文件
    """
    try:
        import os
        from pathlib import Path
        
        # 获取bot目录的绝对路径
        bot_dir = Path(__file__).parent.parent  # 从当前文件向上两级到bot目录
        config_file = bot_dir / "config.env"
        
        # 读取现有的配置文件（如果存在）
        existing_config = {}
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_config[key.strip()] = value.strip()
        
        # 更新配置
        existing_config.update(setting)
        
        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            for key, value in existing_config.items():
                f.write(f"{key}={value}\n")
        
        return Response.success(
            data=f"配置文件已更新，共 {len(existing_config)} 个配置项",
            status="setting_updated"
        )
        
    except Exception as e:
        return Response.error(
            message=f"设置配置失败: {str(e)}",
            status="setting_failed"
        )


'''
1. __name__ 的本质
所有 Python 模块（文件）都有一个 __name__ 属性。
它的值由 Python 解释器自动设置，取决于模块的运行方式：
直接运行时：__name__ 被设为 "__main__"。
被导入时：__name__ 被设为模块的文件名（不含 .py 后缀）
'''
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000,ws="websockets")