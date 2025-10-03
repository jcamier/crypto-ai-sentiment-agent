@echo off
echo Fetching latest crypto news from CoinGecko API...
docker compose exec crypto-agent bash -c "cd /app/src && python -c 'from services.coingecko_service import fetch_latest_news; fetch_latest_news()'"
echo CoinGecko fetch complete!
