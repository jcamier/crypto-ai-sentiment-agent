@echo off
echo Fetching latest crypto news from CoinGecko API...
docker compose exec crypto-agent python -c "from src.services.coingecko_service import fetch_latest_news; fetch_latest_news()"
echo CoinGecko fetch complete!
