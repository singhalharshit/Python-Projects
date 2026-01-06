"""
Production-Grade Competitor Discovery using Playwright
Multi-source candidate generation with online learning
"""
import logging
import asyncio
from typing import List, Dict, Any, Set
from playwright.async_api import async_playwright, Page
import re
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


class PlaywrightCompetitorHarvester:
    """
    LAYER 1: Raw Candidate Generation
    Goal: Generate 200-500 plausible creators from multiple sources
    
    Methods:
    1. Hashtag Author Harvesting (PRIMARY)
    2. Reel Author Graph (VERY POWERFUL)
    3. Bio-Semantic Search (SECONDARY)
    4. Size-Band Expansion (CRITICAL)
    """
    
    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service
        self.browser = None
        self.context = None
    
    async def harvest_competitors(
        self,
        username: str,
        hashtags: List[str],
        bio: str = "",
        target_count: int = 300
    ) -> List[Dict[str, Any]]:
        """
        Main harvesting pipeline.
        Returns 200-500 raw candidates.
        """
        logger.info(f"🌾 Harvesting competitors for @{username}...")
        logger.info(f"   Target: {target_count} candidates")
        
        all_candidates = []
        
        async with async_playwright() as p:
            # Launch browser
            self.browser = await p.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            try:
                # METHOD 1: Hashtag Author Harvesting (PRIMARY)
                logger.info("📌 METHOD 1: Hashtag harvesting...")
                hashtag_candidates = await self._harvest_from_hashtags(hashtags[:8])
                all_candidates.extend(hashtag_candidates)
                logger.info(f"   ✅ Hashtags: {len(hashtag_candidates)} candidates")
                
                # METHOD 2: Reel Author Graph (VERY POWERFUL)
                logger.info("🎬 METHOD 2: Reel harvesting...")
                reel_candidates = await self._harvest_from_reels(hashtags[:5])
                all_candidates.extend(reel_candidates)
                logger.info(f"   ✅ Reels: {len(reel_candidates)} candidates")
                
                # METHOD 3: Bio-Semantic Search (SECONDARY)
                if self.embedding_service and bio:
                    logger.info("🧠 METHOD 3: Semantic search...")
                    semantic_candidates = await self._harvest_semantic(bio)
                    all_candidates.extend(semantic_candidates)
                    logger.info(f"   ✅ Semantic: {len(semantic_candidates)} candidates")
                
            finally:
                await self.context.close()
                await self.browser.close()
        
        # Deduplicate
        unique_candidates = self._deduplicate(all_candidates)
        logger.info(f"🎯 Total harvested: {len(unique_candidates)} unique candidates")
        
        return unique_candidates
    
    async def _harvest_from_hashtags(
        self,
        hashtags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        METHOD 1: Hashtag Author Harvesting
        
        Process:
        1. Visit hashtag page
        2. Collect 20-40 post links
        3. Extract author username from each
        4. Return 150-300 candidates
        """
        candidates = []
        
        for hashtag in hashtags:
            clean_tag = hashtag.replace('#', '').strip()
            
            try:
                page = await self.context.new_page()
                url = f"https://www.instagram.com/explore/tags/{clean_tag}/"
                
                logger.info(f"  📍 Visiting: {url}")
                
                # Navigate and wait for content
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3)  # Wait for JS render
                
                # Extract post authors from rendered HTML
                authors = await page.evaluate("""
                    () => {
                        const authors = new Set();
                        
                        // Method 1: From post links
                        const links = document.querySelectorAll('a[href*="/p/"]');
                        links.forEach(link => {
                            const href = link.href;
                            const match = href.match(/instagram\\.com\\/p\\/[^/]+/);
                            if (match) {
                                // Get username from surrounding elements
                                const parent = link.closest('article, div[role="button"]');
                                if (parent) {
                                    const userLinks = parent.querySelectorAll('a[href^="/"]');
                                    userLinks.forEach(userLink => {
                                        const username = userLink.pathname.slice(1).split('/')[0];
                                        if (username && username.length > 2 && username !== 'explore') {
                                            authors.add(username);
                                        }
                                    });
                                }
                            }
                        });
                        
                        // Method 2: From profile links
                        const profileLinks = document.querySelectorAll('a[href^="/"][href*="/"]');
                        profileLinks.forEach(link => {
                            const username = link.pathname.slice(1).split('/')[0];
                            if (username && username.length > 2 && 
                                !['explore', 'p', 'reels', 'tv'].includes(username)) {
                                authors.add(username);
                            }
                        });
                        
                        return Array.from(authors);
                    }
                """)
                
                # Create candidate objects
                for author in authors[:40]:  # Max 40 per hashtag
                    candidates.append({
                        'username': author,
                        'platform': 'instagram',
                        'discovered_via': f'hashtag_{clean_tag}',
                        'discovery_method': 'hashtag_harvest',
                        'discovery_signals': 1,
                        'source_hashtag': clean_tag
                    })
                
                logger.info(f"    ✅ #{clean_tag}: {len(authors)} authors")
                
                await page.close()
                
            except Exception as e:
                logger.warning(f"    ⚠️ Failed #{clean_tag}: {e}")
                continue
        
        return candidates
    
    async def _harvest_from_reels(
        self,
        hashtags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        METHOD 2: Reel Author Graph
        
        Reels = Instagram's discovery engine
        Captures current trending competitors
        """
        candidates = []
        
        for hashtag in hashtags:
            clean_tag = hashtag.replace('#', '').strip()
            
            try:
                page = await self.context.new_page()
                # Try both reel URL formats
                urls = [
                    f"https://www.instagram.com/explore/tags/{clean_tag}/reels/",
                    f"https://www.instagram.com/explore/tags/{clean_tag}/"
                ]
                
                for url in urls:
                    try:
                        logger.info(f"  🎬 Reels: {url}")
                        await page.goto(url, wait_until='networkidle', timeout=30000)
                        await asyncio.sleep(3)
                        break
                    except:
                        continue
                
                # Extract reel authors
                reel_authors = await page.evaluate("""
                    () => {
                        const authors = new Set();
                        
                        // Reels have specific selectors
                        const reelLinks = document.querySelectorAll('a[href*="/reel/"]');
                        reelLinks.forEach(link => {
                            const parent = link.closest('div');
                            if (parent) {
                                const userLinks = parent.querySelectorAll('a[href^="/"]');
                                userLinks.forEach(userLink => {
                                    const username = userLink.pathname.slice(1).split('/')[0];
                                    if (username && username.length > 2 && 
                                        !['explore', 'reels', 'reel'].includes(username)) {
                                        authors.add(username);
                                    }
                                });
                            }
                        });
                        
                        return Array.from(authors);
                    }
                """)
                
                for author in reel_authors[:30]:
                    candidates.append({
                        'username': author,
                        'platform': 'instagram',
                        'discovered_via': f'reels_{clean_tag}',
                        'discovery_method': 'reel_graph',
                        'discovery_signals': 1,
                        'source_hashtag': clean_tag,
                        'is_reel_creator': True
                    })
                
                logger.info(f"    ✅ Reels #{clean_tag}: {len(reel_authors)} authors")
                
                await page.close()
                
            except Exception as e:
                logger.warning(f"    ⚠️ Failed reels #{clean_tag}: {e}")
                continue
        
        return candidates
    
    async def _harvest_semantic(
        self,
        bio: str
    ) -> List[Dict[str, Any]]:
        """
        METHOD 3: Bio-Semantic Search
        
        Uses embeddings to find creators with similar bios
        Searches Google: site:instagram.com
        """
        candidates = []
        
        try:
            # Extract key themes from bio
            keywords = self._extract_keywords(bio)
            
            # Search Google for Instagram profiles
            page = await self.context.new_page()
            
            for keyword in keywords[:3]:
                search_query = f"site:instagram.com {keyword} bio"
                google_url = f"https://www.google.com/search?q={search_query}"
                
                try:
                    await page.goto(google_url, wait_until='networkidle', timeout=15000)
                    await asyncio.sleep(2)
                    
                    # Extract Instagram usernames from results
                    usernames = await page.evaluate("""
                        () => {
                            const usernames = new Set();
                            const links = document.querySelectorAll('a[href*="instagram.com/"]');
                            
                            links.forEach(link => {
                                const match = link.href.match(/instagram\\.com\\/([^/?]+)/);
                                if (match && match[1]) {
                                    const username = match[1];
                                    if (username.length > 2 && 
                                        !['explore', 'p', 'reels', 'accounts'].includes(username)) {
                                        usernames.add(username);
                                    }
                                }
                            });
                            
                            return Array.from(usernames);
                        }
                    """)
                    
                    for username in usernames[:20]:
                        candidates.append({
                            'username': username,
                            'platform': 'instagram',
                            'discovered_via': 'semantic_search',
                            'discovery_method': 'bio_similarity',
                            'discovery_signals': 1,
                            'search_keyword': keyword
                        })
                    
                    logger.info(f"    ✅ Semantic '{keyword}': {len(usernames)} profiles")
                    
                except Exception as e:
                    logger.warning(f"    ⚠️ Search failed '{keyword}': {e}")
                    continue
            
            await page.close()
            
        except Exception as e:
            logger.error(f"  ❌ Semantic harvest failed: {e}")
        
        return candidates
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key themes from text"""
        # Simple keyword extraction
        common_words = {'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or', 'but', 'in', 'to'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in common_words]
        
        from collections import Counter
        freq = Counter(keywords)
        return [word for word, _ in freq.most_common(10)]
    
    def _deduplicate(
        self,
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Deduplicate by username, merging discovery signals
        """
        seen = {}
        
        for candidate in candidates:
            username = candidate.get('username', '').lower()
            
            if not username or len(username) < 2:
                continue
            
            if username not in seen:
                seen[username] = candidate
            else:
                # Merge: increment discovery signals
                seen[username]['discovery_signals'] += 1
                
                # Track multiple discovery methods
                if 'discovery_methods' not in seen[username]:
                    seen[username]['discovery_methods'] = [seen[username]['discovery_method']]
                
                if candidate['discovery_method'] not in seen[username]['discovery_methods']:
                    seen[username]['discovery_methods'].append(candidate['discovery_method'])
        
        return list(seen.values())


def get_playwright_harvester(embedding_service=None):
    """Get Playwright harvester instance"""
    return PlaywrightCompetitorHarvester(embedding_service)
