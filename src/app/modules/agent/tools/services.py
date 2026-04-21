from langchain_core.tools import tool

@tool(description="这是一个获取天气的工具。输入是一个城市名称，输出是该城市的天气信息。")
def get_weather(city: str) -> str:
    """
    这是一个获取天气的工具。输入是一个城市名称，输出是该城市的天气信息。
    :param city: 城市名称
    :return: 该城市的天气信息
    """
    return f"{city}的天气是晴朗，温度25摄氏度。"
@tool(description="这是一个获取用户位置信息的工具。输入为空，输出是用户的位置信息。")
def get_user_location() -> str:
    """
    这是一个获取用户位置信息的工具。输入为空，输出是用户的位置信息。
    :return: 用户的位置信息
    """
    return "北京"