@echo off
echo Running tests...
docker compose exec crypto-agent python -m pytest
echo Tests complete!
