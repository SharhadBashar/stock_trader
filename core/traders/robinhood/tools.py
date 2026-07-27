from pydantic_ai.mcp import MCPToolset

from core.traders.robinhood.auth import robinhood_oauth
from core.traders.robinhood.constants import ROBINHOOD_TRADING_MCP_URL
from core.traders.robinhood.tool_mappings import ROBINHOOD_TOOLS, RobinhoodToolType


def robinhood_tools():
    return MCPToolset(ROBINHOOD_TRADING_MCP_URL, id = 'robinhood_trading', auth = robinhood_oauth())


def robinhood_toolset(tool_type: RobinhoodToolType | None = None) -> MCPToolset:
    tools = set(ROBINHOOD_TOOLS[tool_type]) if tool_type is not None else set(ROBINHOOD_TOOLS.values())
    return robinhood_tools().filtered(
        lambda _, tool: tool.name in tools
    )
