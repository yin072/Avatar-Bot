from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bot.agent.Agent import Avatar  # 导入 Avatar 类
from bot.wx_auto.wx_auto_tools import WxAutoTools# 导入 WxAutoTools 类
from typing import List, Dict 
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
from pathlib import Path 

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

# 添加静态文件服务
try:
    # 挂载静态文件目录
    static_dir = Path(__file__).parent.parent / "static" / "dist"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        print(f"✅ 静态文件目录已挂载: {static_dir}")
    else:
        print(f"⚠️ 静态文件目录不存在: {static_dir}")
except Exception as e:
    print(f"⚠️ 挂载静态文件失败: {e}")

# 添加根路径处理，返回前端页面
@app.get("/")
async def serve_frontend():
    """服务前端主页"""
    static_dir = Path(__file__).parent.parent / "static" / "dist"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {"message": "前端页面未找到，请确保已构建Vue项目并复制到static/dist目录"}

# 注意：这里先定义所有API路由，然后再定义通配符路由
# 通配符路由会移到最后，避免拦截API请求

@app.post("/chatPage/chat")
def chat(query: str,contact=str):
    """聊天接口"""
    try:
        avatar = Avatar(MemoryId=contact)
        msg = avatar.run(query)
        print(msg)
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

def open_frontend():
    """打开前端界面（不启动服务器）"""
    import webbrowser
    import socket
    
    print("🌐 打开Avatar Bot前端界面...")
    
    # 检查服务器是否在运行
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("✅ 服务器正在运行")
            try:
                webbrowser.open('http://localhost:8000')
                print("✅ 已打开浏览器")
                print("🌐 前端地址: http://localhost:8000")
                print("🔌 API文档: http://localhost:8000/docs")
            except Exception as e:
                print(f"❌ 无法打开浏览器: {e}")
                print("请手动访问: http://localhost:8000")
        else:
            print("⚠️ 服务器未运行")
            print("请先运行 'avatar serve' 启动服务器")
    except Exception as e:
        print(f"⚠️ 无法检查服务器状态: {e}")

