
import os
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class PlaywrightClient:
    """
    Manages the Playwright browser session for Instagram scraping.
    Handles browser lifecycle and authentication state.
    """
    def __init__(self, headless=True, auth_file="instagram_auth.json"):
        self.headless = headless
        self.auth_file = auth_file
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Start the browser session, loading auth state if available."""
        logger.info("Starting Playwright browser...")
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Load auth state if exists
        auth_path = os.path.abspath(self.auth_file)
        if os.path.exists(auth_path):
            logger.info(f"Loading session from {auth_path}")
            self.context = await self.browser.new_context(
                storage_state=auth_path,
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            )
        else:
            logger.warning(f"No auth file found at {auth_path}. Starting anonymous session.")
            self.context = await self.browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                )
            )
            
        self.page = await self.context.new_page()

    async def stop(self):
        """Clean up resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def save_session(self):
        """Save current session state (cookies) to file."""
        if self.context:
            await self.context.storage_state(path=self.auth_file)
            logger.info(f"Session saved to {self.auth_file}")
