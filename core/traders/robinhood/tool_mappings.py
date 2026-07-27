from enum import Enum

class RobinhoodToolType(Enum):
    ACCOUNT = 'account'
    SEARCH = 'search'
    EQUITIES = 'equities'

ROBINHOOD_TOOLS = {
    RobinhoodToolType.ACCOUNT: [
        'get_accounts',
        'get_portfolio',
        'get_realized_pnl',
        'get_pnl_trade_history'
    ],
    RobinhoodToolType.SEARCH: ['search'],
    RobinhoodToolType.EQUITIES: [
        'get_equity_positions',
        'get_equity_quotes',
        'get_equity_orders',
        'get_equity_tradability',
        'review_equity_order',
        'place_equity_order',
        'cancel_equity_order'
    ],
}
