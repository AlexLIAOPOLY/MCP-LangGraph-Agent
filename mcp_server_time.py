from mcp.server.fastmcp import FastMCP
from datetime import datetime
import os
import pytz
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 服务器配置从环境变量获取，提供默认值
MCP_HOST = os.getenv("MCP_TIME_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_TIME_PORT", "8005"))

# Initialize FastMCP server with configuration
mcp = FastMCP(
    "TimeService",  # Name of the MCP server
    instructions="你是一个时间助手，可以提供不同时区的当前时间，默认为中国标准时间 (Asia/Shanghai)。",  # Instructions for the LLM on how to use this tool
    host=MCP_HOST,  # Host address from environment variable
    port=MCP_PORT,  # Port number from environment variable
)


@mcp.tool()
async def get_current_time(timezone: Optional[str] = "Asia/Shanghai") -> str:
    """
    Get current time information for the specified timezone.

    This function returns the current system time for the requested timezone.

    Args:
        timezone (str, optional): The timezone to get current time for. Defaults to "Asia/Shanghai" (China Standard Time).

    Returns:
        str: A string containing the current time information for the specified timezone
    """
    try:
        # 支持中文时区别名
        timezone_mapping = {
            "中国": "Asia/Shanghai",
            "北京": "Asia/Shanghai", 
            "上海": "Asia/Shanghai",
            "China": "Asia/Shanghai",
            "Beijing": "Asia/Shanghai",
            "CST": "Asia/Shanghai"
        }
        
        # 如果是别名，转换为标准时区名
        actual_timezone = timezone_mapping.get(timezone, timezone)
        
        # Get the timezone object
        tz = pytz.timezone(actual_timezone)

        # Get current time in the specified timezone
        current_time = datetime.now(tz)

        # Format the time as a string
        formatted_time = current_time.strftime("%Y年%m月%d日 %H:%M:%S %Z")

        return f"{timezone} 的当前时间是: {formatted_time}"
    except pytz.exceptions.UnknownTimeZoneError:
        return f"错误: 未知的时区 '{timezone}'。请提供有效的时区名称。"
    except Exception as e:
        return f"获取时间时出错: {str(e)}"


if __name__ == "__main__":
    # Start the MCP server with stdio transport
    # stdio transport allows the server to communicate with clients
    # through standard input/output streams, making it suitable for
    # local development and testing
    mcp.run(transport="stdio")
