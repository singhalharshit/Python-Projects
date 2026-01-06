
from typing import List, Set
import logging
from .hashtag_scraper import HashtagScraper
from .playwright_client import PlaywrightClient
from app.services.scrapers.hybrid_instagram_scraper import get_hybrid_instagram_scraper

logger = logging.getLogger(__name__)

class PlaywrightCandidateGenerator:
    """
    Generates candidates using Playwright-based scraping.
    Replaces the previous API/Instaloader hashtag path.
    """
    def __init__(self, client: PlaywrightClient):
        self.client = client
        self.hashtag_scraper = HashtagScraper(client)
        
    async def generate(self, hashtags: List[str], limit_per_tag: int = 30) -> List[str]:
        """
        Generate candidates from a list of hashtags.
        """
        all_creators: Set[str] = set()
        
        # Ensure browser is running
        if not self.client.page:
            await self.client.start()

        for tag in hashtags:
            try:
                logger.info(f"Scraping #{tag}...")
                creators = await self.hashtag_scraper.scrape_creators(
                    tag, limit=limit_per_tag
                )
                logger.info(f"Found {len(creators)} creators for #{tag}")
                all_creators.update(creators)
            except Exception as e:
                logger.error(f"Failed to scrape #{tag}: {e}")
                continue

        return list(all_creators)
