# Global News → Indian Stock Market (Streamlit)

A one-page Streamlit dashboard that shows up to 10 global news stories likely to matter to Indian markets. It uses Google News RSS and simple transparent keyword rules to rank stories and estimate impact. It is not investment advice and cannot predict market direction reliably.

## Run locally

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python refresh_news.py
streamlit run app.py
```

## Schedule automatic refreshes at 7 AM and 9 PM IST

The GitHub Actions workflow in `.github/workflows/refresh-news.yml` runs at 01:30 UTC and 15:30 UTC, which correspond to 7:00 AM and 9:00 PM India Standard Time.

1. Create a GitHub repository and upload the project files.
2. In the repository, open **Settings → Actions → General** and make sure workflow write permissions are allowed (the workflow declares `contents: write`).
3. Open **Actions**, enable workflows if prompted, then run **Refresh global market news** once using **Run workflow**.
4. The workflow commits the updated `news.json` twice daily. GitHub scheduled workflows may run late and can be disabled for repositories with long periods of inactivity.
5. Deploy the repository on Streamlit Community Cloud, selecting `app.py` as the main file. The site reads the committed `news.json`.

## Important limitations

- This is a useful starter implementation, not a financial-news terminal. RSS headlines/descriptions can be incomplete, and Google News links may redirect.
- The impact label is based on simple keyword matching. "Positive" or "Negative" means a rough possible effect on Indian market sentiment, not a forecast that Nifty/Sensex will rise or fall.
- Review original articles and consider domestic data, RBI decisions, earnings, valuations and market prices before making financial decisions.
- The news list is updated on schedule, not necessarily exactly at the scheduled minute. Use the manual refresh workflow or run `python refresh_news.py` to update it immediately.
