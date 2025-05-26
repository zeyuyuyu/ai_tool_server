import unifai
from config import get_settings

settings = get_settings()
_tools_client = unifai.Tools(api_key=settings.UNIFAI_AGENT_API_KEY)

async def get_tool_funcs(dynamic: bool = True):
    return await _tools_client.get_tools(dynamic_tools=dynamic)

async def call_tool_calls(tool_calls):
    results = await _tools_client.call_tools(tool_calls)
    return results
