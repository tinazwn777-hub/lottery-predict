"""Web content parser - 支持动态页面渲染"""
import os
import re
from urllib.parse import urlparse
from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from app.core.config import settings
from app.models.schemas import ParsedContent, ContentItem


class WebParser:
    """Web content parser - 支持静态和动态页面"""

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT * 1000
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def parse(self, url: str) -> ParsedContent:
        """Main entry point for web parsing"""
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url

        # Try dynamic rendering first (for SPA, Feishu, Notion, etc.)
        try:
            html_content = await self._fetch_with_playwright(url)
            if html_content and len(html_content) > 1000:
                title, main_content = self._extract_content(html_content)
                if main_content and len(main_content) > 100:
                    structured_content = self._parse_to_structured(title, main_content, url)
                    return structured_content
        except Exception as e:
            print(f"Playwright parsing failed: {e}")

        # Fallback to simple HTTP fetch
        try:
            html_content = await self._fetch_html(url)
            title, main_content = self._extract_content(html_content)
            structured_content = self._parse_to_structured(title, main_content, url)
            return structured_content
        except Exception as e:
            raise Exception(f"Failed to parse {url}: {e}")

    async def _fetch_with_playwright(self, url: str) -> str:
        """Fetch HTML using Playwright for dynamic pages"""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Wait for dynamic content
                await page.wait_for_timeout(2000)

                # Get page content
                html = await page.content()
                await browser.close()

                return html
        except ImportError:
            raise Exception("Playwright not installed")
        except Exception as e:
            raise Exception(f"Playwright error: {e}")

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content using aiohttp"""
        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
        async with aiohttp.ClientSession(timeout=timeout, headers=self.headers) as session:
            async with session.get(url) as response:
                if response.status >= 400:
                    raise Exception(f"Failed to fetch URL: {response.status}")
                html = await response.text()
                return html

    def _extract_content(self, html: str) -> tuple:
        """Extract title and main content from HTML"""
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title = ""
        if soup.title:
            title = soup.title.string or ""
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        else:
            og_title = soup.find("meta", property="og:title")
            if og_title:
                title = og_title.get("content", "")

        # Remove unwanted elements
        for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # Extract main content
        main_content = ""

        # Try to find main content area
        main_tag = (
            soup.find("main") or
            soup.find("article") or
            soup.find("div", class_=re.compile(r"content|article|post|main", re.I)) or
            soup.find("div", id=re.compile(r"content|article|post|main", re.I)) or
            # Feishu specific selectors
            soup.find("div", class_=re.compile(r"wiki-content|page-content", re.I)) or
            soup.find("div", class_=re.compile(r"ne-iframe", re.I))
        )

        if main_tag:
            main_content = main_tag.get_text(separator="\n", strip=True)
        else:
            body = soup.find("body")
            if body:
                main_content = body.get_text(separator="\n", strip=True)

        main_content = self._clean_content(main_content)

        return title.strip(), main_content.strip()

    def _clean_content(self, content: str) -> str:
        """Clean extracted content"""
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip very short lines
            if len(line) < 10:
                continue
            # Skip lines that look like navigation
            if re.match(r"^(首页|导航|登录|注册|关于我们|联系我们)$", line):
                continue
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _parse_to_structured(self, title: str, content: str, url: str) -> ParsedContent:
        """Parse raw content into structured format"""
        sections = self._split_into_sections(content)

        items = []
        for i, section in enumerate(sections):
            item = ContentItem(
                title=section.get("title", f"第{i + 1}点"),
                points=section.get("points", []),
                order=i
            )
            items.append(item)

        return ParsedContent(
            title=title or "课程总结",
            items=items,
            source_url=url,
            source_title=title
        )

    def _split_into_sections(self, content: str) -> List[Dict]:
        """Split content into logical sections"""
        lines = content.split("\n")
        sections = []
        current_section = {"title": "", "points": []}

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            if len(line) < 100 and (line.endswith("：") or line.endswith(":") or
                                     re.match(r"^第[一二三四五六七八九十]+[章节段]|^[0-9]+[.:)]", line)):
                if current_section["title"] or current_section["points"]:
                    sections.append(current_section)
                current_section = {"title": line.rstrip("：:"), "points": []}
            else:
                point = line.lstrip("0123456789.、）)")
                if point:
                    current_section["points"].append(point)

        if current_section["title"] or current_section["points"]:
            sections.append(current_section)

        if not sections:
            chunks = self._chunk_content(content)
            for i, chunk in enumerate(chunks):
                sections.append({
                    "title": f"第{i + 1}部分",
                    "points": [chunk]
                })

        return sections[:6]

    def _chunk_content(self, content: str, max_chars: int = 500) -> List[str]:
        """Split content into chunks"""
        if len(content) <= max_chars:
            return [content] if content else []

        sentences = re.split(r"[。！？\n]", content)
        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chars:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "。"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks if chunks else [content[:max_chars]]
