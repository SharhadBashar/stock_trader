import asyncio

from pydantic_ai.mcp import MCPToolset

from core.traders.liquid.auth import liquid_client, liquid_oauth
from core.traders.liquid.constants import LIQUID_COINVEST_MCP_URL
from core.traders.liquid.tool_mappings import LIQUID_TOOLS, LiquidToolType


def liquid_tools():
    return MCPToolset(LIQUID_COINVEST_MCP_URL, id = 'liquid_coinvest', auth = liquid_oauth())


def liquid_toolset(tool_type: LiquidToolType | None = None) -> MCPToolset:
    tools = set(LIQUID_TOOLS[tool_type]) if tool_type is not None else set(LIQUID_TOOLS.values())
    return liquid_tools().filtered(
        lambda _, tool: tool.name in tools
    )
