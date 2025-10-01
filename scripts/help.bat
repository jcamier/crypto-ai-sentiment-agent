@echo off
echo Crypto News & Sentiment Agent - Windows Commands
echo ================================================
echo.
echo Available commands:
echo   scripts\up.bat           - Start all services with docker compose
echo   scripts\down.bat         - Stop all services
echo   scripts\build.bat        - Build all Docker images
echo   scripts\setup.bat        - Complete project setup (database + pgvector)
echo   scripts\test.bat         - Run tests
echo   scripts\clean.bat        - Clean up containers and volumes
echo   scripts\logs.bat         - Show logs from all services
echo   scripts\logs-app.bat     - Show logs from crypto-agent service only
echo   scripts\shell.bat        - Shell into crypto-agent container
echo   scripts\process-s3.bat   - Process S3 PDFs and store in database
echo   scripts\fetch-coingecko.bat - Fetch latest crypto news from CoinGecko API
echo   scripts\test-api.bat     - Test API endpoints
echo   scripts\help.bat         - Show this help message
echo.
echo For Linux/Mac users, use the Makefile instead:
echo   make up, make down, make build, etc.
echo.
echo Prerequisites:
echo   - Docker Desktop installed and running
echo   - .env file configured with your AWS credentials
echo.
