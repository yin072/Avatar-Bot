# Avatar Bot - 智能分身机器人项目

## 🎯 项目简介

Avatar Bot 是一个基于AI的智能微信机器人项目，它能够：

- 🤖 **智能对话**：基于你的微信聊天记录，训练出完全模仿你说话风格的AI分身
- 💬 **自动回复**：支持微信好友的自动回复功能
- 🌐 **Web管理界面**：提供Vue.js前端界面，方便管理和监控
- 🔍 **RAG检索**：使用向量数据库存储和检索聊天记录
- 📱 **微信集成**：与微信PC版深度集成，支持消息监听和自动回复

## 🏗️ 项目架构

```
Avatar Bot/
├── bot/                          # 核心后端代码
│   ├── agent/                    # AI代理模块
│   │   ├── Agent.py             # 主要的AI代理类
│   │   ├── Api.py               # FastAPI服务器和CLI工具
│   │   ├── Memory.py            # 记忆管理
│   │   └── Mytools.py           # 工具函数
│   ├── wechat_rag/              # 微信数据处理模块
│   │   ├── Main.py              # 主要处理逻辑
│   │   ├── Config.py            # 配置管理
│   │   └── data_loader/         # 数据加载器
│   ├── wx_auto/                 # 微信自动化模块
│   │   ├── wx_auto_tools.py     # 微信工具类
│   │   └── message_queue.py     # 消息队列
│   ├── static/                  # 前端静态文件
│   │   └── dist/                # Vue构建后的文件
│   └── local_qdrand/            # 本地向量数据库
├── wxdump_work/                 # 微信数据导出目录
├── requirements.txt              # Python依赖
├── setup.py                     # 包配置
└── config.env                   # 环境配置
```

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.8+
- **操作系统**: Windows 10/11
- **微信**: 3.9.8+（不支持4.0）

### 2. 安装依赖

```bash
# 克隆项目
git clone <your-repo-url>
cd Avatar Bot

# 创建虚拟环境
python -m venv myenv
myenv\Scripts\activate  # Windows

# 安装Python依赖
pip install -r requirements.txt

# 安装项目包
pip install -e .
```

### 3. 配置基本参数

1.在PyWxDump界面解密微信，提取聊天记录
2.在聊天查看界面导出备份，选择csv导出
3.在Avatar agent界面-我的-知识库设置-执行微信数据处理
4.填写相关系统设置

```

### 4. 启动服务

#### 使用CLI命令（推荐）

```bash
# 启动完整服务器（API + 前端）
avatar serve

# 打开Avatar agent界面
avatar ui

# 打开PyWxDump界面
wxdump ui

# 停止服务器
avatar stop

# 查看帮助
avatar help
```


## 🔧 核心功能

### 1. AI代理系统

- **个性化训练**：基于你的微信聊天记录训练AI分身
- **风格模仿**：完全复刻你的说话风格、性格特质和价值观
- **智能回复**：根据上下文和历史记录生成合适的回复

### 2. 微信自动化

- **消息监听**：实时监听微信消息
- **自动回复**：支持好友消息的智能自动回复
- **会话管理**：获取好友列表和聊天记录

### 3. RAG检索系统

- **向量存储**：使用Qdrant向量数据库存储聊天记录
- **语义搜索**：基于相似度检索相关聊天内容
- **数据清洗**：自动清理敏感信息，保护隐私


## 🎨 前端界面

项目包含一个完整的Vue.js前端界面，提供：

- **仪表板**：显示系统状态和统计信息
- **聊天管理**：管理AI对话和微信消息
- **数据导入**：导入和处理微信聊天记录
- **设置面板**：配置AI模型和系统参数


### 日志查看

```bash
# 查看服务器日志
avatar logs

# 检查服务器状态
avatar status
```

## 📞 联系方式

- **项目维护者**: [yin072]
- **项目地址**: (https://github.com/yin072/Avatar-Bot.git)

## 🙏 致谢

感谢以下开源项目的支持：

- [PyWxDump](https://github.com/xaoyaoo/PyWxDump.git)
- [wxauto](https://github.com/cluic/wxauto.git)

---

**注意**: 本项目仅供学习和研究使用，请遵守相关法律法规和微信使用条款。使用本工具进行商业活动或恶意行为，后果自负。

---

## 🎉 开始使用

现在你已经了解了Avatar Bot的所有功能，开始你的AI分身之旅吧！

```bash
# 启动服务器
avatar serve

