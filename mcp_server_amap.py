from mcp.server.fastmcp import FastMCP
import json
import os
from typing import Optional
import urllib3
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 从环境变量获取配置
AMAP_API_KEY = os.getenv("AMAP_API_KEY")
if not AMAP_API_KEY:
    raise ValueError("AMAP_API_KEY 环境变量未设置。请在 .env 文件中添加您的高德地图API密钥。")

# 服务器配置从环境变量获取，提供默认值
MCP_HOST = os.getenv("MCP_AMAP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_AMAP_PORT", "8006"))

# 高德地图API配置
AMAP_BASE_URL = os.getenv("AMAP_BASE_URL", "https://restapi.amap.com/v3")

# API端点配置
API_ENDPOINTS = {
    "geocoding": f"{AMAP_BASE_URL}/geocode/geo",
    "reverse_geocoding": f"{AMAP_BASE_URL}/geocode/regeo", 
    "poi_search": f"{AMAP_BASE_URL}/place/text",
    "weather": f"{AMAP_BASE_URL}/weather/weatherInfo",
    "route_planning": f"{AMAP_BASE_URL}/direction/driving",
    "distance": f"{AMAP_BASE_URL}/distance"
}

# Initialize FastMCP server with configuration
mcp = FastMCP(
    "AmapService",
    instructions="你是一个高德地图助手，可以提供地理编码、逆地理编码、POI搜索、路径规划、天气查询等功能。",
    host=MCP_HOST,
    port=MCP_PORT,
)

# 通用请求函数
def make_request(url, params):
    """统一的HTTP请求函数"""
    import requests
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        
        # 直接尝试HTTP连接（跳过HTTPS问题）
        http_url = url.replace('https://', 'http://')
        
        response = requests.get(
            http_url,
            params=params,
            headers=headers,
            timeout=10,
            allow_redirects=True
        )
        
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "0", "info": f"HTTP错误: {response.status_code}, 响应: {response.text[:200]}"}
            
    except Exception as e:
        return {"status": "0", "info": f"请求失败: {str(e)}"}


