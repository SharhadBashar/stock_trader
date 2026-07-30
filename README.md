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

### Environment variables
Copy `.env.example` to `.env` and fill in every value. All variables are required at startup (`validate_environment()` raises on anything missing). This includes the Postgres connection (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB`) and `GOOGLE_APPLICATION_CREDENTIALS` for Firebase.

### Auth (Firebase)
Signup/signin happens on the frontend with the Firebase Web SDK. The frontend sends the Firebase ID token on every request as `Authorization: Bearer <token>`. This backend verifies the token with `firebase-admin` and provisions/updates a row in the local `users` table on the fly (`core/auth/`). Firebase stores all credentials — the backend never sees passwords.

One-time setup:
1. Create a Firebase project at https://console.firebase.google.com and enable your sign-in providers (Authentication -> Sign-in method), e.g. Email/Password, Google, Phone.
2. Generate a service account key: Project settings -> Service accounts -> Generate new private key.
3. Save the JSON somewhere outside the repo (or gitignored) and point `GOOGLE_APPLICATION_CREDENTIALS` in `.env` at it.

Protected routes take `Depends(get_current_user)` from `core.auth`. Missing/invalid tokens get a 401, archived users (`users.archived_at` set) get a 403.

### Database migrations
Alembic is wired to the models in `db/models/` and reads the DB URL from `.env` (same `DB_*` variables as the app).
- Apply migrations: `uv run alembic upgrade head`
- Roll back one: `uv run alembic downgrade -1`
- New migration after model changes: `uv run alembic revision --autogenerate -m 'describe change'`


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