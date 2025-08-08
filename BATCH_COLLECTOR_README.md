# Batch University Data Collector

A sophisticated script to collect university data from a CSV file using the `university_data_collector.py` with a beautiful terminal interface and comprehensive progress tracking.

## Features

🎯 **Sophisticated Progress Tracking**
- Real-time progress bar with time estimates
- Live statistics (success rate, confidence scores, ETA)
- Current university information display
- Graceful interruption handling (Ctrl+C)

📊 **Rich Terminal Interface**
- Beautiful tables and panels using Rich library
- Color-coded success/failure indicators
- Comprehensive statistics and summaries
- Professional-looking output

🔄 **Flexible Filtering Options**
- Filter by rank range (start-rank to end-rank)
- Filter by country
- Limit total number of universities
- Preview mode to see what will be processed

💾 **Progress Persistence**
- Automatic progress checkpoints every 10 universities
- JSON output with comprehensive metadata
- Resume capability (can be extended)

⚡ **Performance Features**
- **Parallel Processing**: Run multiple universities simultaneously (configurable concurrency)
- **Skip Existing**: Automatically skip universities already in the database
- **Retry Logic**: Automatic retries for network failures with exponential backoff
- **Network Diagnostics**: Built-in connectivity checks before starting collection
- Configurable delay between requests
- Batch processing with error handling
- Detailed logging to file

🔍 **Advanced Search Strategies**
- **Wikipedia & Academic Sources**: Prioritizes Wikipedia and academic databases
- **Educational Databases**: Direct access to university ranking sites
- **Google Search**: Enhanced anti-bot measures
- **Direct URL Access**: Attempts direct university website access
- **Knowledge-Based Fallback**: LLM-powered fallback when web scraping fails
- **Bing Search**: Alternative search engine as last resort

## Installation

1. Install the required dependencies:
```bash
source .venv/bin/activate
uv pip install rich
```

2. Make sure you have the `university_data_collector.py` script in the `app/` directory.

3. Set up your environment variables (especially `OPENAI_API_KEY`).

## Usage

### Basic Usage

Process all universities from the CSV file:
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv"
```

### Advanced Filtering

**Process only top 50 universities:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --limit 50
```

**Process universities ranked 1-100:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --start-rank 1 --end-rank 100
```

**Process only US universities:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --countries "United States"
```

**Process universities from multiple countries:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --countries "United States" "United Kingdom" "Canada"
```

### Performance Tuning

**Set custom delay between requests (default: 5 seconds):**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --delay 10
```

**Run with parallel processing (default: 2 concurrent):**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --max-concurrent 5
```

**Set maximum retries for failed collections (default: 3):**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --max-retries 5
```

**Check network connectivity before starting:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --check-network
```

### Database Management

**Skip universities that already exist in the database:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --skip-existing
```

**Force collection even if university exists:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --force
```

**Clear duplicate universities from database:**
```bash
python3 clear_duplicates.py --remove
```

### Output Control

**Specify custom output file:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --output my_results.json
```

**Preview mode (see what will be processed without starting):**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --preview --limit 20
```

### API Key Configuration

**Pass API key via command line:**
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --openai-key "your-api-key-here"
```

**Or set environment variable:**
```bash
export OPENAI_API_KEY="your-api-key-here"
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv"
```

## Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `csv_file` | - | CSV file containing university data (required) |
| `--limit` | `-l` | Limit number of universities to process |
| `--start-rank` | `-s` | Start processing from this rank (inclusive) |
| `--end-rank` | `-e` | End processing at this rank (inclusive) |
| `--countries` | `-c` | Only process universities from these countries |
| `--delay` | `-d` | Delay between universities in seconds (default: 5) |
| `--output` | `-o` | Output JSON file name |
| `--openai-key` | - | OpenAI API key |
| `--no-save-progress` | - | Don't save progress checkpoints |
| `--preview` | - | Show preview without starting collection |
| `--skip-existing` | - | Skip universities already in database |
| `--force` | - | Force collection even if university exists |
| `--max-retries` | - | Maximum retries for failed collections (default: 3) |
| `--max-concurrent` | - | Maximum concurrent universities to process (default: 2) |
| `--check-network` | - | Check network connectivity before starting |

## CSV File Format

The script expects a CSV file with the following columns:
- `Rank` - University ranking
- `Name` - University name
- `Country` - University country
- `Student Population` - Number of students
- `Students to Staff Ratio` - Student-to-faculty ratio
- `International Students` - Percentage of international students
- `Female to Male Ratio` - Gender distribution
- `Overall Score` - University score
- `Year` - Year of the ranking

## Output Format

The script generates JSON files with the following structure:

```json
{
  "metadata": {
    "total_universities": 100,
    "successful_collections": 85,
    "failed_collections": 10,
    "skipped_collections": 5,
    "generated_at": "2024-01-01T12:00:00",
    "script_version": "1.0.0"
  },
  "results": [
    {
      "success": true,
      "university_name": "Stanford University",
      "confidence_score": 0.92,
      "data_collection_id": "collection_123",
      "source_urls": ["https://example.com/stanford"],
      "extracted_data": {
        "name": "Stanford University",
        "website": "https://www.stanford.edu",
        "city": "Stanford",
        "state": "California",
        "country": "United States",
        "student_population": 15596,
        "acceptance_rate": "4%",
        "programs": ["Computer Science", "Engineering"]
      },
      "csv_data": {
        "rank": 3,
        "country": "United States",
        "student_population": 15596,
        "overall_score": 93.9,
        "year": 2016
      }
    }
  ]
}
```

