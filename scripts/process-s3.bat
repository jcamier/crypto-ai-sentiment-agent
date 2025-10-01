@echo off
echo Processing S3 PDFs and storing in database...
docker compose exec crypto-agent python -c "from src.services.s3_processor import process_s3_pdfs; process_s3_pdfs()"
echo S3 processing complete!
