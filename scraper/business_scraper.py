"""
Business Scraper Module

Extracts detailed information from individual Google Maps business pages.

Copyright (c) 2026 @khil
"""

import time
from typing import Optional, Dict
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeout
from rich.console import Console
from .utils import normalize_phone, clean_text, extract_emails_from_text, extract_social_links
from .email_finder import EmailFinder

console = Console()

class BusinessScraper:
    """Extract detailed information from individual business pages."""
    
    def __init__(self, page: Page, email_finder: EmailFinder):
        """Initialize business scraper."""
        self.page = page
        self.email_finder = email_finder
    
    def scrape_business(self, business_url: str) -> Optional[Dict[str, str]]:
        """
        Scrape all details from a business page.
        
        Returns dict with keys including social media links.
        """
        business_name = None
        phone = None
        website = None
        rating = None
        review_count = None
        email = None
        socials = {
            'Facebook': 'N/A',
            'Instagram': 'N/A',
            'LinkedIn': 'N/A',
            'Twitter': 'N/A'
        }
        
        try:
            # Navigate to business page
            try:
                self.page.goto(business_url, wait_until='domcontentloaded', timeout=10000)
                time.sleep(1.5)
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Page load error: {str(e)[:50]}...")
            
            # Extract basic info
            business_name = self._extract_business_name()
            phone = self._extract_phone()
            website = self._extract_website()
            rating = self._extract_rating()
            review_count = self._extract_review_count()
            
            # Try to find email and socials on Google Maps page first
            email = self._extract_email_from_page()
            maps_socials = extract_social_links(self.page.content())
            socials.update({k: v for k, v in maps_socials.items() if v != 'N/A'})
            
            # If details missing and website exists, search website
            if website and (not email or any(v == 'N/A' for v in socials.values())):
                try:
                    console.print(f"[dim]🌐 Searching website for details: {website}[/dim]")
                    details = self.email_finder.find_all_details_sync(website)
                    
                    if not email and details['Email']:
                        email = details['Email']
                        console.print(f"[dim]✓ Found email on website[/dim]")
                        
                    # Update socials if missing
                    for platform, link in details['Social'].items():
                        if socials[platform] == 'N/A' and link != 'N/A':
                            socials[platform] = link
                            console.print(f"[dim]✓ Found {platform} on website[/dim]")
                except Exception:
                    pass
            
            # Prepare data
            business_data = {
                'Business Name': business_name or 'N/A',
                'Email': email or 'N/A',
                'Contact Number': phone or 'N/A',
                'Website Link': website or 'N/A',
                'Facebook': socials['Facebook'],
                'Instagram': socials['Instagram'],
                'LinkedIn': socials['LinkedIn'],
                'Twitter': socials['Twitter'],
                'Google Map Location': business_url,
                'Rating': rating or 'N/A',
                'Number of Reviews': review_count or 'N/A'
            }
            
            display_name = business_name if business_name else "Unknown Business"
            console.print(f"[green]✓[/green] {display_name}")
            return business_data
        
        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Error scraping: {str(e)[:50]}...")
            return {
                'Business Name': business_name or 'N/A',
                'Email': email or 'N/A',
                'Contact Number': phone or 'N/A',
                'Website Link': website or 'N/A',
                'Facebook': socials['Facebook'],
                'Instagram': socials['Instagram'],
                'LinkedIn': socials['LinkedIn'],
                'Twitter': socials['Twitter'],
                'Google Map Location': business_url,
                'Rating': rating or 'N/A',
                'Number of Reviews': review_count or 'N/A'
            }
    
    def _extract_business_name(self) -> Optional[str]:
        """Extract business name."""
        try:
            # Try multiple selectors
            selectors = [
                'h1.DUwDvf',
                'h1[class*="title"]',
                'h1',
                '[role="main"] h1'
            ]
            
            for selector in selectors:
                element = self.page.query_selector(selector)
                if element:
                    name = element.inner_text().strip()
                    if name:
                        return clean_text(name)
            
            return None
        except Exception:
            return None
    
    def _extract_phone(self) -> Optional[str]:
        """Extract phone number."""
        try:
            # Look for phone button or link
            selectors = [
                'button[data-item-id*="phone"]',
                'a[data-item-id*="phone"]',
                'button[aria-label*="phone" i]',
                'a[href^="tel:"]',
                '[data-tooltip*="phone" i]'
            ]
            
            for selector in selectors:
                element = self.page.query_selector(selector)
                if element:
                    # Try to get aria-label first
                    phone = element.get_attribute('aria-label')
                    if not phone:
                        phone = element.inner_text()
                    if not phone and element.get_attribute('href'):
                        phone = element.get_attribute('href').replace('tel:', '')
                    
                    if phone:
                        # Clean phone number
                        phone = phone.replace('Phone:', '').replace('Call', '').strip()
                        return normalize_phone(phone)
            
            return None
        except Exception:
            return None
    
    def _extract_website(self) -> Optional[str]:
        """Extract website URL."""
        try:
            # Look for website link
            selectors = [
                'a[data-item-id*="authority"]',
                'a[aria-label*="website" i]',
                'a[data-tooltip*="website" i]',
                'a[href*="http"]:has-text("Website")'
            ]
            
            for selector in selectors:
                element = self.page.query_selector(selector)
                if element:
                    href = element.get_attribute('href')
                    if href and 'http' in href:
                        # Google Maps wraps URLs, extract the actual URL
                        if 'google.com/url?q=' in href:
                            import urllib.parse
                            parsed = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)
                            if 'q' in parsed:
                                return parsed['q'][0]
                        return href
            
            return None
        except Exception:
            return None
    
    def _extract_rating(self) -> Optional[str]:
        """Extract rating."""
        try:
            # Look for rating element
            selectors = [
                'div.F7nice span[aria-hidden="true"]',
                'span.ceNzKf',
                '[aria-label*="stars"]'
            ]
            
            for selector in selectors:
                element = self.page.query_selector(selector)
                if element:
                    rating_text = element.inner_text().strip()
                    if rating_text and rating_text[0].isdigit():
                        return rating_text
            
            return None
        except Exception:
            return None
    
    def _extract_review_count(self) -> Optional[str]:
        """Extract number of reviews."""
        try:
            import re
            
            # Strategy 1: Try multiple specific selectors
            # NOTE: Google Maps changed HTML structure - div.F7nice no longer exists
            selectors = [
                'span[aria-label*="reviews"]',  # Primary: <span aria-label="56 reviews">(56)</span>
                'button[aria-label*="reviews"]',
                'span[aria-label*="review"]',  # Singular form
                'button[aria-label*="review"]',
            ]
            
            for selector in selectors:
                element = self.page.query_selector(selector)
                if element:
                    # Get aria-label first (most reliable)
                    aria_label = element.get_attribute('aria-label')
                    if aria_label:
                        # Extract from "56 reviews" or "1,704 reviews"
                        match = re.search(r'([\d,]+)\s*review', aria_label, re.IGNORECASE)
                        if match:
                            return match.group(1)
                    
                    # Fallback to text content like "(56)"
                    text = element.inner_text()
                    if text:
                        # Pattern: "(56)" or "(1,704)"
                        match = re.search(r'\(([\d,]+)\)', text)
                        if match:
                            return match.group(1)
                        
                        # Pattern: "56 reviews" in text
                        match = re.search(r'([\d,]+)\s*review', text, re.IGNORECASE)
                        if match:
                            return match.group(1)
            
            return None
        except Exception as e:
            console.print(f"[dim]Review count extraction error: {str(e)[:30]}[/dim]")
            return None
    
    def _extract_email_from_page(self) -> Optional[str]:
        """Extract email directly from the Google Maps business page."""
        try:
            # Strategy 1: Look for email in specific elements
            email_selectors = [
                'button[data-item-id*="email"]',
                'a[href^="mailto:"]',
                'div[data-item-id*="email"]',
                '[aria-label*="email" i]'
            ]
            
            for selector in email_selectors:
                elements = self.page.query_selector_all(selector)
                for element in elements:
                    # Check href for mailto
                    href = element.get_attribute('href')
                    if href and href.startswith('mailto:'):
                        email = href.replace('mailto:', '').split('?')[0].strip()
                        emails = extract_emails_from_text(email)
                        if emails:
                            return emails[0]
                    
                    # Check aria-label
                    aria_label = element.get_attribute('aria-label')
                    if aria_label:
                        emails = extract_emails_from_text(aria_label)
                        if emails:
                            return emails[0]
                    
                    # Check text content
                    try:
                        text = element.inner_text()
                        emails = extract_emails_from_text(text)
                        if emails:
                            return emails[0]
                    except:
                        pass
            
            # Strategy 2: Search visible text content
            try:
                visible_text = self.page.evaluate("""
                    () => {
                        return document.body.innerText;
                    }
                """)
                emails = extract_emails_from_text(visible_text)
                if emails:
                    # Filter out common noise emails
                    for email in emails:
                        lower_email = email.lower()
                        if not any(noise in lower_email for noise in ['example.com', 'test.com', 'google.com', 'maps.com']):
                            return email
            except:
                pass
            
            # Strategy 3: Search entire page HTML as fallback
            page_text = self.page.content()
            emails = extract_emails_from_text(page_text)
            
            if emails:
                # Filter noise and return first valid email
                for email in emails:
                    lower_email = email.lower()
                    if not any(noise in lower_email for noise in ['example.com', 'test.com', 'google.com', 'maps.com', 'schema.org']):
                        return email
            
            return None
        except Exception as e:
            console.print(f"[dim]Email extraction error: {str(e)[:30]}[/dim]")
            return None
