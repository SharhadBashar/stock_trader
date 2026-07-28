# stock_trader
A platform that will eventually become a bot trader
https://www.youtube.com/watch?v=8IQ8PttfmDU

### Helpful commands
To run locally, use this command: `uv run uvicorn app.main:app --reload`
To start a venv: `source .venv/bin/activate`
If you run into port in use issue:
1. Find what's using port 8000: `lsof -i :8000`
2. Kill the process: `kill -9 <PID>`
3. Kill the process using port 8000 `lsof -ti :8000 | xargs kill -9`


TODO:
1. add agent maping for the subagents and main agents
2. add conversation capabilities

Stock Trader
1. 	update you on your stock prices
	look up directed info on specific stocks/companies

	Basically, what the first version will do is it will take all your stocks and it will give you updated information on the price, especially:
		- what the starting price was at the beginning of the day
		- what the closing price was
		- the current price of the day if it's in the middle of the day
	I'll be building this by using as many web search tools as I can find, such as Perplexity, Firecrall, MCPs, into things like Robinhood, TradingViewer, and as many things as I can find. 
	perplexity search
	pydantic ai websearch
	firecrawl
	mcps into stock trading/news platform

2. 	deep reasearch agent
	news and updates on trends
	suggest what stocks are hot

	perplexity deep search
	mcps into stock trading/news platform

3. strategy builder. pass your own skills

4. phone app for updates like claw bot

5. perform trades


## TODO
1. add tool approval
2. compaction
3. deep research
4. message history
	- agentic message retrival