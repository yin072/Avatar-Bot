from langchain.agents import tool
from langchain_community.utilities import SerpAPIWrapper
from dotenv import load_dotenv


load_dotenv("bot/config.env")

@tool
def search(query:str):
    """只有需要了解实时信息或不知道的事情的时候才会使用这个工具。"""
    serp = SerpAPIWrapper()
    result = serp.run(query)
    print("实时搜索结果:",result)
    return result