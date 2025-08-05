# Browser Use Tool

This directory contains the tool system for the University Data Collection System, including the powerful BrowserUseTool for web automation.

## Overview

The BrowserUseTool provides comprehensive browser automation capabilities using the `browser-use` library. It allows you to:

- Navigate web pages
- Interact with forms and elements
- Extract content using LLM-powered analysis
- Manage multiple tabs
- Perform web searches
- Take screenshots and get page states

## Quick Start

### 1. Configuration

First, enable browser automation in your `.env` file:

```env
# Enable Browser Use Tool
BROWSER_USE_ENABLED=true
BROWSER_HEADLESS=true
BROWSER_DISABLE_SECURITY=true

# LLM Configuration (required for content extraction)
LLM_PROVIDER=openai
LLM_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4
```

### 2. Basic Usage

```python
import asyncio
from app.tool.browser_use_tool import BrowserUseTool

async def main():
    # Create browser tool instance
    browser_tool = BrowserUseTool()
    
    try:
        # Navigate to a website
        result = await browser_tool.execute(
            action="go_to_url",
            url="https://www.example.com"
        )
        print(f"Navigation result: {result.output}")
        
        # Get current page state
        state_result = await browser_tool.get_current_state()
        if state_result.is_success():
            state_data = json.loads(state_result.output)
            print(f"Current URL: {state_data.get('url')}")
            
    finally:
        await browser_tool.cleanup()

asyncio.run(main())
```

## Available Actions

### Navigation Actions

- **`go_to_url`**: Navigate to a specific URL
  ```python
  await browser_tool.execute(action="go_to_url", url="https://example.com")
  ```

- **`go_back`**: Navigate back in browser history
  ```python
  await browser_tool.execute(action="go_back")
  ```

- **`refresh`**: Refresh the current page
  ```python
  await browser_tool.execute(action="refresh")
  ```

### Element Interaction

- **`click_element`**: Click on an element by index
  ```python
  await browser_tool.execute(action="click_element", index=0)
  ```

- **`input_text`**: Input text into a form field
  ```python
  await browser_tool.execute(action="input_text", index=1, text="Hello World")
  ```

- **`send_keys`**: Send keyboard shortcuts
  ```python
  await browser_tool.execute(action="send_keys", keys="Enter")
  ```

### Scrolling

- **`scroll_down`**: Scroll down by pixels
  ```python
  await browser_tool.execute(action="scroll_down", scroll_amount=500)
  ```

- **`scroll_up`**: Scroll up by pixels
  ```python
  await browser_tool.execute(action="scroll_up", scroll_amount=300)
  ```

- **`scroll_to_text`**: Scroll to specific text
  ```python
  await browser_tool.execute(action="scroll_to_text", text="About Us")
  ```

### Content Extraction

- **`extract_content`**: Extract content using LLM analysis
  ```python
  result = await browser_tool.execute(
      action="extract_content",
      goal="Extract all contact information from this page"
  )
  ```

### Tab Management

- **`open_tab`**: Open a new tab
  ```python
  await browser_tool.execute(action="open_tab", url="https://example.com")
  ```

- **`switch_tab`**: Switch to a specific tab
  ```python
  await browser_tool.execute(action="switch_tab", tab_id=0)
  ```

- **`close_tab`**: Close the current tab
  ```python
  await browser_tool.execute(action="close_tab")
  ```

### Utility Actions

- **`wait`**: Wait for a specified number of seconds
  ```python
  await browser_tool.execute(action="wait", seconds=5)
  ```

- **`web_search`**: Perform a web search
  ```python
  await browser_tool.execute(action="web_search", query="MIT university")
  ```

## Advanced Features

### Getting Page State

The `get_current_state()` method provides comprehensive information about the current page:

```python
state_result = await browser_tool.get_current_state()
if state_result.is_success():
    state_data = json.loads(state_result.output)
    
    # Page information
    print(f"URL: {state_data['url']}")
    print(f"Title: {state_data['title']}")
    
    # Interactive elements
    print(f"Elements: {state_data['interactive_elements']}")
    
    # Screenshot (base64 encoded)
    if state_result.base64_image:
        # Save screenshot
        import base64
        with open("screenshot.jpg", "wb") as f:
            f.write(base64.b64decode(state_result.base64_image))
```

### Content Extraction with LLM

The content extraction feature uses your configured LLM to intelligently extract information:

```python
result = await browser_tool.execute(
    action="extract_content",
    goal="""Extract comprehensive university information including:
    1. Basic information (name, location, type)
    2. Mission and vision
    3. Academic programs
    4. Student statistics
    5. Contact information"""
)

if result.is_success():
    print("Extracted content:")
    print(result.output)
```

### Configuration Options

You can configure the browser behavior through environment variables:

```env
# Browser Configuration
BROWSER_USE_ENABLED=true
BROWSER_HEADLESS=true
BROWSER_DISABLE_SECURITY=true
BROWSER_CHROME_PATH=/path/to/chrome
BROWSER_EXTRA_ARGS=--no-sandbox,--disable-dev-shm-usage
BROWSER_MAX_CONTENT_LENGTH=2000

# Proxy Configuration (optional)
BROWSER_PROXY_SERVER=proxy.example.com:8080
BROWSER_PROXY_USERNAME=username
BROWSER_PROXY_PASSWORD=password
```

## Error Handling

The tool provides comprehensive error handling:

```python
result = await browser_tool.execute(action="click_element", index=999)
if not result.is_success():
    print(f"Error: {result.error}")
else:
    print(f"Success: {result.output}")
```

## Integration with University Data Collection

The BrowserUseTool is designed to work seamlessly with the University Data Collection System:

```python
from app.tool.browser_use_tool import BrowserUseTool

async def collect_university_data(university_name: str):
    browser_tool = BrowserUseTool()
    
    try:
        # Search for university
        await browser_tool.execute(
            action="web_search",
            query=f"{university_name} official website"
        )
        
        # Extract university information
        result = await browser_tool.execute(
            action="extract_content",
            goal=f"Extract comprehensive information about {university_name}"
        )
        
        return result.output
        
    finally:
        await browser_tool.cleanup()
```

## Examples

See `app/example_browser_use_tool.py` for comprehensive examples of all features.

## Dependencies

The BrowserUseTool requires:

- `browser-use>=0.1.0`
- `markdownify>=0.11.6`
- `pydantic>=2.5.0`
- LLM provider (OpenAI, Anthropic, or local)

## Troubleshooting

### Common Issues

1. **Browser not starting**: Check if `BROWSER_USE_ENABLED=true` is set
2. **Content extraction failing**: Verify LLM configuration and API keys
3. **Element not found**: Use `get_current_state()` to see available elements
4. **Timeout errors**: Increase wait times or check network connectivity

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

- The tool runs with `disable_security=true` by default for automation
- Use proxy settings for additional security if needed
- Always clean up browser resources with `cleanup()`
- Be cautious with sensitive data in extracted content 