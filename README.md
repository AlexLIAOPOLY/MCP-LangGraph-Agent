# LangGraph MCP Tools 🤖

一个基于LangGraph和MCP（Model Context Protocol）的智能工具集成平台，支持自定义接入和使用各种MCP工具的ReAct代理。

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.44+-red.svg)
![LangGraph](https://img.shields.io/badge/langgraph-0.3+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ 功能特性

- 🎯 **智能代理**: 基于DeepSeek V3模型的ReAct代理，具备强大的推理和工具调用能力
- 🔧 **MCP工具集成**: 支持多种MCP工具服务器，包括GitHub、文件系统、Shell、浏览器自动化等
- 🗺️ **地理服务**: 集成高德地图API，提供地理编码、路径规划、天气查询等功能
- ⏰ **时间服务**: 支持多时区时间查询和格式化
- 🌐 **Web界面**: 基于Streamlit的现代化用户界面，支持实时对话和工具调用可视化
- 🔌 **可扩展**: 支持动态添加和管理MCP工具服务器
- 🔒 **安全**: 采用环境变量管理敏感信息，确保API密钥安全

## 🛠️ 支持的MCP工具

### 官方工具
- **GitHub**: 仓库管理、问题跟踪、PR创建和代码协作
- **文件系统**: 文件读写、目录操作和文件管理功能
- **Shell**: 安全的系统命令执行和脚本运行
- **浏览器自动化**: 网页操作、截图、点击和表单填写
- **序列思维**: 动态反思式问题解决和结构化思考

### 自定义工具
- **高德地图服务**: 地理编码、逆地理编码、POI搜索、天气查询、路径规划
- **时间服务**: 多时区时间获取和格式化

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 或 uv (推荐)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/MCP-LangGraph-Agent.git
cd MCP-LangGraph-Agent
```

2. **安装依赖**
```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入您的API密钥
nano .env
```

环境变量配置示例：
```env
# DeepSeek API密钥 (必需)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 高德地图API密钥 (可选，如果使用地图功能)
AMAP_API_KEY=your_amap_api_key_here

# GitHub Personal Access Token (可选，如果使用GitHub工具)
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
```

4. **启动应用**
```bash
streamlit run app.py
```

5. **访问应用**
打开浏览器访问 `http://localhost:8501`

## 📖 使用指南

### 基本使用

1. **启动应用**后，您会看到一个现代化的聊天界面
2. **在侧边栏**可以查看和管理已配置的MCP工具
3. **在聊天框**中输入您的问题，AI代理会自动选择合适的工具来回答
4. **工具调用过程**会实时显示，包括工具选择和执行结果

### 添加MCP工具

1. 点击侧边栏的 **"添加MCP工具"**
2. 输入工具配置的JSON格式：
```json
{
  "tool_name": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-example"],
    "transport": "stdio"
  }
}
```
3. 点击 **"添加工具"**
4. 点击 **"应用设置"** 重新加载工具

### 示例对话

- 🗺️ "帮我查询北京到上海的驾车路线"
- 📁 "列出当前目录的所有文件"
- 🌤️ "今天北京的天气怎么样？"
- ⏰ "现在东京时间是几点？"
- 💻 "帮我在GitHub上创建一个新的仓库"

## 🏗️ 项目结构

```
MCP-LangGraph-Agent/
├── app.py                 # 主应用文件
├── config.json           # MCP工具配置
├── utils.py              # 工具函数
├── mcp_server_amap.py    # 高德地图MCP服务器
├── mcp_server_time.py    # 时间服务MCP服务器
├── requirements.txt      # Python依赖
├── .env.example         # 环境变量模板
├── .gitignore           # Git忽略文件
└── README.md            # 项目说明
```

## 🔧 配置说明

### MCP工具配置

工具配置存储在 `config.json` 文件中，支持两种类型的MCP服务器：

1. **本地脚本类型**:
```json
{
  "tool_name": {
    "command": "python",
    "args": ["./your_script.py"],
    "transport": "stdio"
  }
}
```

2. **NPX包类型**:
```json
{
  "tool_name": {
    "command": "npx",
    "args": ["-y", "@org/package-name"],
    "transport": "stdio"
  }
}
```

### 环境变量

| 变量名 | 描述 | 必需 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥，用于AI对话 | 是 |
| `AMAP_API_KEY` | 高德地图API密钥，用于地理服务 | 否 |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub访问令牌，用于GitHub工具 | 否 |

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 这个仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📝 开发说明

### 添加新的MCP工具

1. 创建新的MCP服务器脚本
2. 在 `config.json` 中添加配置
3. 重启应用或点击"应用设置"

### 自定义UI

- 修改 `app.py` 中的CSS样式
- 调整Streamlit组件布局
- 添加新的交互功能

## 🐛 问题排查

### 常见问题

1. **工具调用失败**
   - 检查环境变量是否正确配置
   - 确认MCP服务器是否正常运行
   - 查看控制台错误日志

2. **API密钥错误**
   - 验证 `.env` 文件中的API密钥格式
   - 确认API密钥有效且有足够权限

3. **依赖安装问题**
   - 使用 `uv` 而不是 `pip` 安装依赖
   - 确保Python版本兼容性

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 强大的AI工作流框架
- [Streamlit](https://streamlit.io/) - 简单易用的Web应用框架
- [DeepSeek](https://www.deepseek.com/) - 高性能的AI模型
- [Model Context Protocol](https://modelcontextprotocol.io/) - 标准化的工具集成协议

---

⭐ 如果这个项目对您有帮助，请给它一个星星！
