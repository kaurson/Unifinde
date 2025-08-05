"""
Browser Tool using Playwright directly

This is an alternative implementation that uses Playwright directly instead of
the browser-use library to avoid dependency issues.
"""

import asyncio
import base64
import json
import logging
from typing import Generic, Optional, TypeVar, Any

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from pydantic import Field, field_validator, ConfigDict
from pydantic_core.core_schema import ValidationInfo

from .base import BaseTool, ToolResult
from .web_search import WebSearch
from ..llm import LLM
from ..config import load_config

logger = logging.getLogger(__name__)

_BROWSER_DESCRIPTION = """\
A powerful browser automation tool that allows interaction with web pages through various actions.
* This tool provides commands for controlling a browser session, navigating web pages, and extracting information
* It maintains state across calls, keeping the browser session alive until explicitly closed
* Use this when you need to browse websites, fill forms, click buttons, extract content, or perform web searches
* Each action requires specific parameters as defined in the tool's dependencies

Key capabilities include:
* Navigation: Go to specific URLs, go back, search the web, or refresh pages
* Interaction: Click elements, input text, select from dropdowns, send keyboard commands
* Scrolling: Scroll up/down by pixel amount or scroll to specific text
* Content extraction: Extract and analyze content from web pages based on specific goals
* Tab management: Switch between tabs, open new tabs, or close tabs

Note: When using element indices, refer to the numbered elements shown in the current browser state.
"""

Context = TypeVar("Context")


