@echo off
echo Processing S3 PDFs and storing in database...
docker compose exec crypto-agent bash -c "cd /app/src && python -c 'from services.s3_processor import process_s3_pdfs; process_s3_pdfs()'"
echo S3 processing complete!
