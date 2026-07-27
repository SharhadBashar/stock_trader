from enum import Enum


class LiquidToolType(Enum):
    RESEARCH = 'research'
    PORTFOLIO = 'portfolio'
    TRADING = 'trading'
    CHARTS = 'charts'
    PLATFORM = 'platform'
    INTERNAL = 'internal'


LIQUID_TOOLS = {
    LiquidToolType.RESEARCH: [
        'analyze_market',
        'analyze_markets_batch',
        'get_technical_indicators',
        'search_markets',
        'get_news',
        'market_picks',
        'get_positioning_pulse',
        'search_prediction_markets',
    ],
    LiquidToolType.PORTFOLIO: [
        'get_portfolio',
        'get_transaction_history',
        'view_prediction_positions',
        'view_open_orders',
        'view_prediction_orders',
        'show_deposit',
        'convert_balances',
        'plan_portfolio',
    ],
    LiquidToolType.TRADING: [
        'suggest_trade',
        'suggest_trades_batch',
        'modify_position',
        'update_leverage',
        'close_positions_batch',
        'cancel_order',
        'execute_prediction_order',
        'close_prediction_position',
        'cancel_prediction_order',
        'enable_trading',
    ],
    LiquidToolType.CHARTS: [
        'show_chart',
        'show_orderbook',
        'show_prediction_orderbook',
        'show_market_overview',
        'show_portfolio_chart',
    ],
    LiquidToolType.PLATFORM: [
        'enable_paper_trading',
        'disable_paper_trading',
        'reset_paper_account',
        'paper_trading_status',
        'edit_watchlist',
        'refer',
        'help',
    ],
    LiquidToolType.INTERNAL: [
        'execute_order',
        'execute_orders_batch',
        'execute_tpsl',
        'close_position',
        'generate_deposit_address',
        'create_onramp_session',
        '_convert_pending_status',
    ],
}
