import streamlit as st
import asyncio
import nest_asyncio
import json
import os
import platform
# ----- 1. 页面和CSS美化 -----

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Apply nest_asyncio: Allow nested calls within an already running event loop
nest_asyncio.apply()

# Create and reuse global event loop (create once and continue using)
if "event_loop" not in st.session_state:
    loop = asyncio.new_event_loop()
    st.session_state.event_loop = loop
    asyncio.set_event_loop(loop)

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils import astream_graph, random_uuid
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.messages.tool import ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_deepseek import ChatDeepSeek

# Load environment variables (get API keys and settings from .env file)
load_dotenv(override=True)

# config.json file path setting
CONFIG_FILE_PATH = "config.json"


# 从 JSON 文件中加载设置
def load_config_from_json():
    """
    Loads settings from config.json file.
    Creates a file with default settings if it doesn't exist.

    Returns:
        dict: Loaded settings
    """
    default_config = {
        "get_current_time": {
            "command": "python",
            "args": ["./mcp_server_time.py"],
            "transport": "stdio"
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Create file with default settings if it doesn't exist
            save_config_to_json(default_config)
            return default_config
    except Exception as e:
        st.error(f"Error loading settings file: {str(e)}")
        return default_config

# 将设置保存到 JSON 文件
def save_config_to_json(config):
    """
    Saves settings to config.json file.

    Args:
        config (dict): Settings to save
    
    Returns:
        bool: Save success status
    """
    try:
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Error saving settings file: {str(e)}")
        return False

# 直接使用宽布局
st.set_page_config(page_title="LangGraph Agent MCP Tools", layout="wide")

# 添加自定义CSS样式
st.markdown("""
<style>
    /* 主题色彩配置 - 升级版 */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --background-color: #f093fb;
        --text-color: #2C3E50;
        --card-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
        --hover-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
    }
    
    /* 侧边栏样式 */
    .css-1d391kg {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
    }
    
    /* 主内容区域 */
    .main .block-container {
        padding-top: 0.5rem;
        max-width: none;
    }
    
    /* 标题样式 */
    h1 {
        color: var(--primary-color);
        font-weight: 600;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 0.5rem;
    }
    
    /* 子标题样式 */
    h2, h3 {
        color: var(--text-color);
        font-weight: 500;
    }
    
    /* 按钮样式优化 */
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #ddd;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        border-color: var(--primary-color);
        color: var(--primary-color);
    }
    
    /* 输入框样式 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 6px;
        border: 1px solid #ddd;
        transition: border-color 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(46, 134, 171, 0.1);
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div {
        border-radius: 6px;
    }
    
    /* 滑块样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, var(--primary-color) 0%, #ddd 0%);
    }
    
    /* 扩展器样式 */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 6px;
        border: 1px solid #e0e0e0;
    }
    
    /* 消息样式 */
    [data-testid="stChatMessage"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* 侧边栏分割线 */
    hr {
        margin: 1rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e0e0e0, transparent);
    }
    
    /* 工具列表样式 */
    .element-container {
        margin-bottom: 0.5rem;
    }
    
    /* 工具卡片样式 */
    .tool-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .tool-card:hover {
        border-color: var(--primary-color);
        box-shadow: 0 2px 8px rgba(46, 134, 171, 0.15);
    }
    
    .tool-name {
        color: var(--primary-color);
        font-weight: 600;
        font-size: 1.1em;
        margin-bottom: 6px;
    }
    
    .tool-description {
        color: #666;
        font-size: 0.9em;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    
    .tool-config {
        color: #888;
        font-size: 0.8em;
        font-family: 'Courier New', monospace;
        background: #f8f9fa;
        padding: 4px 8px;
        border-radius: 4px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)





st.sidebar.divider()  

# 页面标题和描述
# 简洁的标题区域
st.markdown("""
<div style="text-align: center; padding: 15px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
    <h1 style="color: white; margin: 0; font-size: 2.2rem; font-weight: 600;">
        LangGraph MCP Tools
    </h1>
    <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 1rem;">
        智能MCP工具集成平台 - 可自定义接入和使用MCP工具的ReAct代理
    </p>
</div>
""", unsafe_allow_html=True)


# 设置系统提示词
SYSTEM_PROMPT = """<ROLE>
You are a smart agent with an ability to use tools. 
You will be given a question and you will use the tools to answer the question.
Pick the most relevant tool to answer the question. 
If you are failed to answer the question, try different tools to get context.
Your answer should be very polite and professional.
</ROLE>

----

<INSTRUCTIONS>
Step 1: Analyze the question
- Analyze user's question and final goal.
- If the user's question is consist of multiple sub-questions, split them into smaller sub-questions.

Step 2: Pick the most relevant tool
- Pick the most relevant tool to answer the question.
- If you are failed to answer the question, try different tools to get context.

Step 3: Answer the question
- Answer the question in the same language as the question.
- Your answer should be very polite and professional.

Step 4: Provide the source of the answer(if applicable)
- If you've used the tool, provide the source of the answer.
- Valid sources are either a website(URL) or a document(PDF, etc).

Guidelines:
- If you've used the tool, your answer should be based on the tool's output(tool's output is more important than your own knowledge).
- If you've used the tool, and the source is valid URL, provide the source(URL) of the answer.
- Skip providing the source if the source is not URL.
- Answer in the same language as the question.
- Answer should be concise and to the point.
- Avoid response your output with any other information than the answer and the source.  
</INSTRUCTIONS>

----

<OUTPUT_FORMAT>
(concise answer to the question)

**Source**(if applicable)
- (source1: valid URL)
- (source2: valid URL)
- ...
</OUTPUT_FORMAT>
"""


# 初始化会话状态
if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False  
    st.session_state.agent = None  
    st.session_state.history = []  
    st.session_state.mcp_client = None  
    st.session_state.timeout_seconds = (
        120  
    )
    st.session_state.selected_model = (
        "deepseek-chat"   # 默认的模型是 DeepSeek v3
    )
    st.session_state.recursion_limit = 100  # 递归调用限制，默认100

if "thread_id" not in st.session_state:
    st.session_state.thread_id = random_uuid()


# --- 工具函数定义 ---
async def cleanup_mcp_client():
    """
    Safely terminates the existing MCP client.

    Properly releases resources if an existing client exists.
    """
    if "mcp_client" in st.session_state and st.session_state.mcp_client is not None:
        try:
            # 新版本不需要手动调用__aexit__，直接设置为None即可
            st.session_state.mcp_client = None
        except Exception as e:
            import traceback
            st.error(f"清理MCP客户端时出错: {str(e)}")
            st.session_state.mcp_client = None

def print_message():
    """
    Displays chat history on the screen.

    Distinguishes between user and assistant messages on the screen,
    and displays tool call information within the assistant message container.
    """
    i = 0
    while i < len(st.session_state.history):
        message = st.session_state.history[i]
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])
            i += 1
        elif message["role"] == "assistant":
            # 创建助手消息容器
            with st.chat_message("assistant"):
                # 显示助手消息内容
                st.markdown(message["content"])

                # 检查下一个消息是否是工具调用信息
                if (
                    i + 1 < len(st.session_state.history)
                    and st.session_state.history[i + 1]["role"] == "assistant_tool"
                ):
                    # 在同一个容器中显示工具调用信息
                    with st.expander("工具调用信息", expanded=False):
                        st.markdown(st.session_state.history[i + 1]["content"])
                    i += 2  # 递增2，因为我们处理了两个消息
                else:
                    i += 1  # 递增1，因为我们只处理了一个常规消息
        else:
            # 跳过助手工具消息，因为它们已经在上面处理了
            i += 1


def get_streaming_callback(text_placeholder, tool_placeholder):
    """
    Creates a streaming callback function.

    This function creates a callback function to display responses generated from the LLM in real-time.
    It displays text responses and tool call information in separate areas.

    Args:
        text_placeholder: Streamlit component to display text responses
        tool_placeholder: Streamlit component to display tool call information

    Returns:
        callback_func: Streaming callback function
        accumulated_text: List to store accumulated text responses
        accumulated_tool: List to store accumulated tool call information
    """
    accumulated_text = []
    accumulated_tool = []

    def callback_func(message: dict):
        nonlocal accumulated_text, accumulated_tool
        message_content = message.get("content", None)

        if isinstance(message_content, AIMessageChunk):
            content = message_content.content
            if (
                hasattr(message_content, "tool_calls")
                and message_content.tool_calls
                and len(message_content.tool_calls[0]["name"]) > 0
            ):
                tool_call_info = message_content.tool_calls[0]
                accumulated_tool.append("\n```json\n" + str(tool_call_info) + "\n```\n")
                with tool_placeholder.expander(
                    "工具调用信息", expanded=True
                ):
                    st.markdown("".join(accumulated_tool))
            # 如果内容是字符串类型
            elif isinstance(content, str):
                accumulated_text.append(content)
                text_placeholder.markdown("".join(accumulated_text))
            # 如果存在无效的工具调用信息
            elif (
                hasattr(message_content, "invalid_tool_calls")
                and message_content.invalid_tool_calls
            ):
                tool_call_info = message_content.invalid_tool_calls[0]
                accumulated_tool.append("\n```json\n" + str(tool_call_info) + "\n```\n")
                with tool_placeholder.expander(
                    "工具调用信息 (无效)", expanded=True
                ):
                    st.markdown("".join(accumulated_tool))
            # 如果tool_call_chunks属性存在
            elif (
                hasattr(message_content, "tool_call_chunks")
                and message_content.tool_call_chunks
            ):
                tool_call_chunk = message_content.tool_call_chunks[0]
                accumulated_tool.append(
                    "\n```json\n" + str(tool_call_chunk) + "\n```\n"
                )
                with tool_placeholder.expander(
                    "工具调用信息", expanded=True
                ):
                    st.markdown("".join(accumulated_tool))
            # 如果tool_calls存在additional_kwargs中（支持各种模型兼容性）
            elif (
                hasattr(message_content, "additional_kwargs")
                and "tool_calls" in message_content.additional_kwargs
            ):
                tool_call_info = message_content.additional_kwargs["tool_calls"][0]
                accumulated_tool.append("\n```json\n" + str(tool_call_info) + "\n```\n")
                with tool_placeholder.expander(
                    "工具调用信息", expanded=True
                ):
                    st.markdown("".join(accumulated_tool))
        # 如果消息是工具消息（工具响应）
        elif isinstance(message_content, ToolMessage):
            accumulated_tool.append(
                "\n```json\n" + str(message_content.content) + "\n```\n"
            )
            with tool_placeholder.expander("工具调用信息", expanded=True):
                st.markdown("".join(accumulated_tool))
        return None
    return callback_func, accumulated_text, accumulated_tool


async def process_query(query, text_placeholder, tool_placeholder, timeout_seconds=60):
    """
    Processes user questions and generates responses.

    This function passes the user's question to the agent and streams the response in real-time.
    Returns a timeout error if the response is not completed within the specified time.

    Args:
        query: Text of the question entered by the user
        text_placeholder: Streamlit component to display text responses
        tool_placeholder: Streamlit component to display tool call information
        timeout_seconds: Response generation time limit (seconds)

    Returns:
        response: Agent's response object
        final_text: Final text response
        final_tool: Final tool call information
    """
    try:
        if st.session_state.agent:
            streaming_callback, accumulated_text_obj, accumulated_tool_obj = (
                get_streaming_callback(text_placeholder, tool_placeholder)
            )
            try:
                response = await asyncio.wait_for(
                    astream_graph(
                        st.session_state.agent,
                        {"messages": [HumanMessage(content=query)]},
                        callback=streaming_callback,
                        config=RunnableConfig(
                            recursion_limit=st.session_state.recursion_limit,
                            thread_id=st.session_state.thread_id,
                        ),
                    ),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                error_msg = f"请求时间超过 {timeout_seconds} 秒. 请稍后再试."
                return {"error": error_msg}, error_msg, ""

            final_text = "".join(accumulated_text_obj)
            final_tool = "".join(accumulated_tool_obj)
            return response, final_text, final_tool
        else:
            return (
                {"error": "🚫 代理未初始化."},
                "🚫 代理未初始化.",
                "",
            )
    except Exception as e:
        import traceback

        error_msg = f"❌ 查询处理时发生错误: {str(e)}\n{traceback.format_exc()}"
        return {"error": error_msg}, error_msg, ""


async def initialize_session(mcp_config=None):
    """
    Initializes MCP session and agent.

    Args:
        mcp_config: MCP tool configuration information (JSON). Uses default settings if None

    Returns:
        bool: Initialization success status
    """
    try:
        with st.spinner("连接到MCP服务器..."):
            # 首先安全地清理现有的客户端
            await cleanup_mcp_client()

            if mcp_config is None:
                # 从config.json文件加载设置
                mcp_config = load_config_from_json()
            
            # 使用新的API方式创建客户端
            client = MultiServerMCPClient(mcp_config)
            
            # 方法1: 直接获取工具
            tools = await client.get_tools()
            st.session_state.tool_count = len(tools)
            st.session_state.mcp_client = client

            # 根据选择初始化适当的模型
            selected_model = st.session_state.selected_model

            model = ChatDeepSeek(
                model=selected_model,
                temperature=0.1,
            )
            agent = create_react_agent(
                model,
                tools,
                checkpointer=MemorySaver(),
                prompt=SYSTEM_PROMPT,
            )
            st.session_state.agent = agent
            st.session_state.session_initialized = True
            return True
            
    except Exception as e:
        st.error(f"MCP客户端初始化失败: {str(e)}")
        st.error("请检查MCP服务器配置是否正确")
        return False


# --- Sidebar: 工具设置 ---
with st.sidebar:
    st.markdown("### MCP工具管理")

    # 管理扩展器状态
    if "mcp_tools_expander" not in st.session_state:
        st.session_state.mcp_tools_expander = False

    # MCP 工具添加界面
    with st.expander("添加 MCP 工具", expanded=st.session_state.mcp_tools_expander):
        # 从config.json文件加载设置
        loaded_config = load_config_from_json()
        default_config_text = json.dumps(loaded_config, indent=2, ensure_ascii=False)
        
        # 根据现有的mcp_config_text创建pending config
        if "pending_mcp_config" not in st.session_state:
            try:
                st.session_state.pending_mcp_config = loaded_config
            except Exception as e:
                st.error(f"Failed to set initial pending config: {e}")

        # 添加单个工具的UI
        st.markdown("**添加新工具**")
        st.markdown("请输入工具配置 (JSON格式):")
        # 提供简化的示例
        example_json = {
            "tool_name": {
                "command": "python",
                "args": ["./your_script.py"],
                "transport": "stdio"
            }
        }

        default_text = json.dumps(example_json, indent=2, ensure_ascii=False)

        new_tool_json = st.text_area(
            "工具配置",
            default_text,
            height=200,
        )

        # 添加按钮
        if st.button(
            "添加工具",
            type="primary",
            key="add_tool_button",
            use_container_width=True,
        ):
            try:
                # 验证输入
                if not new_tool_json.strip().startswith(
                    "{"
                ) or not new_tool_json.strip().endswith("}"):
                    st.error("JSON must start and end with curly braces ({}).")
                    st.markdown('Correct format: `{ "tool_name": { ... } }`')
                else:
                    # 解析 JSON
                    parsed_tool = json.loads(new_tool_json)

                    # 检查是否在mcpServers格式中，并相应处理
                    if "mcpServers" in parsed_tool:
                        # 将mcpServers的内容移动到顶层
                        parsed_tool = parsed_tool["mcpServers"]
                        st.info(
                            "'mcpServers' format detected. Converting automatically."
                        )

                    # 检查输入的工具数量
                    if len(parsed_tool) == 0:
                        st.error("Please enter at least one tool.")
                    else:
                        # 处理所有工具
                        success_tools = []
                        for tool_name, tool_config in parsed_tool.items():
                            # 检查URL字段并设置transport
                            if "url" in tool_config:
                                # 如果URL存在，则设置transport为"sse"
                                tool_config["transport"] = "sse"
                                st.info(
                                    f"URL detected in '{tool_name}' tool, setting transport to 'sse'."
                                )
                            elif "transport" not in tool_config:
                                # 如果URL不存在且transport未指定，则设置默认值"stdio"
                                tool_config["transport"] = "stdio"

                            # 检查必需字段
                            if (
                                "command" not in tool_config
                                and "url" not in tool_config
                            ):
                                st.error(
                                    f"'{tool_name}' tool configuration requires either 'command' or 'url' field."
                                )
                            elif "command" in tool_config and "args" not in tool_config:
                                st.error(
                                    f"'{tool_name}' tool configuration requires 'args' field."
                                )
                            elif "command" in tool_config and not isinstance(
                                tool_config["args"], list
                            ):
                                st.error(
                                    f"'args' field in '{tool_name}' tool must be an array ([]) format."
                                )
                            else:
                                # 将工具添加到pending_mcp_config
                                st.session_state.pending_mcp_config[tool_name] = (
                                    tool_config
                                )
                                success_tools.append(tool_name)

                        # 成功消息
                        if success_tools:
                            if len(success_tools) == 1:
                                st.success(
                                    f"{success_tools[0]} 工具已添加. 点击 '应用设置' 按钮以应用."
                                )
                            else:
                                tool_names = ", ".join(success_tools)
                                st.success(
                                    f"总共 {len(success_tools)} 个工具 ({tool_names}) 已添加. 点击 '应用设置' 按钮以应用."
                                )
                            # 添加工具后折叠扩展器
                            st.session_state.mcp_tools_expander = False
                            st.rerun()

            except json.JSONDecodeError as e:
                st.error(f"JSON 解析错误: {e}")
                st.markdown(
                    f"""
                **如何修复**:
                1. 检查您的JSON格式是否正确.
                2. 所有键必须用双引号包裹 (").
                3. 字符串值也必须用双引号包裹 (").
                4. 在字符串中使用双引号时，必须转义 (\").
                """
                )
            except Exception as e:
                st.error(f"发生错误: {e}")

    # 显示已注册的MCP服务器列表并添加删除按钮
    with st.expander("已注册的MCP服务器", expanded=True):
        try:
            pending_config = st.session_state.pending_mcp_config
        except Exception as e:
            st.error("不是一个有效的MCP工具配置.")
        else:
            # 工具描述字典 - 包含完整的MCP服务器描述
            tool_descriptions = {
                # 核心项目工具
                "get_current_time": "时间工具 - 获取当前系统时间，支持不同时区和格式化选项",
                "amap_geocoding": "高德地图地理编码服务 - 提供地址转坐标、坐标转地址、POI搜索、天气查询、路径规划等功能",
                
                # 官方MCP服务器 (常见的NPX包)
                "github": "GitHub集成工具 - 支持仓库管理、问题跟踪、PR创建和代码协作",
                "filesystem": "文件系统工具 - 提供文件读写、目录操作和文件管理功能，安全访问指定目录", 
                "shell": "Shell命令工具 - 支持系统命令执行和脚本运行，提供安全的命令行访问",
                "context7": "Context7文档工具 - 提供库文档检索和API参考，支持编程学习和开发",
                "sequential-thinking": "序列思维工具 - 动态反思式问题解决，通过结构化思考过程分析复杂问题",
                "browser-tools-mcp": "浏览器自动化工具 - 支持网页操作、截图、点击和表单填写等自动化任务",
                "edgeone-pages-mcp-server": "EdgeOne Pages部署工具 - 支持HTML和静态网站快速部署到CDN",
                
                # 时间和日期工具
                "time": "时间处理工具，提供时间计算、转换和格式化功能",
                "datetime": "日期时间管理工具，支持复杂的日期时间操作",
                
                # 地图和位置服务
                "google_maps": "Google Maps API工具，提供地图搜索和路径规划",
                "geocoding": "地理编码服务，支持地址解析和坐标转换",
                
                # 开发工具
                "git": "Git版本控制工具，提供代码版本管理和协作功能",
                "file": "文件处理工具，支持文件上传、下载和格式转换",
                
                # 网络和搜索
                "web_search": "网络搜索工具，提供实时搜索和网页内容抓取功能",
                "web": "网页访问工具，支持HTTP请求和网页内容提取",
                "curl": "网络请求工具，支持各种HTTP操作和API调用",
                "requests": "HTTP请求库，提供RESTful API访问功能",
                "brave-search": "Brave搜索工具 - 提供隐私友好的网络搜索服务",
                
                # 计算和数据处理
                "calculator": "数学计算器工具，支持基础运算和高级数学函数",
                "math": "数学计算工具，提供科学计算和统计分析功能",
                "data_analysis": "数据分析工具，支持数据处理和可视化",
                "pandas": "数据处理工具，提供数据清洗和分析功能",
                "sqlite": "SQLite数据库工具 - 轻量级数据库管理和SQL查询功能",
                "postgres": "PostgreSQL数据库工具 - 企业级关系数据库管理",
                
                # 通信和消息
                "email": "邮件发送工具，支持文本和HTML格式邮件发送",
                "smtp": "SMTP邮件服务，提供邮件发送和管理功能",
                "slack": "Slack集成工具 - 支持消息发送、频道管理和团队协作",
                "telegram": "Telegram机器人工具，提供消息推送功能",
                "discord": "Discord机器人工具 - 支持服务器管理和消息交互",
                
                # 翻译和语言
                "translator": "多语言翻译工具，支持多种语言互译",
                "translation": "翻译服务工具，提供实时翻译和语言检测",
                "language": "语言处理工具，支持文本分析和语言识别",
                
                # 天气和环境
                "weather": "天气查询工具，提供实时天气和天气预报信息",
                "climate": "气候数据工具，提供气象信息和环境监测",
                
                # 数据库和存储
                "database": "数据库连接工具，支持SQL查询和数据操作",
                "sql": "SQL数据库工具，提供数据查询和管理功能",
                "redis": "Redis缓存工具，提供高性能数据存储服务",
                "mongodb": "MongoDB文档数据库工具，支持NoSQL数据操作",
                
                # 媒体和图像
                "image": "图像处理工具，支持图片编辑和格式转换",
                "video": "视频处理工具，提供视频编辑和转码功能",
                "audio": "音频处理工具，支持音频编辑和格式转换",
                
                # AI和机器学习
                "openai": "OpenAI API工具，提供GPT模型访问和AI功能",
                "anthropic": "Anthropic Claude API工具，支持对话和文本生成",
                "huggingface": "Hugging Face模型工具，提供机器学习模型访问",
                
                # 系统和监控
                "system": "系统监控工具，提供系统状态和性能监测",
                "docker": "Docker容器工具，支持容器管理和部署",
                "kubernetes": "Kubernetes集群工具，提供容器编排功能",
                
                # 云服务和部署
                "aws": "AWS云服务工具 - 支持云资源管理和服务调用",
                "gcp": "Google Cloud Platform工具 - 提供GCP服务集成",
                "azure": "Microsoft Azure工具 - 支持Azure云服务管理",
                "vercel": "Vercel部署工具 - 支持前端项目快速部署",
                "netlify": "Netlify托管工具 - 提供静态网站部署和管理",
            }
            
            if not pending_config:
                st.info("当前系统中没有已注册的MCP服务器。请通过上方的'添加MCP工具'功能添加您需要的MCP服务器配置，然后点击'应用设置'按钮来激活这些工具。MCP服务器将为您的智能代理提供各种专业功能，如文件操作、网络请求、数据处理等能力。")
            else:
                # 获取已初始化的工具详情
                available_tools = []
                if st.session_state.session_initialized and st.session_state.mcp_client:
                    try:
                        tools = st.session_state.event_loop.run_until_complete(
                            st.session_state.mcp_client.get_tools()
                        )
                        available_tools = [tool.name for tool in tools]
                    except Exception as e:
                        st.error(f"获取工具列表失败: {str(e)}")
                
                # 遍历pending config中的键（MCP服务器名称）
                for i, server_name in enumerate(list(pending_config.keys())):
                    # 获取服务器配置
                    server_config = pending_config[server_name]
                    description = tool_descriptions.get(server_name, f"{server_name} MCP服务器 - 这是一个Model Context Protocol工具服务器，为系统提供特定功能和工具集成能力")
                    
                    # 服务器配置预览
                    config_info = []
                    if "command" in server_config:
                        config_info.append(f"命令: {server_config['command']}")
                    if "transport" in server_config:
                        config_info.append(f"传输: {server_config['transport']}")
                    if "url" in server_config:
                        config_info.append(f"URL: {server_config['url']}")
                    
                    # 获取此服务器提供的工具 - 改进匹配逻辑
                    server_tools = []
                    if available_tools:
                        # 动态获取实际工具列表而不是使用硬编码
                        # 根据工具名称模式智能分组
                        def get_tools_for_server(server_name, all_tools):
                            """根据服务器名称和工具特征智能分组工具"""
                            tools_list = []
                            
                            # 基于服务器名称的工具模式匹配
                            patterns = {
                                "amap_geocoding": ["geocoding", "reverse_geocoding", "poi_search", "weather_query", "route_planning", "distance_calculation"],
                                "get_current_time": ["get_current_time"],
                                "github": lambda name: "github" in name.lower() or any(keyword in name.lower() for keyword in ["repo", "issue", "pull", "commit", "branch"]),
                                "filesystem": lambda name: any(keyword in name.lower() for keyword in ["read_file", "write_file", "list_directory", "create_directory", "delete_file", "get_file", "search_files"]),
                                "shell": lambda name: any(keyword in name.lower() for keyword in ["shell", "command", "exec", "run"]),
                                "context7": lambda name: any(keyword in name.lower() for keyword in ["resolve", "get-library", "library"]),
                                "edgeone-pages-mcp-server": lambda name: any(keyword in name.lower() for keyword in ["deploy", "edge", "pages"]),
                                "browser-tools-mcp": lambda name: any(keyword in name.lower() for keyword in ["browser", "navigate", "click", "screenshot"]),
                                "sequential-thinking": lambda name: any(keyword in name.lower() for keyword in ["thinking", "sequential"]),
                            }
                            
                            if server_name in patterns:
                                pattern = patterns[server_name]
                                if isinstance(pattern, list):
                                    # 精确匹配列表
                                    tools_list = [tool for tool in all_tools if tool in pattern]
                                elif callable(pattern):
                                    # 使用函数匹配
                                    tools_list = [tool for tool in all_tools if pattern(tool)]
                            
                            return tools_list
                        
                        # 使用新的智能分组函数
                        server_tools = get_tools_for_server(server_name, available_tools)
                    
                    # 如果仍然没有找到工具，显示空列表而不是所有工具
                    # 这避免了将所有86个工具分配给每个服务器的问题
                    if not server_tools:
                        server_tools = []
                    
                    # 创建状态标识
                    status_color = "#28a745" if st.session_state.session_initialized else "#6c757d"
                    if st.session_state.session_initialized and server_tools:
                        status_text = f"已激活 • {len(server_tools)}个工具"
                    elif st.session_state.session_initialized:
                        status_text = "已激活"
                    else:
                        status_text = "待激活"
                    
                    col1, col2 = st.columns([8, 2])
                    with col1:
                        # 服务器名称和状态
                        st.markdown(f"**{server_name}** `{status_text}`")
                        
                        # 服务器描述
                        st.markdown(f'<p style="color: #666; font-size: 0.9em; margin-top: -10px; margin-bottom: 8px;">{description}</p>', unsafe_allow_html=True)
                        
                        # 配置信息
                        if config_info:
                            st.markdown(f'<p style="color: #888; font-size: 0.8em; margin-top: -5px; margin-bottom: 8px;">{" | ".join(config_info)}</p>', unsafe_allow_html=True)
                        
                        # 工具列表 - 使用真实的工具描述
                        if server_tools and st.session_state.session_initialized:
                            st.markdown(f'**包含的工具 ({len(server_tools)}个):**')
                            
                            # 获取真实的工具描述
                            for tool_name in server_tools:
                                # 从实际工具对象中获取描述
                                tool_obj = None
                                for tool in tools:
                                    if tool.name == tool_name:
                                        tool_obj = tool
                                        break
                                
                                if tool_obj and tool_obj.description:
                                    # 使用完整的真实描述
                                    desc = tool_obj.description.strip()
                                    # 如果描述很长，保留完整内容但格式化显示
                                    if '\n' in desc:
                                        # 如果有多行，只显示第一段但保留完整信息
                                        desc = desc.replace('\n\n', ' ').replace('\n', ' ')
                                else:
                                    desc = "此工具暂未提供详细描述信息"
                                
                                st.markdown(f"- `{tool_name}`: {desc}")
                    
                    with col2:
                        st.markdown("<br>", unsafe_allow_html=True)  # 垂直对齐
                        if st.button("删除", key=f"delete_{server_name}", type="secondary", use_container_width=True):
                            # 从pending config中删除服务器并立即保存
                            del st.session_state.pending_mcp_config[server_name]
                            
                            # 立即保存到配置文件
                            save_result = save_config_to_json(st.session_state.pending_mcp_config)
                            if save_result:
                                st.success(f"{server_name} 服务器已成功删除并保存!")
                                # 重新初始化会话以应用更改
                                st.session_state.session_initialized = False
                                st.session_state.agent = None
                                success = st.session_state.event_loop.run_until_complete(
                                    initialize_session(st.session_state.pending_mcp_config)
                                )
                                if success:
                                    st.success("设置已自动重新应用!")
                            else:
                                st.error("删除失败，无法保存到配置文件")
                            st.rerun()
                    
                    # 添加分割线
                    st.markdown("---")

    st.markdown("---")

# --- Sidebar: 系统信息和操作按钮部分 ---
with st.sidebar:
    st.markdown("### 状态信息")
    # 显示简化的系统状态
    tool_count = st.session_state.get('tool_count', '系统正在初始化，正在加载和连接MCP服务器')
    status_text = "已就绪" if st.session_state.session_initialized else "初始化中"
    
    st.info(f"""
    **系统状态**: {status_text}
    
    **可用工具**: {tool_count}个
    """)

    # 应用设置按钮 - 根据初始化状态显示不同文本
    button_text = "重新应用设置" if st.session_state.session_initialized else "应用设置"
    if st.button(
        button_text,
        key="apply_button",
        type="primary",
        use_container_width=True,
    ):
     
        apply_status = st.empty()
        with apply_status.container():
            st.warning("正在应用配置更改，重新初始化MCP服务器连接，请稍候等待完成...")
            progress_bar = st.progress(0)

            # 保存设置
            st.session_state.mcp_config_text = json.dumps(
                st.session_state.pending_mcp_config, indent=2, ensure_ascii=False
            )

            # 将设置保存到config.json文件
            save_result = save_config_to_json(st.session_state.pending_mcp_config)
            if not save_result:
                st.error("保存设置文件失败.")
            
            progress_bar.progress(15)

            # 准备会话初始化
            st.session_state.session_initialized = False
            st.session_state.agent = None

            # 更新进度
            progress_bar.progress(30)

            # 运行初始化
            success = st.session_state.event_loop.run_until_complete(
                initialize_session(st.session_state.pending_mcp_config)
            )

            # 更新进度
            progress_bar.progress(100)

            if success:
                st.success("新设置已应用.")
                # 折叠工具添加扩展器
                if "mcp_tools_expander" in st.session_state:
                    st.session_state.mcp_tools_expander = False
            else:
                st.error("应用设置失败.")

        # 刷新页面
        st.rerun()

    st.markdown("---")
    
    # 操作按钮部分
    st.markdown("### 快捷操作")

    # 重置对话按钮
    if st.button("重置对话", use_container_width=True, type="primary"):
        # 重置thread_id
        st.session_state.thread_id = random_uuid()

        # 重置对话历史
        st.session_state.history = []

        # 通知消息
        st.success("对话已重置")

        # 刷新页面
        st.rerun()
    
    # 对话历史统计
    if st.session_state.history:
        st.markdown(f"**对话统计**: {len([h for h in st.session_state.history if h['role'] == 'user'])} 条对话")
    
    # 管理功能按钮
    st.markdown("---")
    st.markdown("**配置管理**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("导出设置", use_container_width=True):
            config_str = json.dumps(st.session_state.get('pending_mcp_config', {}), indent=2, ensure_ascii=False)
            st.download_button(
                label="下载配置文件",
                data=config_str,
                file_name="mcp_config.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col2:
        if st.button("系统详情", use_container_width=True):
            st.write("**系统状态**:")
            st.write(f"初始化: {'已完成' if st.session_state.session_initialized else '进行中'}")
            st.write(f"会话ID: `{st.session_state.get('thread_id', 'N/A')}`")
            st.write(f"连接: {'在线' if st.session_state.session_initialized else '离线'}")


# --- Initialize default session (if not initialized) ---
if not st.session_state.session_initialized:
    with st.spinner("正在初始化MCP服务器和代理..."):
        # 自动加载配置并初始化
        loaded_config = load_config_from_json()
        if "pending_mcp_config" not in st.session_state:
            st.session_state.pending_mcp_config = loaded_config
        
        # 自动运行初始化
        success = st.session_state.event_loop.run_until_complete(
            initialize_session(st.session_state.pending_mcp_config)
        )
        
        if success:
            st.success("系统已自动初始化完成!")
            st.rerun()
        else:
            st.error("自动初始化失败，请检查配置或手动点击'应用设置'按钮。")


# --- 打印对话历史 ---
print_message()

# --- 用户输入和处理 ---
user_query = st.chat_input("输入您的问题")
if user_query:
    if st.session_state.session_initialized:
        st.chat_message("user").markdown(user_query)
        with st.chat_message("assistant"):
            tool_placeholder = st.empty()
            text_placeholder = st.empty()
            resp, final_text, final_tool = (
                st.session_state.event_loop.run_until_complete(
                    process_query(
                        user_query,
                        text_placeholder,
                        tool_placeholder,
                        st.session_state.timeout_seconds,
                    )
                )
            )
        if "error" in resp:
            st.error(resp["error"])
        else:
            st.session_state.history.append({"role": "user", "content": user_query})
            st.session_state.history.append(
                {"role": "assistant", "content": final_text}
            )
            if final_tool.strip():
                st.session_state.history.append(
                    {"role": "assistant_tool", "content": final_tool}
                )
            st.rerun()
    else:
        st.warning(
            "系统正在初始化MCP服务器连接和智能代理，请稍候等待初始化完成。初始化过程包括连接各个MCP服务器、加载工具列表、配置代理模型等步骤..."
        )
