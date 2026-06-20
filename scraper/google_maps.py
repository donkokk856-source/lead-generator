"""
Google Maps Scraper Module

Handles navigation and URL collection from Google Maps search results.

Copyright (c) 2026 @khil
"""

import time
from typing import List, Set
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeout
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

class GoogleMapsScraper:
    """Scrape business listings from Google Maps."""
    
    def __init__(self):
        """Initialize Google Maps scraper."""
        self.browser: Browser = None
        self.page: Page = None
        self.playwright = None
    
    def start_browser(self):
        """Start Playwright browser."""
        console.print("[cyan]Starting browser...[/cyan]")
        self.playwright = sync_playwright().start()
        
        # Launch browser with specific args to avoid detection
        self.browser = self.playwright.chromium.launch(
            headless=False,  # Set to True for production
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create context with realistic settings
        context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = context.new_page()
        
        # Remove webdriver flag
        self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        console.print("[green]✓[/green] Browser started")
    
    def close_browser(self):
        """Close browser and cleanup."""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        console.print("[green]✓[/green] Browser closed")
    
    def search_google_maps(self, niche: str, location: str) -> bool:
        """
        Navigate to Google Maps and perform search.
        
        Args:
            niche: Business type (e.g., "dentist", "gym")
            location: Location (e.g., "New York", "Mumbai")
        
        Returns:
            True if search successful, False otherwise
        """
        try:
            query = f"{niche} in {location}"
            search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            
            console.print(f"[cyan]Searching: {query}[/cyan]")
            self.page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for results to load
            time.sleep(3)
            
            # Check if we have results
            results_panel = self.page.query_selector('[role="feed"]')
            if not results_panel:
                console.print("[red]No results found[/red]")
                return False
            
            console.print("[green]✓[/green] Search results loaded")
            return True
        
        except Exception as e:
            console.print(f"[red]Search failed: {str(e)}[/red]")
            return False
    
    def scroll_and_collect_urls(self, max_leads: int) -> List[str]:
        """
        Scroll through results and collect business URLs.
        
        Args:
            max_leads: Number of leads to collect (0 = all)
        
        Returns:
            List of business URLs
        """
        business_urls: Set[str] = set()
        
        # Get the scrollable results panel
        results_panel = self.page.query_selector('[role="feed"]')
        if not results_panel:
            console.print("[red]Could not find results panel[/red]")
            return []
        
        console.print(f"[cyan]{'Scrolling to collect all leads...' if max_leads == 0 else f'Collecting {max_leads} leads...'}[/cyan]")
        
        consecutive_no_new = 0
        scroll_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            if max_leads > 0:
                task = progress.add_task(f"Collecting URLs...", total=max_leads)
            else:
                task = progress.add_task("Scrolling...", total=None)
            
            while True:
                # Get current business links
                previous_count = len(business_urls)
                
                # Find all business links in the current view
                links = self.page.query_selector_all('a[href*="/maps/place/"]')
                
                for link in links:
                    href = link.get_attribute('href')
                    if href and '/maps/place/' in href:
                        # Clean URL (remove query params)
                        clean_url = href.split('?')[0] if '?' in href else href
                        business_urls.add(clean_url)
                
                # Update progress
                current_count = len(business_urls)
                if max_leads > 0:
                    progress.update(task, completed=min(current_count, max_leads))
                else:
                    progress.update(task, description=f"Collected {current_count} URLs...")
                
                # Check if we have enough leads
                if max_leads > 0 and current_count >= max_leads:
                    console.print(f"[green]✓[/green] Collected {max_leads} business URLs")
                    break
                
                # Check if we got new results
                if current_count == previous_count:
                    consecutive_no_new += 1
                else:
                    consecutive_no_new = 0
                
                # Check for "end of list" message
                if self._check_end_of_list():
                    console.print(f"[green]✓[/green] Reached end of list with {current_count} businesses")
                    break
                
                # If no new results after several scrolls, we might be at the end
                if consecutive_no_new >= 5:
                    console.print(f"[yellow]No new results after {consecutive_no_new} scrolls. Assuming end of list.[/yellow]")
                    break
                
                # Scroll down
                self._scroll_results_panel(results_panel)
                scroll_count += 1
                
                # Small delay to allow content to load
                time.sleep(0.5)
        
        # Convert to list and limit if needed
        url_list = list(business_urls)
        if max_leads > 0:
            url_list = url_list[:max_leads]
        
        return url_list
    
    def _scroll_results_panel(self, panel):
        """Scroll the results panel down."""
        try:
            # Scroll using JavaScript
            panel.evaluate("""
                (element) => {
                    element.scrollTop = element.scrollHeight;
                }
            """)
        except Exception as e:
            console.print(f"[dim]Scroll error: {str(e)}[/dim]")
    
    def _check_end_of_list(self) -> bool:
        """Check if we've reached the end of the list."""
        try:
            # Look for end of list message
            end_messages = [
                "You've reached the end of the list",
                "You've reached the end",
                "No more results"
            ]
            
            page_text = self.page.content().lower()
            
            for message in end_messages:
                if message.lower() in page_text:
                    return True
            
            # Alternative: check if there's a specific element indicating end
            end_element = self.page.query_selector('span:has-text("You\'ve reached the end")')
            if end_element:
                return True
            
            return False
        except Exception:
            return False
