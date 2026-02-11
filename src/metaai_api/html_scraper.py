"""
HTML scraping utilities for extracting video URLs from Meta AI conversation pages.
"""
import re
import time
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class MetaAIHTMLScraper:
    """Scrapes video URLs from Meta AI conversation HTML pages."""
    
    def __init__(self, session):
        """
        Initialize HTML scraper.
        
        Args:
            session: requests.Session with authentication cookies
        """
        self.session = session
        self.logger = logger
        
    def fetch_conversation_html(self, conversation_id: str) -> Optional[str]:
        """
        Fetch the HTML of a Meta AI conversation page.
        
        Args:
            conversation_id: The conversation UUID
            
        Returns:
            HTML content as string, or None if failed
        """
        url = f"https://www.meta.ai/prompt/{conversation_id}"
        
        try:
            self.logger.info(f"Fetching conversation HTML from {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch conversation HTML: {e}")
            return None
    
    def extract_video_urls_from_html(self, html: str) -> List[Dict[str, str]]:
        """
        Extract video URLs from Meta AI conversation HTML.
        
        Args:
            html: HTML content of the conversation page
            
        Returns:
            List of dicts with video information (url, id, etc.)
        """
        videos = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Method 1: Find <video> tags
            video_tags = soup.find_all('video')
            for video in video_tags:
                src = video.get('src')
                if src and 'fbcdn.net' in src:
                    videos.append({
                        'url': src,
                        'type': 'video_tag'
                    })
                    self.logger.info(f"Found video URL in <video> tag: {src[:100]}...")
                    
                # Check for <source> tags inside <video>
                sources = video.find_all('source')
                for source in sources:
                    src = source.get('src')
                    if src and 'fbcdn.net' in src:
                        videos.append({
                            'url': src,
                            'type': 'source_tag'
                        })
                        self.logger.info(f"Found video URL in <source> tag: {src[:100]}...")
            
            # Method 2: Find URLs in inline JavaScript/JSON
            # Meta AI often embeds data in <script> tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_content = script.string or ''
                
                # Look for video URLs in script content
                # Pattern: https://video-*.xx.fbcdn.net/...mp4
                video_url_pattern = r'https://video-[^"\']+\.mp4[^"\']*'
                matches = re.findall(video_url_pattern, script_content)
                
                for url in matches:
                    # Clean up any escaped characters
                    url = url.replace('\\/', '/')
                    if url not in [v['url'] for v in videos]:
                        videos.append({
                            'url': url,
                            'type': 'script_json'
                        })
                        self.logger.info(f"Found video URL in script: {url[:100]}...")
            
            # Method 3: Search for fbcdn video URLs anywhere in HTML
            if not videos:
                fbcdn_pattern = r'https://video-[a-z0-9-]+\.xx\.fbcdn\.net/[^\s"\'<>]+\.mp4[^\s"\'<>]*'
                matches = re.findall(fbcdn_pattern, html)
                
                for url in matches:
                    url = url.replace('\\/', '/')
                    if url not in [v['url'] for v in videos]:
                        videos.append({
                            'url': url,
                            'type': 'html_search'
                        })
                        self.logger.info(f"Found video URL in HTML: {url[:100]}...")
            
            self.logger.info(f"Extracted {len(videos)} video URLs from HTML")
            
        except Exception as e:
            self.logger.error(f"Error extracting video URLs from HTML: {e}")
        
        return videos
    
    def fetch_video_urls_from_page(
        self, 
        conversation_id: str,
        max_attempts: int = 12,
        wait_seconds: int = 5
    ) -> List[Dict[str, str]]:
        """
        Fetch video URLs from Meta AI conversation page with retry logic.
        Videos may take time to process, so we retry until URLs are found.
        
        Args:
            conversation_id: The conversation UUID
            max_attempts: Maximum number of retry attempts (default: 12)
            wait_seconds: Seconds to wait between attempts (default: 5)
            
        Returns:
            List of dicts with video information
        """
        self.logger.info(
            f"Fetching video URLs from page for conversation {conversation_id} "
            f"(max {max_attempts} attempts, {wait_seconds}s intervals)"
        )
        
        for attempt in range(1, max_attempts + 1):
            self.logger.info(f"Attempt {attempt}/{max_attempts}...")
            
            html = self.fetch_conversation_html(conversation_id)
            if not html:
                self.logger.warning(f"Failed to fetch HTML on attempt {attempt}")
                time.sleep(wait_seconds)
                continue
            
            videos = self.extract_video_urls_from_html(html)
            
            if videos:
                self.logger.info(f"Successfully found {len(videos)} video URLs on attempt {attempt}")
                return videos
            
            if attempt < max_attempts:
                self.logger.info(f"No videos found yet, waiting {wait_seconds}s before retry...")
                time.sleep(wait_seconds)
        
        self.logger.warning(f"No video URLs found after {max_attempts} attempts")
        return []
