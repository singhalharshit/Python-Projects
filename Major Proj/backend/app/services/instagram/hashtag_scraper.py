
import asyncio
import logging
from typing import Set
from .playwright_client import PlaywrightClient

logger = logging.getLogger(__name__)

class HashtagScraper:
    """
    Scrapes Instagram creators from hashtag pages using Playwright.
    """
    def __init__(self, client: PlaywrightClient):
        self.client = client

    async def scrape_creators(self, hashtag: str, limit: int = 50) -> Set[str]:
        """
        Scrape unique usernames from a hashtag page.
        """
        if not self.client.page:
            logger.error("Playwright client not ready. Call start() first.")
            return set()

        url = f"https://www.instagram.com/explore/tags/{hashtag}/"
        logger.info(f"Navigating to {url}")
        
        try:
            await self.client.page.goto(url, timeout=60000)
            
            # Wait for content to load
            # Instagram loads 'article' tags for posts
            try:
                await self.client.page.wait_for_selector("article", timeout=10000)
            except Exception:
                logger.warning(f"Timeout waiting for content on #{hashtag} (might be login wall)")
                # If we hit login wall, we might still see some content if public, but likely not.
                # Check for login redirect logic here if needed.
            
            # Allow some dynamic loading
            await asyncio.sleep(4)

            creators = set()
            
            # Strategy: Find all links that look like profile links
            # Valid profile links: /username/ (not /p/, /explore/, etc.)
            
            # We can also click posts to get exact authors, but that's slower.
            # Faster method: Look for hrefs in the grid? 
            # Actually, grid items link to POSTS (/p/code), not AUTHORS usually.
            # To get authors, we usually need to open the post or hover.
            
            # The User's provided code suggests: 
            # post.click() -> get author from modal.
            # This is robust but slow.
            
            # Initial simple approach (User's snippet was slightly simpler, just parsing hrefs? 
            # "href... parts == 1" -> this implies finding profile links directly on the page.
            # On hashtag page, usually only POST links exist.
            
            # Let's try the click method for accuracy, as grid usually doesn't show author name text.
            
            posts = await self.client.page.query_selector_all("article a")
            logger.info(f"Found {len(posts)} posts for #{hashtag}")
            
            for i, post in enumerate(posts[:limit]):
                try:
                    # Click to open modal
                    # We need to be careful about not navigating AWAY from the page
                    # Instagram opens posts in modal usually if window is wide enough.
                    
                    # Force new tab? No, keep it simple.
                    
                    # NOTE: Clicking might navigate away if not logged in or in mobile view.
                    # Safest for headless: Extract post shortcode, then go to post URL directly?
                    # Or just try scraping hrefs if any exist.
                    
                    # Let's trust the user's intent: "Simulate real human".
                    # But iterating clicks is slow.
                    
                    # Alternative: Get post URLs, then visit them individually?
                    href = await post.get_attribute("href")
                    if href and "/p/" in href:
                        # It's a post.
                        # We could visit it.
                        pass
                except Exception:
                    continue

            # REVISION: To avoid complex interactions that might break,
            # let's try to extract ANY text that looks like a username if possible, 
            # OR just visit the first few posts.
            
            # Actually, let's implement the user's "click" logic but safer.
            # "click(), wait for header a, extract text, press escape"
            
            for post in posts[:limit]:
                try:
                    await post.click()
                    # Wait for modal header
                    # Header usually contains the username link
                    await self.client.page.wait_for_selector("header a", timeout=3000)
                    
                    author_link = await self.client.page.query_selector("header a")
                    if author_link:
                        username = await author_link.inner_text()
                        if username:
                            creators.add(username.strip())
                            # logger.info(f"Found creator: {username}")
                    
                    # Close modal
                    await self.client.page.keyboard.press("Escape")
                    await asyncio.sleep(0.5 + (0.1 * len(creators))) # Randomish delay
                    
                    if len(creators) >= limit:
                        break
                        
                except Exception as e:
                    # If click failed or modal didn't appear
                    # Try to recover by going back if url changed
                    if self.client.page.url != url:
                        await self.client.page.go_back()
                    pass

            return creators
            
        except Exception as e:
            logger.error(f"Error scraping #{hashtag}: {e}")
            return set()
