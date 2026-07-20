from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from mcp.client.stdio import get_default_environment
from pydantic_ai.mcp import MCPToolset

from core.perplexity.constants import PERPLEXITY_MCP_ARGS, PERPLEXITY_MCP_COMMAND
from core.perplexity.tool_mappings import PERPLEXITY_TOOLS, PerplexityToolType
from settings import PERPLEXITY_API_KEY


def perplexity_tools() -> MCPToolset:
    if not PERPLEXITY_API_KEY:
        raise ValueError('PERPLEXITY_API_KEY is not set')

    env = {**get_default_environment(), 'PERPLEXITY_API_KEY': PERPLEXITY_API_KEY}
    transport = StdioTransport(
        command = PERPLEXITY_MCP_COMMAND,
        args = PERPLEXITY_MCP_ARGS,
        env = env,
    )
    return MCPToolset(Client(transport), id = 'perplexity')


def perplexity_toolset(tool_type: PerplexityToolType | None = None) -> MCPToolset:
    toolset = perplexity_tools()
    if tool_type is None:
        tool_type = PerplexityToolType.ALL
    tools = set(PERPLEXITY_TOOLS[tool_type])
    return toolset.filtered(lambda _, tool: tool.name in tools)
