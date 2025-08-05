# LLM Configuration Guide

This guide explains how to configure different LLM providers for the University Data Collection System.

## Quick Setup

1. **Create configuration file:**
```bash
python -m app.main --setup
```

2. **Edit the `.env` file** with your API keys and settings

3. **Test the configuration:**
```bash
python -m app.main --list-fields
```

## Supported LLM Providers

### 1. OpenAI (GPT-4, GPT-3.5)

**Configuration:**
```env
LLM_PROVIDER=openai
LLM_API_KEY=sk-your-openai-api-key-here
LLM_MODEL=gpt-4
LLM_BASE_URL=
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
```

**Setup:**
1. Get an API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add your API key to the `.env` file
3. Choose your model (gpt-4, gpt-3.5-turbo, etc.)

**Example:**
```bash
python -m app.main --setup --llm-provider openai
```

### 2. Anthropic (Claude)

**Configuration:**
```env
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-your-anthropic-api-key-here
LLM_MODEL=claude-3-sonnet-20240229
LLM_BASE_URL=
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
```

**Setup:**
1. Get an API key from [Anthropic Console](https://console.anthropic.com/)
2. Add your API key to the `.env` file
3. Choose your model (claude-3-sonnet, claude-3-haiku, etc.)

**Example:**
```bash
python -m app.main --setup --llm-provider anthropic
```

### 3. Ollama (Local Models)

**Configuration:**
```env
LLM_PROVIDER=local
LLM_API_KEY=not-needed
LLM_MODEL=llama2
LLM_BASE_URL=http://localhost:11434/v1
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
```

**Setup:**
1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Start Ollama server: `ollama serve`

**Example:**
```bash
python -m app.main --setup --llm-provider ollama
```

### 4. Local OpenAI-Compatible API

**Configuration:**
```env
LLM_PROVIDER=local
LLM_API_KEY=not-needed
LLM_MODEL=gpt-4
LLM_BASE_URL=http://localhost:1234/v1
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=1000
```

**Setup:**
1. Run your local OpenAI-compatible server
2. Update the `LLM_BASE_URL` to point to your server
3. Set the appropriate model name

**Example:**
```bash
python -m app.main --setup --llm-provider local_openai
```

## Usage Examples

### Basic Usage with LLM Enhancement

```python
import asyncio
from app.main import UniversityDataCollector

async def main():
    collector = UniversityDataCollector()
    
    # Collect data with LLM enhancement
    result = await collector.collect_university_data(
        "MIT",
        fields=["basic_info", "academic"],
        use_llm=True  # Enable LLM enhancement
    )
    
    print(f"LLM Enhanced: {result['llm_enhanced']}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    
    collector.close()

asyncio.run(main())
```

### Command Line Usage

```bash
# Collect data with LLM enhancement (default)
python -m app.main --university "MIT" --fields basic_info academic

# Collect data without LLM enhancement
python -m app.main --university "MIT" --fields basic_info academic --no-llm

# Batch collection with LLM
python -m app.main --file universities.txt --fields all
```

### Programmatic Configuration

```python
from app.mcp_server import LLMConfig
from app.main import UniversityDataCollector

# Custom LLM configuration
llm_config = LLMConfig(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4",
    temperature=0.1,
    max_tokens=1000
)

# Initialize collector with custom config
collector = UniversityDataCollector(llm_config=llm_config)

# Update configuration at runtime
collector.update_llm_config(new_llm_config)
```

## Configuration Options

### LLM Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openai, anthropic, local) | openai |
| `LLM_API_KEY` | API key for the provider | None |
| `LLM_MODEL` | Model name to use | gpt-4 |
| `LLM_BASE_URL` | Custom base URL for local/self-hosted | None |
| `LLM_TEMPERATURE` | Creativity level (0.0-1.0) | 0.1 |
| `LLM_MAX_TOKENS` | Maximum response length | 1000 |
| `LLM_TIMEOUT` | Request timeout in seconds | 30 |

### Scraper Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `SCRAPER_HEADLESS` | Run browser in headless mode | true |
| `SCRAPER_TIMEOUT` | Page load timeout | 10 |
| `SCRAPER_DELAY` | Delay between requests | 2.0 |
| `SCRAPER_MAX_RETRIES` | Maximum retry attempts | 3 |

### Database Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `DATABASE_URL` | Database connection string | sqlite:///universities.db |
| `DATABASE_ECHO` | Log SQL queries | false |
| `DATABASE_POOL_SIZE` | Connection pool size | 10 |

## Troubleshooting

### Common Issues

1. **"LLM not available" error:**
   - Check your API key is correct
   - Verify the provider is supported
   - Ensure the model name is valid

2. **"Failed to import LLM library":**
   - Install required packages: `pip install openai anthropic`
   - Check your Python environment

3. **"API key not set":**
   - Add your API key to the `.env` file
   - Restart the application

4. **Local model not responding:**
   - Ensure Ollama is running: `ollama serve`
   - Check the model is downloaded: `ollama list`
   - Verify the base URL is correct

### Testing Your Configuration

```bash
# Test configuration
python -m app.main --list-fields

# Test with a simple request
python -m app.main --university "MIT" --fields basic_info --no-llm

# Test with LLM enhancement
python -m app.main --university "MIT" --fields basic_info
```

### Environment Variables Priority

1. Command line arguments
2. Environment variables
3. Default values

## Security Notes

- Never commit your `.env` file to version control
- Use environment variables in production
- Rotate API keys regularly
- Monitor API usage and costs

## Cost Optimization

- Use `LLM_MAX_TOKENS` to limit response length
- Set `LLM_TEMPERATURE` to 0.0 for more focused responses
- Consider using cheaper models for testing
- Monitor API usage in your provider's dashboard 