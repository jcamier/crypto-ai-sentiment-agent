"""
S3 PDF processor for downloading and processing crypto news PDFs.
"""

import boto3
import json
import logging
from typing import List, Dict, Any
from datetime import datetime
import PyPDF2
import io
from decouple import config
from sqlalchemy.orm import Session
from database import SessionLocal
from models import NewsArticle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Processor:
    """Service for processing PDFs from S3 bucket."""

    def __init__(self):
        """Initialize S3 client and configuration."""
        self.aws_access_key = config("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = config("AWS_SECRET_ACCESS_KEY")
        self.aws_region = config("AWS_DEFAULT_REGION", default="us-east-1")
        self.s3_bucket_name = config("S3_BUCKET_NAME")

        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )

        # Load news sources configuration
        self.news_sources = self._load_news_sources()

    def _load_news_sources(self) -> Dict[str, Any]:
        """Load news sources configuration from JSON file."""
        try:
            with open('/app/news_sources.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("news_sources.json not found")
            return {"articles": []}

    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text content from PDF bytes."""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text = ""

            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _download_pdf_from_s3(self, bucket: str, key: str) -> bytes:
        """Download PDF from S3 bucket."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error downloading PDF from S3: {e}")
            raise

    def _parse_published_date(self, date_str: str) -> datetime:
        """Parse published date string to datetime object."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse date: {date_str}")
            return datetime.now()

    def process_single_article(self, article_config: Dict[str, Any]) -> NewsArticle:
        """Process a single article from S3."""
        try:
            # Download PDF from instructor's bucket
            instructor_bucket = self.news_sources.get("s3_bucket", "crypto-news-pdfs-sep-2025")
            pdf_content = self._download_pdf_from_s3(instructor_bucket, article_config["s3_key"])

            # Extract text content
            content = self._extract_text_from_pdf(pdf_content)

            # Create NewsArticle object
            article = NewsArticle(
                title=article_config["title"],
                content=content,
                source=article_config["source"],
                url=None,  # No URL for PDF articles
                published_at=self._parse_published_date(article_config["published_date"]),
                tokens_mentioned=article_config["tokens"],
                sentiment=None,  # Will be filled by sentiment analysis
                confidence_score=None,
                s3_bucket_source=instructor_bucket,
                s3_key_source=article_config["s3_key"]
            )

            logger.info(f"Processed article: {article_config['title']}")
            return article

        except Exception as e:
            logger.error(f"Error processing article {article_config.get('title', 'Unknown')}: {e}")
            raise

    def process_all_articles(self) -> List[NewsArticle]:
        """Process all articles from the news sources configuration."""
        articles = []

        for article_config in self.news_sources.get("articles", []):
            try:
                article = self.process_single_article(article_config)
                articles.append(article)
            except Exception as e:
                logger.error(f"Failed to process article: {e}")
                continue

        logger.info(f"Successfully processed {len(articles)} articles")
        return articles

    def save_articles_to_db(self, articles: List[NewsArticle]) -> int:
        """Save processed articles to database."""
        db = SessionLocal()
        saved_count = 0

        try:
            for article in articles:
                # Check if article already exists (by title and source)
                existing = db.query(NewsArticle).filter(
                    NewsArticle.title == article.title,
                    NewsArticle.source == article.source
                ).first()

                if not existing:
                    db.add(article)
                    saved_count += 1
                else:
                    logger.info(f"Article already exists: {article.title}")

            db.commit()
            logger.info(f"Saved {saved_count} new articles to database")

        except Exception as e:
            logger.error(f"Error saving articles to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return saved_count


def process_s3_pdfs():
    """Main function to process S3 PDFs and store in database."""
    try:
        processor = S3Processor()

        # Process all articles
        articles = processor.process_all_articles()

        if articles:
            # Save to database
            saved_count = processor.save_articles_to_db(articles)
            logger.info(f"Successfully processed and saved {saved_count} articles")
        else:
            logger.warning("No articles were processed")

    except Exception as e:
        logger.error(f"Error in process_s3_pdfs: {e}")
        raise


if __name__ == "__main__":
    process_s3_pdfs()
