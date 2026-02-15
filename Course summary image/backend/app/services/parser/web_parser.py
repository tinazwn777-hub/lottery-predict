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
    """Web content parser using Playwright and BeautifulSoup"""

    def __init__(self):
        self.timeout = settings.REQUEST_TIMEOUT * 1000  # Convert to ms
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def parse(self, url: str) -> ParsedContent:
        """Main entry point for web parsing"""
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url

        # Fetch content
        html_content = await self._fetch_html(url)

        # Extract content
        title, main_content = self._extract_content(html_content)

        # Parse into structured format
        structured_content = self._parse_to_structured(title, main_content, url)

        return structured_content

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content using aiohttp (with fallback for Playwright)"""
        timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
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
            soup.find("div", id=re.compile(r"content|article|post|main", re.I))
        )

        if main_tag:
            main_content = main_tag.get_text(separator="\n", strip=True)
        else:
            # Fallback to body
            body = soup.find("body")
            if body:
                main_content = body.get_text(separator="\n", strip=True)

        # Clean content
        main_content = self._clean_content(main_content)

        return title.strip(), main_content.strip()

    def _clean_content(self, content: str) -> str:
        """Clean extracted content"""
        # Remove extra whitespace
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
        # Split content into sections
        sections = self._split_into_sections(content)

        # Create content items
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
                # Add as point
                point = line.lstrip("0123456789.、）)")
                if point:
                    current_section["points"].append(point)

        # Add last section
        if current_section["title"] or current_section["points"]:
            sections.append(current_section)

        # If no sections were created, create one from all content
        if not sections:
            # Split long content into chunks
            chunks = self._chunk_content(content)
            for i, chunk in enumerate(chunks):
                sections.append({
                    "title": f"第{i + 1}部分",
                    "points": [chunk]
                })

        return sections[:6]  # Limit to 6 sections for image layout

    def _chunk_content(self, content: str, max_chars: int = 500) -> List[str]:
        """Split content into chunks of max_chars"""
        if len(content) <= max_chars:
            return [content] if content else []

        # Split by sentences or paragraphs
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
