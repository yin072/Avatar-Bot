"""
通用返回类型定义模块

定义所有API接口共用的统一返回格式
"""

from typing import Any, Dict
from pydantic import BaseModel


class Response(BaseModel):
    """通用返回类型 - 所有接口共用"""
    
    code: int = 200                    # 状态码：200成功，其他失败
    status: str = "success"            # 状态：可以自定义
    data: Dict[str, Any] = {"message": None}  # 固定字典格式，键为message
    
    @classmethod
    def success(cls, data: Any = None, status: str = "success") -> "Response":
        """创建成功响应"""
        return cls(code=200, status=status, data={"message": data})
    
    @classmethod
    def error(cls, message: str = "error", code: int = 500, status: str = "error") -> "Response":
        """创建错误响应"""
        return cls(code=code, status=status, data={"message": message})
