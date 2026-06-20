from scraper.google_maps import GoogleMapsScraper
from scraper.business_scraper import BusinessScraper
from scraper.email_finder import EmailFinder
from scraper.csv_exporter import CSVExporter

def run_scraper(niche, location, leads_count, output_path):
    maps_scraper = GoogleMapsScraper()
    email_finder = EmailFinder(timeout=5)
    csv_exporter = CSVExporter(output_path)

    try:
        maps_scraper.start_browser()

        if not maps_scraper.search_google_maps(niche, location):
            return {"status": "error", "message": "Search failed"}

        business_urls = maps_scraper.scroll_and_collect_urls(leads_count)

        if not business_urls:
            return {"status": "error", "message": "No businesses found"}

        business_scraper = BusinessScraper(maps_scraper.page, email_finder)

        results = []
        for url in business_urls:
            try:
                data = business_scraper.scrape_business(url)
                if data:
                    csv_exporter.append_business(data)
                    results.append(data)
            except Exception as e:
                print("Error:", e)

        return {
            "status": "success",
            "count": len(results),
            "data": results,
            "file": output_path
        }

    finally:
        maps_scraper.close_browser()