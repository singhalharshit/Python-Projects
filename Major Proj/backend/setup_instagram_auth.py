
import asyncio
import os
import sys

# Add parent directory to path to allow imports if needed
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright

AUTH_FILE = "instagram_auth.json"

async def setup_auth():
    print("=" * 60)
    print("INSTAGRAM AUTHENTICATION SETUP")
    print("=" * 60)
    print("This script will open a browser window.")
    print("1. Log in to Instagram manually.")
    print("2. Handle any 2-factor authentication.")
    print("3. When you are fully logged in and on the home feed, come back here.")
    print("4. Press ENTER in this terminal to save your session.")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch non-headless browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("\nOpening Instagram...")
        await page.goto("https://www.instagram.com/")
        
        # Wait for user input
        input("\n>>> PRESS ENTER HERE WHEN YOU ARE LOGGED IN <<<")
        
        # Save storage state
        await context.storage_state(path=AUTH_FILE)
        print(f"\n✅ Session saved to {os.path.abspath(AUTH_FILE)}")
        print("You can now close the browser.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(setup_auth())
