from fastapi import FastAPI
from pydantic import BaseModel
from n8napp import run_scraper

app = FastAPI()

class ScrapeRequest(BaseModel):
    niche: str
    location: str
    leads_count: int = 10

@app.post("/scrape")
def scrape(req: ScrapeRequest):
    output_file = f"{req.niche}_{req.location}.csv"

    result = run_scraper(
        req.niche,
        req.location,
        req.leads_count,
        output_file
    )

    return result