# University Data Collection Tool

This tool uses browser automation and LLM (Large Language Model) to collect comprehensive university information from the internet. It searches for university data, scrapes relevant web pages, and uses AI to extract structured information.

## Features

- **Web Search**: Automatically searches for university information using Google
- **Web Scraping**: Extracts content from university websites and related pages
- **LLM Analysis**: Uses OpenAI GPT-4 to extract structured data from scraped content
- **Database Integration**: Stores all collected data in the database
- **Background Processing**: Runs data collection as background tasks
- **Progress Tracking**: Monitors collection status and provides detailed results

## Prerequisites

- Python 3.8+
- OpenAI API key
- Database connection (PostgreSQL/SQLite)
- Playwright browsers

## Installation

1. **Run the setup script**:
   ```bash
   cd browser_use
   python setup.py
   ```

2. **Update environment variables**:
   Edit the `.env` file and add your:
   - OpenAI API key
   - Database connection string
   - Other configuration options

3. **Install database migrations**:
   ```bash
   alembic upgrade head
   ```

## Usage

### 1. Using the FastAPI Endpoints

The tool provides several API endpoints for data collection:

#### Start Data Collection
```bash
curl -X POST "http://localhost:8000/university-data/collect" \
     -H "Content-Type: application/json" \
     -d '{"university_name": "Stanford University"}'
```

#### Check Collection Status
```bash
curl "http://localhost:8000/university-data/status/{collection_id}"
```

#### Get Collection Results
```bash
curl "http://localhost:8000/university-data/collections/{collection_id}/results"
```

#### List All Collections
```bash
curl "http://localhost:8000/university-data/collections"
```

#### Batch Collection
```bash
curl -X POST "http://localhost:8000/university-data/collect-batch" \
     -H "Content-Type: application/json" \
     -d '{"university_names": ["MIT", "Harvard University", "Stanford University"]}'
```

### 2. Using the Python Script Directly

```python
import asyncio
from browser_use.university_scraper import UniversityDataScraper
from database.database import get_db

async def main():
    db_session = next(get_db())
    scraper = UniversityDataScraper(
        openai_api_key="your-api-key",
        db_session=db_session
    )
    
    result = await scraper.collect_university_data("Stanford University")
    print(result)

asyncio.run(main())
```

## Data Schema

The tool extracts the following university information:

### Basic Information
- Name, website, contact details
- Location (country, city, state)
- Founded year, type (public/private)
- Accreditation information

### Statistics
- Student population
- Faculty count
- Acceptance rate
- Tuition (domestic and international)
- Rankings (world and national)

### Academic Information
- Description and mission statement
- Programs offered (with details)
- Facilities available

### Metadata
- Source URLs for verification
- Confidence scores
- Processing timestamps

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `DATABASE_URL` | Database connection string | Required |
| `BROWSER_HEADLESS` | Run browser in headless mode | `true` |
| `BROWSER_TIMEOUT` | Browser timeout in milliseconds | `30000` |
| `SEARCH_DELAY` | Delay between searches in seconds | `2` |
| `SCRAPE_DELAY` | Delay between page scrapes in seconds | `1` |
| `LLM_MODEL` | OpenAI model to use | `gpt-4` |
| `LLM_TEMPERATURE` | LLM temperature setting | `0.1` |
| `LLM_MAX_TOKENS` | Maximum tokens for LLM response | `4000` |

### Search Queries

The tool automatically generates search queries for:
- Official university website
- Admissions requirements
- Programs and degrees
- Tuition and fees
- University rankings
- Student population
- Faculty information

## Database Models

### UniversityDataCollection
Tracks the overall data collection process:
- Collection status and progress
- Search results and scraped content
- LLM analysis results
- Confidence scores and metadata

### UniversitySearchTask
Manages individual search tasks:
- Search queries and engines
- Results and processing status
- Task configuration

### LLMAnalysisResult
Stores LLM analysis results:
- Raw and structured data
- Model information and prompts
- Quality metrics and citations

## Error Handling

The tool includes comprehensive error handling:
- Network timeouts and connection errors
- Rate limiting and blocking detection
- LLM API errors and parsing failures
- Database connection issues

All errors are logged and stored in the database for debugging.

## Rate Limiting

To avoid being blocked by websites:
- Delays between searches (2 seconds)
- Delays between page scrapes (1 second)
- User agent rotation
- Respect for robots.txt

## Monitoring and Logging

- Collection progress tracking
- Detailed error logging
- Performance metrics
- Confidence score calculation
- Source URL tracking

## Troubleshooting

### Common Issues

1. **Playwright browser not found**:
   ```bash
   python -m playwright install chromium
   ```

2. **OpenAI API errors**:
   - Check your API key
   - Verify account has sufficient credits
   - Check rate limits

3. **Database connection errors**:
   - Verify database URL
   - Check database is running
   - Ensure tables exist

4. **Web scraping blocked**:
   - Increase delays between requests
   - Check if site blocks automated access
   - Try different user agents

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## Performance Optimization

- Use batch collection for multiple universities
- Monitor API usage and costs
- Adjust delays based on target websites
- Use appropriate LLM models for your needs

## Security Considerations

- Store API keys securely
- Use environment variables
- Implement proper authentication
- Monitor API usage
- Respect website terms of service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 