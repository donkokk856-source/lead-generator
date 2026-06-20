"""
Email Finder Module

Searches websites for email addresses using async HTTP requests.


"""

import asyncio
import httpx
import concurrent.futures
from bs4 import BeautifulSoup
from typing import Optional, Set
from rich.console import Console
from .utils import extract_emails_from_text, normalize_url, extract_social_links

console = Console()

class EmailFinder:
    """Extract email addresses and social media links from websites."""
    
    # Common paths to check
    EMAIL_PATHS = [
        '',  # Homepage
        '/contact',
        '/contact-us',
        '/about',
        '/about-us',
        '/social',
    ]
    
    def __init__(self, timeout: int = 5):
        """Initialize email finder."""
        self.timeout = timeout
        self.cache: dict[str, dict] = {}
    
    async def find_all_details(self, website_url: str) -> dict:
        """Find both email and social links."""
        if not website_url:
            return {'Email': None, 'Social': {}}
            
        normalized_url = normalize_url(website_url)
        if not normalized_url:
            return {'Email': None, 'Social': {}}
            
        if normalized_url in self.cache:
            return self.cache[normalized_url]
            
        result = {'Email': None, 'Social': {}}
        all_socials = {
            'Facebook': 'N/A',
            'Instagram': 'N/A',
            'LinkedIn': 'N/A',
            'Twitter': 'N/A'
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=False
            ) as client:
                # Try homepage first
                homepage_data = await self._extract_details_from_url(client, normalized_url)
                result['Email'] = homepage_data['Email']
                all_socials.update({k: v for k, v in homepage_data['Social'].items() if v != 'N/A'})
                
                # If we're missing details, try common pages
                if not result['Email'] or any(v == 'N/A' for v in all_socials.values()):
                    base_url = normalized_url.rstrip('/')
                    for path in self.EMAIL_PATHS[1:]:
                        url = f"{base_url}{path}"
                        page_data = await self._extract_details_from_url(client, url)
                        
                        if not result['Email'] and page_data['Email']:
                            result['Email'] = page_data['Email']
                            
                        all_socials.update({k: v for k, v in page_data['Social'].items() if v != 'N/A' and all_socials[k] == 'N/A'})
                        
                        # Stop if we found everything
                        if result['Email'] and all(v != 'N/A' for v in all_socials.values()):
                            break
        except Exception:
            pass
            
        result['Social'] = all_socials
        self.cache[normalized_url] = result
        return result

    async def find_email(self, website_url: str) -> Optional[str]:
        """Find email address on a website."""
        details = await self.find_all_details(website_url)
        return details.get('Email')

    async def _extract_details_from_url(self, client: httpx.AsyncClient, url: str) -> dict:
        """Extract email and social links from a specific URL."""
        data = {'Email': None, 'Social': {}}
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return data
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get all text and links
            text = soup.get_text(separator=' ', strip=True)
            html = response.text
            
            # Extract email
            emails = extract_emails_from_text(text)
            # Also check mailto links
            for link in soup.find_all('a', href=True):
                if link['href'].startswith('mailto:'):
                    email = link['href'].replace('mailto:', '').split('?')[0]
                    if self._is_valid_email(email):
                        emails.append(email)
            
            if emails:
                # Filter noise
                noise_patterns = ['example.com', 'test.com', 'wixpress', 'sentry.io']
                for e in emails:
                    if not any(n in e.lower() for n in noise_patterns):
                        data['Email'] = e
                        break
            
            # Extract social links from HTML (better for hrefs)
            data['Social'] = extract_social_links(html)
            
        except Exception:
            pass
        return data
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        try:
            if not email or not isinstance(email, str):
                return False
            
            email = email.strip()
            
            if len(email) < 5 or len(email) > 254:  # RFC 5321
                return False
            
            # Must have exactly one @
            if email.count('@') != 1:
                return False
            
            # Basic email validation
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email))
        except Exception:
            return False
    
    def find_all_details_sync(self, website_url: str) -> dict:
        """Synchronous wrapper for find_all_details."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_all_in_new_loop, website_url)
                    return future.result(timeout=self.timeout + 2)
            else:
                return loop.run_until_complete(self.find_all_details(website_url))
        except Exception:
            return {'Email': None, 'Social': {}}

    def _run_all_in_new_loop(self, website_url: str) -> dict:
        """Helper to run async code in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.find_all_details(website_url))
        finally:
            loop.close()

    def find_email_sync(self, website_url: str) -> Optional[str]:
        """Synchronous wrapper for find_email."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_event_loop()
            # Check if loop is running
            if loop.is_running():
                # Create a new event loop in a thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_in_new_loop, website_url)
                    return future.result(timeout=self.timeout + 2)
            else:
                return loop.run_until_complete(self.find_email(website_url))
        except RuntimeError:
            # No event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.find_email(website_url))
            finally:
                loop.close()
        except concurrent.futures.TimeoutError:
            console.print(f"[yellow]⚠[/yellow] Email finder timeout for {website_url[:50]}...")
            return None
        except Exception as e:
            # Show full error message for debugging
            error_msg = f"{type(e).__name__}: {str(e)}"
            console.print(f"[yellow]⚠[/yellow] Email finder error: {error_msg}")
            return None
    
    def _run_in_new_loop(self, website_url: str) -> Optional[str]:
        """Helper to run async code in a new event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.find_email(website_url))
        finally:
            loop.close()
