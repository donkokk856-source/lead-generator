import re
import time
import validators
from typing import Optional, Callable, Any
from rich.console import Console

console = Console()

def validate_email(email: str) -> bool:
    """Validate email address using regex."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def extract_emails_from_text(text: str) -> list[str]:
    """Extract all email addresses from text using regex."""
    if not text:
        return []
    pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    emails = re.findall(pattern, text)
    # Filter and validate emails
    valid_emails = [email for email in emails if validate_email(email)]
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in valid_emails:
        email_lower = email.lower()
        if email_lower not in seen:
            seen.add(email_lower)
            unique_emails.append(email)
    return unique_emails

def normalize_url(url: str) -> Optional[str]:
    """Normalize and validate URL."""
    if not url:
        return None
    
    url = url.strip()
    
    # Add https:// if no protocol
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    
    # Validate URL
    if validators.url(url):
        return url
    return None

def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number by removing extra characters."""
    if not phone:
        return None
    
    # Remove common formatting characters but keep the actual number
    phone = phone.strip()
    return phone if phone else None

def retry_on_exception(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """Retry a function on exception."""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                console.print(f"[red]Failed after {max_retries} attempts: {str(e)}[/red]")
                raise
            console.print(f"[yellow]Attempt {attempt + 1} failed, retrying in {delay}s...[/yellow]")
            time.sleep(delay)
    return None

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and special characters."""
    if not text:
        return ""
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_social_links(text: str) -> dict[str, str]:
    """Extract social media links from text."""
    social_links = {
        'Facebook': 'N/A',
        'Instagram': 'N/A',
        'LinkedIn': 'N/A',
        'Twitter': 'N/A'
    }
    
    if not text:
        return social_links
        
    patterns = {
        'Facebook': r'https?://(?:www\.)?facebook\.com/[\w.%-]+/?',
        'Instagram': r'https?://(?:www\.)?instagram\.com/[\w.%-]+/?',
        'LinkedIn': r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[\w.%-]+/?',
        'Twitter': r'https?://(?:www\.)?(?:twitter\.com|x\.com)/[\w.%-]+/?'
    }
    
    for platform, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            # Clean up potential noise (like share links)
            for match in matches:
                if any(noise in match for noise in ['/sharer/', '/share', '/intent/']):
                    continue
                social_links[platform] = match
                break
                
    return social_links
