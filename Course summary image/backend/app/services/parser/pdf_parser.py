import os
from typing import Optional, Dict, Any
import fitz  # PyMuPDF
from app.core.config import settings
from app.models.schemas import ParsedContent, ContentItem


class PDFParser:
    """PDF document parser using PyMuPDF"""

    def __init__(self):
        self.max_pages = 100  # Limit for MVP

    async def parse(self, file_path: str, filename: str = "") -> ParsedContent:
        """Main entry point for PDF parsing"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        # Extract text from PDF
        title, page_count, raw_text = self._extract_text(file_path)

        # Parse into structured format
        structured_content = self._parse_to_structured(
            title=title or filename or "PDF文档总结",
            content=raw_text,
            page_count=page_count
        )

        return structured_content

    def _extract_text(self, file_path: str) -> tuple:
        """Extract text from PDF"""
        doc = fitz.open(file_path)

        try:
            # Get title from first page
            title = ""
            if doc.page_count > 0:
                first_page = doc[0]
                title = first_page.get_text("text")
                # Try to find a proper title
                lines = title.split("\n")
                for line in lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if 10 < len(line) < 200 and not line.endswith("。"):  # Likely a title
                        title = line
                        break

            # Extract text from all pages (limited)
            all_text = []
            max_pages = min(doc.page_count, self.max_pages)

            for page_num in range(max_pages):
                page = doc[page_num]
                text = page.get_text("text")
                # Clean text
                text = self._clean_text(text)
                if text.strip():
                    all_text.append(text)

            full_text = "\n\n".join(all_text)

            # Check if PDF is image-based (scanned)
            if len(full_text.strip()) < 100:
                # This might be a scanned PDF
                full_text = self._extract_from_images(doc, max_pages)

            return title.strip(), doc.page_count, full_text

        finally:
            doc.close()

    def _extract_from_images(self, doc: fitz.Document, max_pages: int) -> str:
        """Extract text from image-based PDF pages"""
        # For MVP, we'll note that OCR is needed
        # In V2.0, this would use OCR (Tesseract or cloud API)
        text_parts = []

        for page_num in range(min(doc.page_count, max_pages)):
            page = doc[page_num]

            # Get images on page
            image_list = page.get_images(full=True)

            if image_list:
                text_parts.append(f"[第{page_num + 1}页包含图片，需要OCR识别]")

        return "\n".join(text_parts) if text_parts else "无法提取文本内容（可能是扫描版PDF）"

    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        import re

        # Remove page numbers
        text = re.sub(r'\s*\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove header/footer patterns
        text = re.sub(r'^.{1,20}\s*\d{1,3}\s*$', '', text, flags=re.MULTILINE)

        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _parse_to_structured(self, title: str, content: str, page_count: int) -> ParsedContent:
        """Parse raw content into structured format"""
        # Split content into sections
        sections = self._split_into_sections(content)

        # Create content items
        items = []
        for i, section in enumerate(sections):
            item = ContentItem(
                title=section.get("title", f"第{i + 1}章"),
                points=section.get("points", []),
                order=i
            )
            items.append(item)

        # Add metadata as first section if available
        metadata_points = [f"共 {page_count} 页"]

        return ParsedContent(
            title=title or "PDF文档总结",
            items=items,
            source_title=title
        )

    def _split_into_sections(self, content: str) -> list:
        """Split content into logical sections"""
        import re

        # Try to split by chapter headings
        chapter_patterns = [
            r'^第[一二三四五六七八九十百千]+[章节]',
            r'^[0-9]+[.）)]?\s*[A-Z][^.!?]*(?:章|节|部分)',
            r'^第[0-9]+[章节]|^Chapter\s+[0-9]',
            r'\n\n[A-Z][^.!?]*?(?=\n\n|$)',  # All caps paragraphs
        ]

        sections = []

        for pattern in chapter_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            if matches:
                # Found chapter-like headings
                for i, match in enumerate(matches):
                    start = match.end()
                    end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

                    section_text = content[start:end].strip()
                    points = self._text_to_points(section_text)

                    sections.append({
                        "title": match.group().strip(),
                        "points": points
                    })

                break

        # If no sections found, create sections by splitting content
        if not sections:
            sections = self._create_default_sections(content)

        return sections[:6]  # Limit to 6 sections

    def _text_to_points(self, text: str) -> list:
        """Convert text block to list of points"""
        import re

        points = []

        # Split by common delimiters
        sentences = re.split(r'[。！？\n]', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= 10:  # Filter short fragments
                # Remove leading numbers/bullets
                sentence = re.sub(r'^[0-9（）()\s.]+', '', sentence)
                if sentence:
                    points.append(sentence)

        return points

    def _create_default_sections(self, content: str) -> list:
        """Create sections by chunking content"""
        import re

        sections = []

        # Split into roughly equal parts
        chunks = []
        chunk_size = 2000  # Approximate characters per section

        words = content.split('\n\n')
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) < chunk_size:
                current_chunk += word + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        for i, chunk in enumerate(chunks):
            points = self._text_to_points(chunk)
            sections.append({
                "title": f"第{i + 1}部分",
                "points": points
            })

        return sections