@mcp.tool()
def geocoding(address: str, city: Optional[str] = None) -> str:
    """
    地理编码 - 将地址转换为经纬度坐标
    
    Args:
        address (str): 要查询的地址
        city (str, optional): 指定查询的城市，提高查询精度
    
    Returns:
        str: 包含经纬度坐标和详细地址信息的JSON字符串
    """
    url = API_ENDPOINTS["geocoding"]
    params = {
        "key": AMAP_API_KEY,
        "address": address,
        "output": "json"
    }
    if city:
        params["city"] = city
        
    data = make_request(url, params)
    
    if data["status"] == "1" and data.get("geocodes"):
        result = data["geocodes"][0]
        return json.dumps({
            "status": "success",
            "location": result["location"],
            "formatted_address": result["formatted_address"],
            "province": result["province"],
            "city": result["city"],
            "district": result["district"],
            "level": result["level"]
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "message": f"地理编码查询失败: {data.get('info', '未知错误')}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def reverse_geocoding(longitude: float, latitude: float, radius: Optional[int] = 1000) -> str:
    """
    逆地理编码 - 将经纬度坐标转换为地址信息
    
    Args:
        longitude (float): 经度
        latitude (float): 纬度
        radius (int, optional): 搜索半径，单位米，默认1000米
    
    Returns:
        str: 包含地址信息的JSON字符串
    """
    url = API_ENDPOINTS["reverse_geocoding"]
    params = {
        "key": AMAP_API_KEY,
        "location": f"{longitude},{latitude}",
        "output": "json",
        "radius": radius,
        "extensions": "all"
    }
    
    data = make_request(url, params)
    
    if data["status"] == "1":
        regeocode = data["regeocode"]
        return json.dumps({
            "status": "success",
            "formatted_address": regeocode["formatted_address"],
            "addressComponent": regeocode["addressComponent"],
            "pois": regeocode.get("pois", [])[:5]
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "message": f"逆地理编码查询失败: {data.get('info', '未知错误')}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def poi_search(keywords: str, city: Optional[str] = None, types: Optional[str] = None, page: Optional[int] = 1) -> str:
    """
    POI搜索 - 搜索兴趣点信息
    
    Args:
        keywords (str): 搜索关键词
        city (str, optional): 搜索城市
        types (str, optional): POI类型，如"餐饮服务|购物服务"
        page (int, optional): 页码，默认第1页
    
    Returns:
        str: 包含POI搜索结果的JSON字符串
    """
    url = API_ENDPOINTS["poi_search"]
    params = {
        "key": AMAP_API_KEY,
        "keywords": keywords,
        "output": "json",
        "page": page,
        "offset": 10
    }
    
    if city:
        params["city"] = city
    if types:
        params["types"] = types
        
    data = make_request(url, params)
    
    if data["status"] == "1":
        pois = []
        for poi in data["pois"]:
            pois.append({
                "name": poi["name"],
                "type": poi["type"],
                "address": poi["address"],
                "location": poi["location"],
                "tel": poi.get("tel", ""),
                "distance": poi.get("distance", ""),
                "business_area": poi.get("business_area", "")
            })
        
        return json.dumps({
            "status": "success",
            "count": data["count"],
            "pois": pois
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "message": f"POI搜索失败: {data.get('info', '未知错误')}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def weather_query(city: str = "北京市", extensions: Optional[str] = "base") -> str:
    """
    天气查询 - 获取指定城市的天气信息
    
    Args:
        city (str): 城市名称，如"北京市"、"上海市"等，默认"北京市"
        extensions (str, optional): 气象类型，base-实况天气，all-预报天气，默认base
    
    Returns:
        str: 包含天气信息的JSON字符串
    """
    # 如果没有提供完整城市名，尝试补全
    if city and not city.endswith("市") and not city.endswith("区") and not city.endswith("县"):
        city = city + "市"
        
    url = API_ENDPOINTS["weather"]
    params = {
        "key": AMAP_API_KEY,
        "city": city,
        "extensions": extensions,
        "output": "json"
    }
    
    data = make_request(url, params)
    
    if data["status"] == "1":
        if extensions == "base":
            live = data["lives"][0]
            return json.dumps({
                "status": "success",
                "city": live["city"],
                "weather": live["weather"],
                "temperature": live["temperature"],
                "winddirection": live["winddirection"],
                "windpower": live["windpower"],
                "humidity": live["humidity"],
                "reporttime": live["reporttime"]
            }, ensure_ascii=False, indent=2)
        else:
            forecast = data["forecasts"][0]
            return json.dumps({
                "status": "success",
                "city": forecast["city"],
                "reporttime": forecast["reporttime"],
                "casts": [
                    {
                        "date": cast["date"],
                        "week": cast["week"],
                        "dayweather": cast["dayweather"],
                        "nightweather": cast["nightweather"],
                        "daytemp": cast["daytemp"],
                        "nighttemp": cast["nighttemp"],
                        "daywind": cast["daywind"],
                        "nightwind": cast["nightwind"],
                        "daypower": cast["daypower"],
                        "nightpower": cast["nightpower"]
                    } for cast in forecast["casts"]
                ]
            }, ensure_ascii=False, indent=2)
    else:
        error_info = data.get('info', '未知错误')
        if "502" in error_info or "Empty reply" in error_info:
            return json.dumps({
                "status": "error", 
                "message": f"目前无法获取{city}的天气信息，可能是由于网络或服务暂不可用。建议稍后再试或通过其他天气查询工具获取最新信息。",
                "technical_info": f"API错误: {error_info}"
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "message": f"天气查询失败: {error_info}，请检查城市名称是否正确"
            }, ensure_ascii=False, indent=2)


@mcp.tool()
def route_planning(origin: str, destination: str, strategy: Optional[int] = 10, waypoints: Optional[str] = None) -> str:
    """
    路径规划 - 驾车路径规划
    
    Args:
        origin (str): 起点坐标，格式：经度,纬度
        destination (str): 终点坐标，格式：经度,纬度
        strategy (int, optional): 路径规划策略，默认10（不走高速+费用最少+距离最短）
        waypoints (str, optional): 途经点，格式：经度,纬度;经度,纬度
    
    Returns:
        str: 包含路径规划结果的JSON字符串
    """
    url = API_ENDPOINTS["route_planning"]
    params = {
        "key": AMAP_API_KEY,
        "origin": origin,
        "destination": destination,
        "strategy": strategy,
        "output": "json",
        "extensions": "all"
    }
    
    if waypoints:
        params["waypoints"] = waypoints
        
    data = make_request(url, params)
    
    if data["status"] == "1" and data["route"]["paths"]:
        path = data["route"]["paths"][0]
        return json.dumps({
            "status": "success",
            "distance": path["distance"],
            "duration": path["duration"],
            "tolls": path["tolls"],
            "toll_distance": path["toll_distance"],
            "restriction": path["restriction"],
            "steps_count": len(path["steps"]),
            "steps": [
                {
                    "instruction": step["instruction"],
                    "distance": step["distance"],
                    "duration": step["duration"],
                    "road": step.get("road", "")
                } for step in path["steps"][:5]
            ]
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "message": f"路径规划失败: {data.get('info', '未知错误')}"
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def distance_calculation(origins: str, destinations: str, type_distance: Optional[int] = 1) -> str:
    """
    距离测量 - 计算两点间的距离和时间
    
    Args:
        origins (str): 起点坐标，格式：经度,纬度|经度,纬度
        destinations (str): 终点坐标，格式：经度,纬度|经度,纬度
        type_distance (int, optional): 路径计算方式，1-直线距离，3-驾车导航距离，默认1
    
    Returns:
        str: 包含距离和时间信息的JSON字符串
    """
    url = API_ENDPOINTS["distance"]
    params = {
        "key": AMAP_API_KEY,
        "origins": origins,
        "destination": destinations,
        "type": type_distance,
        "output": "json"
    }
    
    data = make_request(url, params)
    
    if data["status"] == "1":
        results = []
        for result in data["results"]:
            results.append({
                "origin_id": result.get("origin_id", ""),
                "dest_id": result.get("dest_id", ""),
                "distance": result["distance"],
                "duration": result.get("duration", ""),
                "info": result.get("info", "")
            })
        
        return json.dumps({
            "status": "success",
            "results": results
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "status": "error",
            "message": f"距离计算失败: {data.get('info', '未知错误')}"
        }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    mcp.run(transport="stdio")