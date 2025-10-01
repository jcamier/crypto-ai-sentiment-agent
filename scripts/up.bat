@echo off
echo Starting all services...
docker compose down
docker compose up -d
echo Services started! Use 'scripts\logs.bat' to view logs.