def start_server():
    """启动完整服务器（API + 前端）"""
    import uvicorn
    import webbrowser
    import threading
    import time
    import subprocess
    import sys
    import os
    import signal
    
    print("🚀 Avatar Bot 服务器启动中...")
    print("=" * 40)
    print("🌐 前端页面: http://localhost:8000")
    print("🔌 API接口: http://localhost:8000/docs")
    print("📁 静态文件: http://localhost:8000/static/")
    print("📱 wxdump UI 界面将自动启动")
    print("💡 如果关闭浏览器，可以运行 'avatar ui' 重新打开")
    print("💡 服务器将在后台运行，终端可以继续使用")
    print("=" * 40)
    
    # 使用subprocess在后台启动服务器
    try:
        # 构建启动命令
        cmd = [sys.executable, "-c", f"""
import uvicorn
from bot.agent.Api import app
uvicorn.run(app, host="0.0.0.0", port=8000, ws="websockets")
"""]
        
        # 在后台启动服务器进程
        server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        print(f"✅ 服务器进程已启动 (PID: {server_process.pid})")
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查服务器是否成功启动
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("✅ 服务器已成功启动！")
            
            # 直接在主进程中打开浏览器，确保能执行
            try:
                print("🌐 正在打开浏览器...")
                webbrowser.open('http://localhost:8000')
                print("✅ 已自动打开浏览器")
            except Exception as e:
                print(f"⚠️ 无法自动打开浏览器: {e}")
                print("请手动访问: http://localhost:8000")
            
            # 自动运行 wxdump ui 命令
            try:
                print("📱 正在启动 wxdump UI 界面...")
                wxdump_process = subprocess.Popen(
                    ['wxdump', 'ui'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd()
                )
                print(f"✅ wxdump UI 已启动 (PID: {wxdump_process.pid})")
                
                # 保存wxdump进程ID到文件
                with open("wxdump.pid", "w") as f:
                    f.write(str(wxdump_process.pid))
                    
            except Exception as e:
                print(f"⚠️ 无法启动 wxdump UI: {e}")
                print("请手动运行 'wxdump ui' 命令")
            
            print("🌐 前端地址: http://localhost:8000")
            print("🔌 API地址: http://localhost:8000/docs")
            print("📱 wxdump UI 界面已启动")
            print("💡 现在可以继续使用终端，运行其他命令")
            print("💡 要停止服务器，请运行 'avatar stop' 或重启终端")
            print("=" * 40)
            
            # 保存服务器进程ID到文件，方便后续停止
            with open("server.pid", "w") as f:
                f.write(str(server_process.pid))
            
        else:
            print("❌ 服务器启动失败")
            server_process.terminate()
            return
            
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return

def stop_server():
    """停止服务器"""
    import socket
    import os
    import signal
    
    print("🛑 正在停止Avatar Bot服务器...")
    
    try:
        # 尝试连接服务器
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            # 服务器正在运行，尝试停止
            if os.path.exists("server.pid"):
                try:
                    with open("server.pid", "r") as f:
                        pid = int(f.read().strip())
                    
                    # 尝试终止进程
                    os.kill(pid, signal.SIGTERM)
                    print(f"✅ 已发送停止信号到服务器进程 (PID: {pid})")
                    
                    # 等待进程结束
                    import time
                    time.sleep(2)
                    
                    # 检查是否真的停止了
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', 8000))
                    sock.close()
                    
                    if result != 0:
                        print("✅ 服务器已成功停止")
                        os.remove("server.pid")
                    else:
                        print("⚠️ 服务器仍在运行，可能需要手动停止")
                        
                except Exception as e:
                    print(f"⚠️ 无法停止服务器进程: {e}")
                    print("💡 请手动关闭终端或重启系统")
            else:
                print("⚠️ 找不到服务器进程ID文件")
                print("💡 请手动关闭终端或重启系统")
        
        # 尝试停止 wxdump UI 进程
        if os.path.exists("wxdump.pid"):
            try:
                with open("wxdump.pid", "r") as f:
                    wxdump_pid = int(f.read().strip())
                
                # 尝试终止 wxdump 进程
                os.kill(wxdump_pid, signal.SIGTERM)
                print(f"✅ 已发送停止信号到 wxdump UI 进程 (PID: {wxdump_pid})")
                
                # 等待进程结束
                import time
                time.sleep(1)
                
                # 检查是否真的停止了
                try:
                    os.kill(wxdump_pid, 0)  # 检查进程是否存在
                    print("⚠️ wxdump UI 进程仍在运行，可能需要手动停止")
                except OSError:
                    print("✅ wxdump UI 进程已成功停止")
                    os.remove("wxdump.pid")
                    
            except Exception as e:
                print(f"⚠️ 无法停止 wxdump UI 进程: {e}")
                print("💡 请手动关闭 wxdump UI 窗口")
        else:
            print("✅ wxdump UI 进程未运行")
            
    except Exception as e:
        print(f"⚠️ 无法检查服务器状态: {e}")
        print("💡 请手动关闭终端或重启系统")

def cli_main():
    """CLI主入口函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("🎯 Avatar Bot 命令行工具")
        print("=" * 30)
        print("使用方法:")
        print("  avatar serve    # 启动服务器")
        print("  avatar ui       # 打开前端界面")
        print("  avatar stop     # 停止服务器")
        print("  avatar help     # 显示帮助信息")
        return
    
    command = sys.argv[1].lower()
    
    if command == "serve":
        start_server()
    elif command == "ui":
        open_frontend()
    elif command == "stop":
        stop_server()
    elif command in ["help", "-h", "--help"]:
        print("🎯 Avatar Bot 命令行工具")
        print("=" * 30)
        print("命令:")
        print("  serve   启动完整服务器（API + 前端）")
        print("  ui      打开前端界面（需要服务器已运行）")
        print("  stop    停止服务器")
        print("  help    显示此帮助信息")
        print("\n示例:")
        print("  avatar serve    # 启动服务器")
        print("  avatar ui       # 重新打开前端")
        print("  avatar stop     # 停止服务器")
    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'avatar help' 查看可用命令")

# 最后定义通配符路由，支持前端路由
# 这个路由必须在所有API路由之后定义，避免拦截API请求
@app.get("/{full_path:path}")
async def serve_frontend_routes(full_path: str):
    """处理前端路由，返回index.html"""
    # 跳过API路由，避免冲突
    if full_path.startswith(("chatpage/", "wechat_rag/", "mine/", "knowledge/", "ws/")):
        return {"message": "API路由不存在"}
    
    static_dir = Path(__file__).parent.parent / "static" / "dist"
    
    # 检查请求的文件是否存在
    file_path = static_dir / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    
    # 文件不存在，返回index.html（支持前端路由）
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        return {"message": "前端页面未找到"}
if __name__ == "__main__":
    # 直接运行main函数，保持向后兼容
    main()

def main():
    """保持原有的main函数，用于直接运行Api.py"""
    start_server()