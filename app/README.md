# University Data Collection System

A comprehensive system for collecting university information using headless browser scraping with an MCP-like interface for LLM integration.

## Features

- **Headless Browser Scraping**: Uses Selenium with Chrome in headless mode to scrape university websites
- **MCP-Style Interface**: LLM can request specific fields of information
- **Database Storage**: Stores collected data in SQLite database with SQLAlchemy ORM
- **Field-Specific Collection**: Request only the data you need (basic info, contact, academic, statistics, etc.)
- **Confidence Scoring**: Provides confidence scores for data quality
- **Batch Processing**: Collect data for multiple universities at once
- **Error Handling**: Robust error handling and retry mechanisms

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Chrome browser (if not already installed)

3. Install ChromeDriver:
```bash
# On macOS with Homebrew
brew install chromedriver

# Or download from https://chromedriver.chromium.org/
```

## Quick Start

### Basic Usage

```python
import asyncio
from app.main import UniversityDataCollector

async def main():
    collector = UniversityDataCollector()
    
    # Collect basic information about MIT
    result = await collector.collect_university_data(
        "Massachusetts Institute of Technology",
        fields=["basic_info", "contact", "academic"]
    )
    
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"Data: {result['data']}")
    
    collector.close()

asyncio.run(main())
```

### Command Line Usage

```bash
# List available fields
python -m app.main --list-fields

# Collect data for a single university
python -m app.main --university "Harvard University" --fields basic_info contact academic

# Collect data for multiple universities from a file
python -m app.main --file universities.txt --fields statistics programs --output results.json

# Collect all available data
python -m app.main --university "Stanford University" --fields all
```

## Available Fields

The system can collect the following categories of information:

### Basic Info
- University name
- Official website URL
- Country, city, state location

### Contact Information
- Phone numbers
- Email addresses
- Physical addresses

### Academic Information
- Founded year
- University type (Public/Private)
- Accreditation information

### Statistics
- Student population
- Faculty count
- Acceptance rate
- Tuition fees (domestic/international)

### Programs
- List of academic programs
- Degree levels offered
- Fields of study

### Facilities
- Campus facilities
- Facility types

### About Information
- University description
- Mission statement
- Vision statement

## MCP-Style Interface

The system provides an MCP-like interface where an LLM can request specific fields:

```python
from app.mcp_server import UniversityMCPServer, FieldType, FieldRequest

async def mcp_example():
    server = UniversityMCPServer()
    
    # LLM requests specific fields
    request = FieldRequest(
        university_name="University of Oxford",
        fields=[FieldType.BASIC_INFO, FieldType.ACADEMIC],
        priority=1
    )
    
    response = await server.process_field_request(request)
    
    print(f"Confidence: {response.confidence_score}")
    print(f"Data: {response.fields}")
    
    server.close()
```

## Database Schema

The system uses SQLAlchemy with the following models:

### University
- Basic information (name, website, location)
- Contact details (phone, email)
- Academic information (founded year, type)
- Statistics (student count, faculty count, etc.)
- Metadata (scraped_at, confidence_score)

### Program
- Program name and level
- Field of study
- Duration and tuition
- Requirements

### Facility
- Facility name and type
- Description and capacity

## Configuration

### Environment Variables

Create a `.env` file in the app directory:

```env
DATABASE_URL=sqlite:///./universities.db
CHROME_HEADLESS=true
SCRAPER_TIMEOUT=10
```

### Database Configuration

The system supports multiple database backends:

```python
# SQLite (default)
collector = UniversityDataCollector("sqlite:///./universities.db")

# PostgreSQL
collector = UniversityDataCollector("postgresql://user:pass@localhost/universities")

# MySQL
collector = UniversityDataCollector("mysql://user:pass@localhost/universities")
```

## Testing

Run the test suite:

```bash
python app/test_system.py
```

The test suite includes:
- Basic functionality tests
- MCP-style request tests
- Error handling tests

## Examples

### Batch Collection

```python
universities = [
    "Harvard University",
    "Stanford University",
    "MIT",
    "Yale University",
    "Princeton University"
]

results = await collector.batch_collect(
    universities,
    fields=["basic_info", "statistics"]
)

for result in results:
    print(f"{result['university_name']}: {result['status']}")
```

### Custom Field Requests

```python
# Request only statistics
stats_result = await collector.collect_university_data(
    "University of California Berkeley",
    fields=["statistics"]
)

# Request only programs
programs_result = await collector.collect_university_data(
    "Carnegie Mellon University",
    fields=["programs"]
)
```

## Error Handling

The system includes robust error handling:

- **Network errors**: Automatic retries with exponential backoff
- **Invalid universities**: Graceful handling of non-existent universities
- **Scraping failures**: Fallback mechanisms and partial data collection
- **Database errors**: Transaction rollback and error logging

## Performance Considerations

- **Rate limiting**: Built-in delays between requests to be respectful to websites
- **Headless mode**: Chrome runs in headless mode for better performance
- **Resource optimization**: Disables images and CSS for faster loading
- **Connection pooling**: Efficient database connection management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the test suite for examples
2. Review the error logs
3. Ensure Chrome and ChromeDriver are properly installed
4. Verify network connectivity for web scraping 