class BrowserToolPlaywright(BaseTool, Generic[Context]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    name: str = "browser_tool"
    description: str = _BROWSER_DESCRIPTION
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "go_to_url",
                    "click_element",
                    "input_text",
                    "scroll_down",
                    "scroll_up",
                    "scroll_to_text",
                    "send_keys",
                    "get_dropdown_options",
                    "select_dropdown_option",
                    "go_back",
                    "web_search",
                    "wait",
                    "extract_content",
                    "switch_tab",
                    "open_tab",
                    "close_tab",
                ],
                "description": "The browser action to perform",
            },
            "url": {
                "type": "string",
                "description": "URL for 'go_to_url' or 'open_tab' actions",
            },
            "index": {
                "type": "integer",
                "description": "Element index for 'click_element', 'input_text', 'get_dropdown_options', or 'select_dropdown_option' actions",
            },
            "text": {
                "type": "string",
                "description": "Text for 'input_text', 'scroll_to_text', or 'select_dropdown_option' actions",
            },
            "scroll_amount": {
                "type": "integer",
                "description": "Pixels to scroll (positive for down, negative for up) for 'scroll_down' or 'scroll_up' actions",
            },
            "tab_id": {
                "type": "integer",
                "description": "Tab ID for 'switch_tab' action",
            },
            "query": {
                "type": "string",
                "description": "Search query for 'web_search' action",
            },
            "goal": {
                "type": "string",
                "description": "Extraction goal for 'extract_content' action",
            },
            "keys": {
                "type": "string",
                "description": "Keys to send for 'send_keys' action",
            },
            "seconds": {
                "type": "integer",
                "description": "Seconds to wait for 'wait' action",
            },
        },
        "required": ["action"],
        "dependencies": {
            "go_to_url": ["url"],
            "click_element": ["index"],
            "input_text": ["index", "text"],
            "switch_tab": ["tab_id"],
            "open_tab": ["url"],
            "scroll_down": ["scroll_amount"],
            "scroll_up": ["scroll_amount"],
            "scroll_to_text": ["text"],
            "send_keys": ["keys"],
            "get_dropdown_options": ["index"],
            "select_dropdown_option": ["index", "text"],
            "go_back": [],
            "web_search": ["query"],
            "wait": ["seconds"],
            "extract_content": ["goal"],
        },
    }

    lock: asyncio.Lock = Field(default_factory=asyncio.Lock)
    playwright: Optional[Any] = Field(default=None, exclude=True)
    browser: Optional[Browser] = Field(default=None, exclude=True)
    context: Optional[BrowserContext] = Field(default=None, exclude=True)
    page: Optional[Page] = Field(default=None, exclude=True)
    web_search_tool: WebSearch = Field(default_factory=WebSearch, exclude=True)

    # Context for generic functionality
    tool_context: Optional[Context] = Field(default=None, exclude=True)

    llm: Optional[LLM] = Field(default_factory=LLM)

    @field_validator("parameters", mode="before")
    def validate_parameters(cls, v: dict, info: ValidationInfo) -> dict:
        if not v:
            raise ValueError("Parameters cannot be empty")
        return v

    async def _ensure_browser_initialized(self) -> Page:
        """Ensure browser and context are initialized."""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
        
        if self.browser is None:
            # Load configuration
            config = load_config()
            
            browser_args = []
            if config.browser_config and config.browser_config.disable_security:
                browser_args.extend([
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ])
            
            if config.browser_config and config.browser_config.extra_chromium_args:
                browser_args.extend(config.browser_config.extra_chromium_args)
            
            headless = True
            if config.browser_config:
                headless = config.browser_config.headless
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=browser_args
            )
        
        if self.context is None:
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
        
        return self.page

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        index: Optional[int] = None,
        text: Optional[str] = None,
        scroll_amount: Optional[int] = None,
        tab_id: Optional[int] = None,
        query: Optional[str] = None,
        goal: Optional[str] = None,
        keys: Optional[str] = None,
        seconds: Optional[int] = None,
        **kwargs,
    ) -> ToolResult:
        """
        Execute a specified browser action.

        Args:
            action: The browser action to perform
            url: URL for navigation or new tab
            index: Element index for click or input actions
            text: Text for input action or search query
            scroll_amount: Pixels to scroll for scroll action
            tab_id: Tab ID for switch_tab action
            query: Search query for Google search
            goal: Extraction goal for content extraction
            keys: Keys to send for keyboard actions
            seconds: Seconds to wait
            **kwargs: Additional arguments

        Returns:
            ToolResult with the action's output or error
        """
        async with self.lock:
            try:
                page = await self._ensure_browser_initialized()

                # Get max content length from config
                config = load_config()
                max_content_length = getattr(
                    config.browser_config, "max_content_length", 2000
                ) if config.browser_config else 2000

                # Navigation actions
                if action == "go_to_url":
                    if not url:
                        return ToolResult(
                            error="URL is required for 'go_to_url' action"
                        )
                    await page.goto(url)
                    await page.wait_for_load_state()
                    return ToolResult(output=f"Navigated to {url}")

                elif action == "go_back":
                    await page.go_back()
                    await page.wait_for_load_state()
                    return ToolResult(output="Navigated back")

                elif action == "refresh":
                    await page.reload()
                    await page.wait_for_load_state()
                    return ToolResult(output="Refreshed current page")

                elif action == "web_search":
                    if not query:
                        return ToolResult(
                            error="Query is required for 'web_search' action"
                        )
                    # Navigate to Google and perform search
                    await page.goto("https://www.google.com")
                    await page.wait_for_load_state()
                    
                    # Find and fill search box
                    search_input = page.locator('input[name="q"]')
                    await search_input.fill(query)
                    await search_input.press("Enter")
                    await page.wait_for_load_state()
                    
                    return ToolResult(output=f"Performed web search for: {query}")

                # Element interaction actions
                elif action == "click_element":
                    if index is None:
                        return ToolResult(
                            error="Index is required for 'click_element' action"
                        )
                    # Get all clickable elements
                    elements = await page.query_selector_all("a, button, input[type='submit'], [role='button']")
                    if index < len(elements):
                        await elements[index].click()
                        return ToolResult(output=f"Clicked element at index {index}")
                    else:
                        return ToolResult(error=f"Element with index {index} not found")

                elif action == "input_text":
                    if index is None or not text:
                        return ToolResult(
                            error="Index and text are required for 'input_text' action"
                        )
                    # Get all input elements
                    elements = await page.query_selector_all("input, textarea")
                    if index < len(elements):
                        await elements[index].fill(text)
                        return ToolResult(output=f"Input '{text}' into element at index {index}")
                    else:
                        return ToolResult(error=f"Element with index {index} not found")

                elif action == "scroll_down" or action == "scroll_up":
                    direction = 1 if action == "scroll_down" else -1
                    amount = scroll_amount if scroll_amount is not None else 500
                    await page.evaluate(f"window.scrollBy(0, {direction * amount})")
                    return ToolResult(
                        output=f"Scrolled {'down' if direction > 0 else 'up'} by {amount} pixels"
                    )

                elif action == "scroll_to_text":
                    if not text:
                        return ToolResult(
                            error="Text is required for 'scroll_to_text' action"
                        )
                    try:
                        locator = page.get_by_text(text, exact=False)
                        await locator.scroll_into_view_if_needed()
                        return ToolResult(output=f"Scrolled to text: '{text}'")
                    except Exception as e:
                        return ToolResult(error=f"Failed to scroll to text: {str(e)}")

                elif action == "send_keys":
                    if not keys:
                        return ToolResult(
                            error="Keys are required for 'send_keys' action"
                        )
                    await page.keyboard.press(keys)
                    return ToolResult(output=f"Sent keys: {keys}")

                # Content extraction actions
                elif action == "extract_content":
                    if not goal:
                        return ToolResult(
                            error="Goal is required for 'extract_content' action"
                        )

                    import markdownify

                    content = markdownify.markdownify(await page.content())

                    prompt = f"""\
Your task is to extract the content of the page. You will be given a page and a goal, and you should extract all relevant information around this goal from the page. If the goal is vague, summarize the page. Respond in json format.
Extraction goal: {goal}

Page content:
{content[:max_content_length]}
"""
                    messages = [{"role": "system", "content": prompt}]

                    # Define extraction function schema
                    extraction_function = {
                        "type": "function",
                        "function": {
                            "name": "extract_content",
                            "description": "Extract specific information from a webpage based on a goal",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "extracted_content": {
                                        "type": "object",
                                        "description": "The content extracted from the page according to the goal",
                                        "properties": {
                                            "text": {
                                                "type": "string",
                                                "description": "Text content extracted from the page",
                                            },
                                            "metadata": {
                                                "type": "object",
                                                "description": "Additional metadata about the extracted content",
                                                "properties": {
                                                    "source": {
                                                        "type": "string",
                                                        "description": "Source of the extracted content",
                                                    }
                                                },
                                            },
                                        },
                                    }
                                },
                                "required": ["extracted_content"],
                            },
                        },
                    }

                    # Use LLM to extract content with required function calling
                    response = await self.llm.ask_tool(
                        messages,
                        tools=[extraction_function],
                        tool_choice="required",
                    )

                    if response and response.tool_calls:
                        args = json.loads(response.tool_calls[0].function.arguments)
                        extracted_content = args.get("extracted_content", {})
                        return ToolResult(
                            output=f"Extracted from page:\n{extracted_content}\n"
                        )

                    return ToolResult(output="No content was extracted from the page.")

                # Tab management actions
                elif action == "open_tab":
                    if not url:
                        return ToolResult(error="URL is required for 'open_tab' action")
                    new_page = await self.context.new_page()
                    await new_page.goto(url)
                    await new_page.wait_for_load_state()
                    return ToolResult(output=f"Opened new tab with {url}")

                elif action == "switch_tab":
                    if tab_id is None:
                        return ToolResult(
                            error="Tab ID is required for 'switch_tab' action"
                        )
                    pages = self.context.pages
                    if tab_id < len(pages):
                        await pages[tab_id].bring_to_front()
                        self.page = pages[tab_id]
                        return ToolResult(output=f"Switched to tab {tab_id}")
                    else:
                        return ToolResult(error=f"Tab {tab_id} not found")

                elif action == "close_tab":
                    if len(self.context.pages) > 1:
                        await self.page.close()
                        self.page = self.context.pages[0]
                        await self.page.bring_to_front()
                        return ToolResult(output="Closed current tab")
                    else:
                        return ToolResult(error="Cannot close the last tab")

                # Utility actions
                elif action == "wait":
                    seconds_to_wait = seconds if seconds is not None else 3
                    await asyncio.sleep(seconds_to_wait)
                    return ToolResult(output=f"Waited for {seconds_to_wait} seconds")

                else:
                    return ToolResult(error=f"Unknown action: {action}")

            except Exception as e:
                return ToolResult(error=f"Browser action '{action}' failed: {str(e)}")

    async def get_current_state(
        self, context: Optional[BrowserContext] = None
    ) -> ToolResult:
        """
        Get the current browser state as a ToolResult.
        """
        try:
            if not self.page:
                return ToolResult(error="Browser page not initialized")

            # Get page information
            url = self.page.url
            title = await self.page.title()

            # Take a screenshot
            screenshot = await self.page.screenshot(
                full_page=True, type="jpeg", quality=100
            )
            screenshot_b64 = base64.b64encode(screenshot).decode("utf-8")

            # Get all pages (tabs)
            pages = self.context.pages if self.context else []
            tabs = []
            for i, page in enumerate(pages):
                try:
                    tabs.append({
                        "id": i,
                        "title": await page.title(),
                        "url": page.url
                    })
                except:
                    tabs.append({
                        "id": i,
                        "title": "Unknown",
                        "url": "Unknown"
                    })

            # Get interactive elements
            elements = await self.page.query_selector_all("a, button, input, select, textarea")
            interactive_elements = []
            for i, element in enumerate(elements[:20]):  # Limit to first 20 elements
                try:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    text_content = await element.evaluate("el => el.textContent || el.value || ''")
                    interactive_elements.append(f"[{i}]{tag_name}: {text_content[:50]}")
                except:
                    interactive_elements.append(f"[{i}]unknown element")

            # Build the state info
            state_info = {
                "url": url,
                "title": title,
                "tabs": tabs,
                "help": "[0], [1], [2], etc., represent clickable indices corresponding to the elements listed. Clicking on these indices will navigate to or interact with the respective content behind them.",
                "interactive_elements": "\n".join(interactive_elements),
                "scroll_info": {
                    "pixels_above": 0,
                    "pixels_below": 0,
                    "total_height": 0,
                },
                "viewport_height": 800,
            }

            return ToolResult(
                output=json.dumps(state_info, indent=4, ensure_ascii=False),
                base64_image=screenshot_b64,
            )
        except Exception as e:
            return ToolResult(error=f"Failed to get browser state: {str(e)}")

    async def cleanup(self):
        """Clean up browser resources."""
        async with self.lock:
            if self.page is not None:
                await self.page.close()
                self.page = None
            if self.context is not None:
                await self.context.close()
                self.context = None
            if self.browser is not None:
                await self.browser.close()
                self.browser = None
            if self.playwright is not None:
                await self.playwright.stop()
                self.playwright = None

    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        if self.playwright is not None:
            try:
                asyncio.run(self.cleanup())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.cleanup())
                loop.close()

    @classmethod
    def create_with_context(cls, context: Context) -> "BrowserToolPlaywright[Context]":
        """Factory method to create a BrowserToolPlaywright with a specific context."""
        tool = cls()
        tool.tool_context = context
        return tool 