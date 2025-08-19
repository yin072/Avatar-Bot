# WeChat RAG API 接口说明

## 概述

新增的接口用于管理微信聊天记录的处理和文件管理，包括执行完整的CSV转TXT流程（自动清理Qdrant数据）和清空文件功能（同时清理Qdrant数据）。

## 接口列表

### 1. 执行微信数据处理流程

**接口信息**
- **URL**: `GET /wechat_rag/count_txt`
- **功能**: 执行完整的微信数据处理流程：先清理Qdrant数据，然后CSV转TXT + 存入Qdrant，返回生成的txt文件个数
- **参数**: 无

**处理流程**
1. **自动清理Qdrant数据**：清空local_qdrant目录下的所有数据
2. 遍历 `wxdump_work/export` 目录下的所有CSV文件
3. 将每个CSV文件转换为对应的TXT文件
4. 将TXT文件内容切片并存入Qdrant数据库
5. 统计生成的TXT文件个数并返回

**响应示例**

#### 成功响应
```json
{
    "code": 200,
    "status": "processing_completed",
    "data": {
        "message": "微信数据处理完成，共处理 15 个聊天数据文件"
    }
}
```

#### 错误响应
```json
{
    "code": 500,
    "status": "processing_failed",
    "data": {
        "message": "微信数据处理失败: 具体错误信息"
    }
}
```

### 2. 清空所有文件

**接口信息**
- **URL**: `POST /wechat_rag/clear_files`
- **功能**: 清空 wxdump_work/export 目录下的所有csv和txt文件，同时清理local_qdrant数据
- **参数**: 无

**清理内容**
- 删除所有CSV和TXT文件
- 清空local_qdrant/collection目录下的所有数据
- 删除.lock锁文件
- 清空meta.json元数据文件内容

**响应示例**

#### 成功响应
```json
{
    "code": 200,
    "status": "files_cleared",
    "data": {
        "message": {
            "cleared_count": 20,
            "cleared_files": ["chat1.csv", "chat1.txt", "chat2.csv", "chat2.txt"],
            "qdrant_cleared": true,
            "message": "成功清空 20 个文件，Qdrant数据也已清理"
        }
    }
}
```

#### 目录不存在响应
```json
{
    "code": 200,
    "status": "no_export_folder",
    "data": {
        "message": "导出目录不存在"
    }
}
```

#### 错误响应
```json
{
    "code": 500,
    "status": "clear_files_failed",
    "data": {
        "message": "清空文件失败: 具体错误信息"
    }
}
```

## 功能说明

### 微信数据处理流程
- **自动清理**: 每次执行前自动清理Qdrant数据，确保数据一致性
- **CSV转TXT**: 将微信导出的CSV文件转换为可读的TXT格式
- **隐私保护**: 自动清洗手机号、身份证等敏感信息
- **时间格式化**: 保留消息发送时间信息
- **Qdrant存储**: 将TXT内容切片并存入向量数据库
- **文件计数**: 在转换过程中统计生成的TXT文件个数

### 文件清空功能
- 递归遍历 `wxdump_work/export` 目录
- 删除所有 `.csv` 和 `.txt` 文件
- **同时清理Qdrant数据**：
  - 删除collection目录下的所有内容
  - 删除.lock锁文件
  - 清空meta.json文件内容
- 返回删除的文件数量和文件名列表
- 包含错误处理，单个文件删除失败不影响其他文件

## 使用场景

1. **数据导入**: 前端调用接口执行完整的CSV转TXT流程（自动清理旧数据）
2. **进度监控**: 实时获取处理结果和生成的文件数量
3. **数据清理**: 用户可以在重新导入聊天记录前清空旧文件和Qdrant数据
4. **状态管理**: 监控整个数据处理流程的完成状态
5. **数据重置**: 完全清理所有相关数据，重新开始

## 注意事项

1. **处理时间**: CSV转TXT流程可能需要较长时间，建议前端显示进度
2. **自动清理**: count_txt接口会自动清理Qdrant数据，无需手动清理
3. **文件路径**: 接口自动定位到正确的目录路径
4. **权限要求**: 确保应用有读写和删除文件的权限
5. **安全考虑**: 清空操作不可逆，建议前端添加确认提示
6. **数据一致性**: 每次处理前自动清理Qdrant数据，确保数据一致性
7. **错误处理**: 所有操作都包含完善的错误处理机制

## 技术实现

- 使用 `pathlib.Path` 进行跨平台路径处理
- 动态导入 `wechat_rag` 模块的功能
- 统一的错误处理和响应格式
- 支持递归遍历子目录
- 集成化的处理流程，避免重复计算
- 智能的Qdrant数据清理，保留目录结构
