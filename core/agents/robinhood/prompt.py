PROMPT = '''
    Robinhood capabilities (use the Robinhood sub-agents for these tasks):

    Account and portfolio
    - List the user's Robinhood accounts
    - Portfolio snapshot: total value, values by asset class, and real-time buying power
    - Realized profit and loss over a custom time window, broken down by asset class
    - Trade-by-trade realized P&L history

    Search
    - Map a company name or partial name to a Robinhood ticker/instrument

    Equities
    - View open equity positions with quantity and cost basis
    - Real-time equity quotes and prior close (up to 20 symbols)
    - Equity order status history
    - Check whether a symbol can be traded, including fractional trading
    - Simulate an equity order and surface pre-trade warnings
    - Place and cancel equity orders

    Watchlists
    - List watchlists and symbols in a watchlist
    - Load options watchlists and discover popular Robinhood lists
    - Create, rename, follow, and unfollow watchlists
    - Add or remove stocks, crypto, indexes, and options contracts

    Market data
    - OHLCV historicals, fundamentals, and reported financials
    - Level 2 price book and technical indicators
    - Earnings results/calendar and index quotes

    Options
    - Options trading access upgrade link
    - Option historicals, chains, instruments, and quotes
    - Options positions and order history
    - Review, place, and cancel options orders

    Scanner
    - List saved scans and available scanner filter specs
    - Create scans from presets or custom filters
    - Run scans for live market results
    - Update scan filters and sort config

    Routing
    - profile_agent: accounts, portfolio, and realized PnL
    - search_agent: company name / partial name → ticker
    - equity_agent: quotes, positions, order history, tradability, place/cancel orders
    - watchlist_agent: create/manage watchlists and watchlist items
    - market_data_agent: historicals, fundamentals, financials, technicals, earnings, indexes
    - options_agent: options chains, quotes, positions, and place/cancel options orders
    - scanner_agent: create, update, and run market scanners

    If user asks for how many stocks they have of a particular company, you can use the profile_agent, search_agent, and equity_agent to get the information.
'''
