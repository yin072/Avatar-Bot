from langchain.agents import tool
from langchain_community.utilities import SerpAPIWrapper
from dotenv import load_dotenv
import requests
import json
import time
import os

load_dotenv("bot/config.env")

@tool
def search(query: str):
    """只有需要了解实时信息或不知道的事情的时候才会使用这个工具。"""
    try:
        serp = SerpAPIWrapper()
        result = serp.run(query)
        print("实时搜索结果:", result)
        return result
    except Exception as e:
        print(f"搜索异常: {e}")
        return "搜索服务暂时不可用，请稍后重试"

@tool
def recognize_image(imageUrl:str):
    """只有需要解析图片内容的时候才会使用这个工具。依据解析的内容生成回答"""
    url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/image-understanding/request"
    payload = json.dumps({
        "url": imageUrl,
        "question": "“这张图片的内容是什么？”"
    }, ensure_ascii=False)
    headers = {
        "Content-Type": "application/json", 
        'Authorization': os.environ.get("BAIDU_API_KEY")  # 从环境变量中获取API密钥
    }
    response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
    result = response.json() 
    task_id = result["result"]["task_id"]
    print("提取的 task_id:", task_id)
    if task_id:
        return get_parser_content(task_id)
    else:
        return print("出现错误")    

def get_parser_content(task_id: str):
    """获取解析的内容（增加自动轮询）"""
    url = "https://aip.baidubce.com/rest/2.0/image-classify/v1/image-understanding/get-result"
    headers = {
        "Content-Type": "application/json",
        'Authorization': os.environ.get("BAIDU_API_KEY")
    }
    
    # 增加自动轮询（最多尝试10次，每次间隔1秒）
    for i in range(10):
        payload = json.dumps({"task_id": task_id}, ensure_ascii=False)
        response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
        result = response.json()
        
        print(f"第{i+1}次尝试，返回结果:", response.text)
        
        if result["result"]["ret_code"] == 0:  # 0表示成功
            return result["result"].get("description", "没有找到描述")
        
        time.sleep(1)  # 等待1秒
    
    return "获取结果超时"  # 获取结果超时

