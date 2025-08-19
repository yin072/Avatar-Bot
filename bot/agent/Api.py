from fastapi import FastAPI, WebSocket
from Agent import Avatar  # 导入 Avatar 类
from bot.wx_auto.wx_auto_tools import WxAutoTools# 导入 WxAutoTools 类
from typing import List, Dict 
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect 

# 导入通用返回类型
from bot.agent.response import Response


app = FastAPI()  # 创建 FastAPI 实例

# 允许所有来源（生产环境应改为具体域名）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 或 ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法（GET/POST/PUT等）
    allow_headers=["*"],  # 允许所有请求头
)

@app.post("/chatPage/chat")
def chat(query: str,contact=str):
    """聊天接口"""
    try:
        avatar = Avatar(MemoryId=contact)
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
        
        # 2. 并行执行两个任务
        auto_reply_task = asyncio.create_task(wx.begin_auto_reply(friend_name))
        await websocket.send_json(Response.success().model_dump())
        
        # 3. 消息监听循环
        while True:
            try:
                # 设置超时，避免永久阻塞
                msg = await asyncio.wait_for(websocket.receive_json(), timeout=0.5)
                
                if msg.get("status") == "stopped":
                    stop_result = wx.stop_auto_reply(friend_name)
                    await websocket.send_json(Response.success(status="stopped").model_dump())
                    auto_reply_task.cancel()  # 取消自动回复任务
                    break
                    
            except asyncio.TimeoutError:
                # 检查自动回复是否意外结束
                if auto_reply_task.done():
                    result = await auto_reply_task
                    if result == "子窗口被关闭":
                        await websocket.send_json(Response.error(
                            message="子窗口被关闭"
                        ).model_dump())
                        break
                continue
                
    except WebSocketDisconnect:
        # 连接已断开，无需处理
        auto_reply_task.cancel() 
        print("WebSocket连接已断开")
        return
        
    except Exception as e:
        try:
            await websocket.send_json(Response.error(message=str(e)).model_dump())
        except (WebSocketDisconnect, RuntimeError):
            # 连接已断开，忽略发送错误
            pass
    finally:
        try:
            await websocket.close()
        except (WebSocketDisconnect, RuntimeError):
            # 连接已断开，忽略关闭错误
            pass

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


@app.get("/wechat_rag/count_txt")
def handle_and_count():
    """执行完整的微信数据处理流程：先清理Qdrant数据，然后CSV转TXT + 存入Qdrant，返回生成的txt文件个数"""
    try:
        import sys
        from pathlib import Path
        
        # 添加wechat_rag目录到Python路径
        wechat_rag_dir = Path(__file__).parent.parent / "wechat_rag"
        sys.path.append(str(wechat_rag_dir))
        
        from Main import process_wechat_data
        
        # 执行完整的处理流程（会自动先清理Qdrant数据）
        txt_count = process_wechat_data()
        
        return Response.success(
            data=f"微信数据处理完成，共处理 {txt_count} 个聊天数据文件",
            status="processing_completed"
        )
        
    except Exception as e:
        return Response.error(
            message=f"微信数据处理失败: {str(e)}",
            status="processing_failed"
        )


@app.post("/wechat_rag/clear_files")
def clear_all_files():
    """清空wxdump_work/export目录下的所有csv和txt文件，同时清理local_qdrant数据"""
    try:
        import sys
        from pathlib import Path
        
        # 添加wechat_rag目录到Python路径
        wechat_rag_dir = Path(__file__).parent.parent / "wechat_rag"
        sys.path.append(str(wechat_rag_dir))
        
        from Main import clear_all_files
        
        # 获取wxdump_work/export目录路径
        export_folder = Path(__file__).parent.parent.parent / "wxdump_work" / "export"
        
        if not export_folder.exists():
            return Response.success(data="导出目录不存在", status="no_export_folder")
        
        cleared_count, cleared_files, qdrant_cleared = clear_all_files(str(export_folder))
        
        result_message = f"成功清空 {cleared_count} 个文件"
        if qdrant_cleared:
            result_message += "，Qdrant数据也已清理"
        else:
            result_message += "，但Qdrant数据清理失败"
        
        return Response.success(
            data={
                "cleared_count": cleared_count,
                "cleared_files": cleared_files,
                "qdrant_cleared": qdrant_cleared,
                "message": result_message
            },
            status="files_cleared"
        )
        
    except Exception as e:
        return Response.error(
            message=f"清空文件失败: {str(e)}",
            status="clear_files_failed"
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