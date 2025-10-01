@echo off
echo Testing API endpoints...
echo.
echo Health check:
curl -s http://localhost:8000/health | python -m json.tool
echo.
echo News articles:
curl -s http://localhost:8000/api/news/ | python -m json.tool
echo.
echo Sentiment analysis:
curl -s http://localhost:8000/api/sentiment/ | python -m json.tool
echo.
echo API testing complete!
