# University Data Collector Script

A standalone script to collect university data using browser automation and LLM (Large Language Model) analysis. This script searches for university information on the web, scrapes relevant content, and uses AI to extract structured data.

## Features

- **Web Search**: Automatically searches for university information using Google
- **Web Scraping**: Extracts content from university websites and related pages
- **LLM Analysis**: Uses OpenAI GPT-4 to extract structured data from scraped content
- **Database Storage**: Stores all collected data in the database
- **Batch Processing**: Process multiple universities with configurable delays
- **Progress Tracking**: Detailed logging and progress monitoring
- **JSON Export**: Save results to JSON files for further analysis

## Quick Start

### 1. Setup

```bash
# Navigate to the app directory
cd app

# Run the setup script
python setup_collector.py
```

### 2. Configure

Edit the `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Run

```bash
# Collect data for a single university
python university_data_collector.py "Stanford University"

# Collect data for multiple universities
python university_data_collector.py "Stanford University" "MIT" "Harvard University"

# Collect from a file (one university per line)
python university_data_collector.py --file universities_example.txt
```

## Usage Examples

### Single University
```bash
python university_data_collector.py "Stanford University"
```

### Multiple Universities
```bash
python university_data_collector.py "Stanford University" "MIT" "Harvard University"
```

### From File
```bash
# Create a file with university names (one per line)
echo "Stanford University
MIT
Harvard University" > my_universities.txt

# Run collection
python university_data_collector.py --file my_universities.txt
```

### Custom Output File
```bash
python university_data_collector.py --file universities.txt --output my_results.json
```

### Adjust Delay Between Universities
```bash
python university_data_collector.py --file universities.txt --delay 10
```

### Don't Save to JSON
```bash
python university_data_collector.py "Stanford University" --no-save
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `universities` | University names as arguments | Required |
| `--file, -f` | File containing university names | None |
| `--output, -o` | Output JSON file name | Auto-generated |
| `--delay, -d` | Delay between universities (seconds) | 5 |
| `--openai-key` | OpenAI API key | From environment |
| `--no-save` | Don't save results to JSON | False |

## Output

### Console Output
The script provides detailed logging including:
- Progress updates for each university
- Extracted data summaries
- Confidence scores
- Error messages
- Final collection summary

### JSON Output
Results are saved to `output/university_data_collection_YYYYMMDD_HHMMSS.json` with the following structure:

```json
{
  "metadata": {
    "total_universities": 3,
    "successful_collections": 2,
    "failed_collections": 1,
    "generated_at": "2024-01-15T10:30:00",
    "script_version": "1.0.0"
  },
  "results": [
    {
      "success": true,
      "data_collection_id": 1,
      "extracted_data": {
        "name": "Stanford University",
        "website": "https://www.stanford.edu",
        "country": "United States",
        "city": "Stanford",
        "state": "California",
        "student_population": 17249,
        "acceptance_rate": 4.3,
        "tuition_domestic": 56169,
        "programs": [...],
        "facilities": [...]
      },
      "confidence_score": 0.85,
      "source_urls": [...]
    }
  ]
}
```

### Database Storage
All collected data is automatically stored in the database with:
- University information
- Search results and scraped content
- LLM analysis results
- Confidence scores and metadata

## Data Schema

The script extracts the following university information:

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

Create a `.env` file in the app directory:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Database Configuration (optional)
DATABASE_URL=sqlite:///universities.db

# Browser Configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# Rate Limiting
SEARCH_DELAY=2
SCRAPE_DELAY=1

# LLM Configuration
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   ```bash
   # Set your API key
   export OPENAI_API_KEY="your-key-here"
   # Or edit the .env file
   ```

2. **Playwright Browser Not Found**:
   ```bash
   python -m playwright install chromium
   ```

3. **Database Connection Error**:
   ```bash
   # Run database migration
   alembic upgrade head
   ```

4. **Web Scraping Blocked**:
   - Increase delays between requests
   - Check if target sites block automated access
   - Try different user agents

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## Performance Tips

- Use batch processing for multiple universities
- Adjust delays based on target websites
- Monitor OpenAI API usage and costs
- Use appropriate LLM models for your needs

## Security Considerations

- Store API keys securely in environment variables
- Monitor API usage to avoid unexpected costs
- Respect website terms of service
- Implement proper rate limiting

## Files Created

- `output/` - JSON result files
- `logs/` - Log files
- `university_collection.log` - Main log file
- `.env` - Configuration file

## Dependencies

- Python 3.8+
- OpenAI API access
- Playwright browsers
- SQLAlchemy
- FastAPI (for database models)

## License

This project is licensed under the MIT License. 