@echo off
echo Cleaning up containers and volumes...
docker compose down -v
docker system prune -f
echo Cleanup complete!
