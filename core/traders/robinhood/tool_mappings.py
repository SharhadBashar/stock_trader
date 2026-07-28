from enum import Enum

class RobinhoodToolType(Enum):
    ACCOUNT = 'account'
    SEARCH = 'search'
    EQUITIES = 'equities'
    WATCHLIST = 'watchlist'
    MARKET_DATA = 'market_data'
    OPTIONS = 'options'
    SCANNER = 'scanner'

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
    RobinhoodToolType.WATCHLIST: [
        'get_watchlists',
        'get_watchlist_items',
        'get_option_watchlist',
        'get_popular_watchlists',
        'create_watchlist',
        'update_watchlist',
        'follow_watchlist',
        'unfollow_watchlist',
        'add_to_watchlist',
        'remove_from_watchlist',
        'add_option_to_watchlist',
        'remove_option_from_watchlist',
    ],
    RobinhoodToolType.MARKET_DATA: [
        'get_equity_historicals',
        'get_equity_fundamentals',
        'get_financials',
        'get_equity_price_book',
        'get_equity_technical_indicators',
        'get_earnings_results',
        'get_earnings_calendar',
        'get_indexes',
        'get_index_quotes',
    ],
    RobinhoodToolType.OPTIONS: [
        'get_option_level_upgrade_info',
        'get_option_historicals',
        'get_option_chains',
        'get_option_instruments',
        'get_option_quotes',
        'get_option_positions',
        'get_option_orders',
        'review_option_order',
        'cancel_option_order',
        'place_option_order',
    ],
    RobinhoodToolType.SCANNER: [
        'get_scans',
        'get_scanner_filter_specs',
        'create_scan',
        'run_scan',
        'update_scan_filters',
        'update_scan_config',
    ],
}