## Progress Checkpoints

The script automatically saves progress every 10 universities to files like:
- `output/progress_checkpoint_10.json`
- `output/progress_checkpoint_20.json`
- etc.

This allows you to resume from where you left off if the process is interrupted.

## Error Handling

The script handles various error scenarios gracefully:

- **Network errors**: Automatic retries with exponential backoff
- **Browser connection failures**: Isolated browser instances per university
- **Search engine blocking**: Multiple search strategies with fallbacks
- **API rate limits**: Respects delays between requests
- **Invalid data**: Skips problematic entries and continues
- **User interruption**: Gracefully stops after completing current university
- **Database conflicts**: Handles duplicate entries intelligently

## Search Strategy Hierarchy

The script uses multiple search strategies in order of reliability:

1. **Wikipedia & Academic Sources** - Most reliable, uses Wikipedia and academic databases
2. **Educational Databases** - Direct access to university ranking sites
3. **Google Search** - Enhanced anti-bot measures
4. **Direct URL Access** - Attempts direct university website access
5. **Bing Search** - Alternative search engine
6. **Knowledge-Based Fallback** - LLM-powered fallback using internal knowledge

## Logging

The script creates detailed logs in:
- `batch_university_collection.log` - Main log file
- Console output with rich formatting
- Network diagnostic logs when using `--check-network`

## Database Management

### Skip Existing Universities

The `--skip-existing` flag checks the database before processing each university:

```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" --skip-existing
```

This feature:
- Checks both `University` and `UniversityDataCollectionResult` tables
- Uses case-insensitive name matching
- Provides detailed statistics on skipped universities
- Can be overridden with `--force` flag

### Clear Duplicates

Use the dedicated duplicate cleanup script:

```bash
# Dry run to see what would be removed
python3 clear_duplicates.py

# Actually remove duplicates
python3 clear_duplicates.py --remove
```

The duplicate detection:
- Uses normalized name comparison
- Scores universities by data completeness
- Keeps the most complete record
- Provides detailed analysis before removal

## Test Mode

For testing the interface without using real browser tools, use the test script:

```bash
python3 test_batch_collector.py
```

This demonstrates the full interface using mock data.

## Examples

### Example 1: Process Top 20 US Universities with Parallel Processing
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" \
  --limit 20 \
  --countries "United States" \
  --max-concurrent 3 \
  --skip-existing \
  --delay 3 \
  --output top_20_us_universities.json
```

### Example 2: Process Universities Ranked 50-100 with Retry Logic
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" \
  --start-rank 50 \
  --end-rank 100 \
  --max-retries 5 \
  --max-concurrent 2 \
  --delay 5 \
  --output universities_50_100.json
```

### Example 3: Network Diagnostics and Preview
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" \
  --check-network \
  --preview \
  --countries "United Kingdom" "Canada" \
  --limit 10
```

### Example 4: Force Collection of Existing Universities
```bash
python3 batch_university_collector.py "THE World University Rankings 2016-2025.csv" \
  --force \
  --limit 5 \
  --max-concurrent 1
```

## Troubleshooting

### Common Issues

1. **"OpenAI API key is required"**
   - Set the `OPENAI_API_KEY` environment variable
   - Or pass it via `--openai-key` parameter

2. **"CSV file not found"**
   - Make sure the CSV file path is correct
   - Use absolute path if needed

3. **Browser connection errors**
   - These are expected if browser tools aren't properly configured
   - The script will try multiple search strategies
   - Use `--max-retries` to increase retry attempts

4. **Network connectivity issues**
   - Use `--check-network` to diagnose connectivity problems
   - Check DNS, HTTP, and HTTPS connectivity
   - Reduce `--max-concurrent` if experiencing timeouts

5. **Memory issues with large datasets**
   - Use `--limit` to process smaller batches
   - Increase delay between requests with `--delay`
   - Reduce `--max-concurrent` to lower memory usage

6. **Search engine blocking**
   - The script automatically tries multiple search strategies
   - If one fails, it falls back to others
   - Use `--delay` to be more respectful to servers

### Performance Tips

- Use `--max-concurrent 2-3` for optimal performance vs. reliability
- Use `--delay 10` for slower but more reliable processing
- Process in smaller batches with `--limit`
- Use `--skip-existing` to avoid re-processing
- Use `--check-network` before large runs
- Use `--no-save-progress` to reduce disk I/O
- Filter by country to focus on specific regions

### Network Optimization

- **Concurrent Processing**: Start with `--max-concurrent 2` and increase if stable
- **Retry Logic**: Use `--max-retries 3-5` for network resilience
- **Search Strategies**: The script automatically tries multiple strategies
- **Browser Isolation**: Each university gets its own browser instance
- **Rate Limiting**: Built-in delays prevent overwhelming servers

## Contributing

To extend the script:

1. Add new filtering options in the `load_universities_from_csv` method
2. Enhance the progress display in `update_progress_display`
3. Add new output formats in `save_progress`
4. Implement resume functionality using checkpoint files
5. Add new search strategies in `university_scraper.py`
6. Enhance duplicate detection algorithms

## License

This script is part of the university matching application project. 