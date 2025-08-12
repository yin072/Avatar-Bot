class Agent:
    def __init__(self):
        """初始化智能体基础能力"""
        self.memory = []  # 简易记忆存储
        self.tools = {}   # 可用工具字典

    def add_tool(self, name: str, tool_func: callable):
        """注册工具到智能体"""
        self.tools[name] = tool_func

    def rag_query(self, query: str) -> str:
        """简化的检索增强生成逻辑"""
        # 这里是RAG核心实现占位
        retrieved_data = self._retrieve(query)  # 检索
        response = self._generate(query, retrieved_data)  # 生成
        return response

    def _retrieve(self, query: str) -> list:
        """检索模块（可替换为真实向量数据库）"""
        return ["相关文档1", "相关文档2"]  # 模拟检索结果

    def _generate(self, query: str, context: list) -> str:
        """生成模块（可替换为真实LLM调用）"""
        return f"基于查询『{query}』和上下文{context}生成的回答"

    def run(self, input_data: dict) -> dict:
        """智能体主运行逻辑"""
        if 'query' in input_data:
            return {"response": self.rag_query(input_data['query'])}
        elif 'command' in input_data:
            return self._handle_command(input_data['command'])
        else:
            raise ValueError("无效输入类型")

    def _handle_command(self, command: str):
        """处理特殊指令"""
        return {"status": f"已执行指令: {command}"}