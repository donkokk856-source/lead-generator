import csv
import os
from typing import List, Dict
from pathlib import Path
from rich.console import Console

console = Console()

class CSVExporter:
    """Handle CSV file creation and progressive saving."""
    
    HEADERS = [
        'Business Name',
        'Email',
        'Contact Number',
        'Website Link',
        'Facebook',
        'Instagram',
        'LinkedIn',
        'Twitter',
        'Google Map Location',
        'Rating',
        'Number of Reviews'
    ]
    
    def __init__(self, output_path: str):
        """Initialize CSV exporter."""
        self.output_path = Path(output_path)
        self.ensure_directory_exists()
        self.initialize_csv()
    
    def ensure_directory_exists(self):
        """Create output directory if it doesn't exist."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
    
    def initialize_csv(self):
        """Create CSV file with headers."""
        try:
            with open(self.output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                writer.writeheader()
            console.print(f"[green]✓[/green] CSV file initialized: {self.output_path}")
        except Exception as e:
            console.print(f"[red]Failed to initialize CSV: {str(e)}[/red]")
            raise
    
    def append_business(self, business_data: Dict[str, str]):
        """Append a single business to the CSV file."""
        try:
            with open(self.output_path, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=self.HEADERS)
                writer.writerow(business_data)
        except Exception as e:
            console.print(f"[red]Failed to append business to CSV: {str(e)}[/red]")
            raise
    
    def append_businesses(self, businesses: List[Dict[str, str]]):
        """Append multiple businesses to the CSV file."""
        for business in businesses:
            self.append_business(business)
    
    def get_row_count(self) -> int:
        """Get the number of rows (excluding header) in the CSV."""
        try:
            with open(self.output_path, 'r', encoding='utf-8-sig') as f:
                return sum(1 for _ in f) - 1  # Subtract header
        except Exception:
            return 0
