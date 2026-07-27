from pathlib import Path

ROBINHOOD_TRADING_MCP_URL = 'https://agent.robinhood.com/mcp/trading'
TOKEN_CACHE_DIR = Path.home() / '.stock_trader' / 'mcp_tokens'
CALLBACK_PORT = 44553
CALLBACK_HOST = '127.0.0.1'
