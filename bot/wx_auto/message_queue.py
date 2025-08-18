from collections import defaultdict
from typing import Callable
from threading import Timer
from concurrent.futures import ThreadPoolExecutor

class MessageQueue:
    """同步消息队列（适用于非异步环境）"""
    def __init__(self, merge_window: float):
        self.merge_window = merge_window
        self.user_queues = defaultdict(list)  # {user_id: [messages]}
        self.timers = {}  # {user_id: threading.Timer}
        self.executor = ThreadPoolExecutor(max_workers=5)  # 增加线程池

    def add_message(self, user_id: str, message: str, callback: Callable[[str, str], None]):
        """添加消息到队列，合并后通过 callback 处理"""
        # 获取当前用户的消息数量（即新消息的序号）
        msg_count = len(self.user_queues[user_id]) + 1
        # 添加带序号的消息
        self.user_queues[user_id].append(f"第{msg_count}条消息： {message}")
    
        if user_id not in self.timers:
            self.timers[user_id] = Timer(
                self.merge_window,
                lambda: self.executor.submit(  # 使用线程池执行处理
                    self._process_user_messages, 
                    user_id, 
                    callback
                )
            )
            self.timers[user_id].start()

    def _process_user_messages(self, user_id: str, callback: Callable[[str, str], None]):
        """处理合并后的消息"""
        if user_id in self.user_queues:
            messages = self.user_queues.pop(user_id)
            merged_message = user_id+":"+" | ".join(messages)
            callback(user_id, merged_message)  # 同步回调
        self.timers.pop(user_id, None)  # 清理计时器
