"""Question parsing service — extracts questions from .docx / .pdf / .txt files."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedOption:
    label: str  # A/B/C/D/E/F/G/H/I/J/K/L/M/N/O/P/Q/R/S/T/U/V/W/X/Y/Z
    text: str


@dataclass
class ParsedQuestion:
    text: str
    options: list[ParsedOption] = field(default_factory=list)
    correct_label: str | None = None
    image_bytes: bytes | None = None


def parse_file(file_path: str | Path) -> list[ParsedQuestion]:
    """Parse a document file and return a list of questions with optional images."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".docx":
        text, images = _extract_docx_with_images(path)
    elif suffix == ".pdf":
        text, images = _extract_pdf_with_images(path)
    else:
        text = path.read_text(encoding="utf-8")
        images = []

    questions = _parse_text(text)

    # Map extracted images to questions by line-position
    if images:
        _assign_images(questions, text, images)

    # Count questions with images for debugging
    img_count = sum(1 for q in questions if q.image_bytes)
    import logging
    logging.getLogger(__name__).info(
        "Parsed %d questions, %d with images (from %d raw images)",
        len(questions), img_count, len(images),
    )

    return questions


def _extract_docx(path: Path) -> str:
    """Extract text only from DOCX (used by answer key parsing)."""
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_docx_with_images(path: Path) -> tuple[str, list[tuple[int, bytes]]]:
    """Extract text and per-question cropped images from DOCX.

    Converts DOCX to PDF (via docx2pdf/Word), then uses the same per-question
    cropping logic as PDF. Falls back to inline image extraction if conversion
    fails (e.g. Word not installed).
    """
    # Try DOCX -> PDF conversion for per-question cropping
    import logging
    _logger = logging.getLogger(__name__)
    try:
        import tempfile
        from docx2pdf import convert

        tmp_pdf = os.path.join(tempfile.gettempdir(), f"eduquiz_conv_{id(path)}.pdf")
        _logger.info("Converting DOCX to PDF: %s", path.name)
        convert(str(path), tmp_pdf)

        if os.path.exists(tmp_pdf):
            try:
                # Use PDF text AND images from the same source so offsets match
                text, images = _extract_pdf_with_images(Path(tmp_pdf))
                _logger.info("Extracted %d images from converted PDF", len(images))
                return text, images
            finally:
                try:
                    os.unlink(tmp_pdf)
                except OSError:
                    pass
        else:
            _logger.warning("DOCX->PDF conversion produced no output file")
    except Exception as e:
        _logger.warning("docx2pdf conversion failed: %s — falling back to inline extraction", e)

    # Fallback: extract text and inline images from DOCX
    from docx import Document

    doc = Document(str(path))
    text = "\n".join(p.text for p in doc.paragraphs)

    images: list[tuple[int, bytes]] = []

    image_parts = {}
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            image_parts[rel.rId] = rel.target_part.blob

    nsmap = {
        "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    }

    for para_idx, para in enumerate(doc.paragraphs):
        for drawing in para._element.findall(".//wp:inline", nsmap):
            blip = drawing.find(".//a:blip", nsmap)
            if blip is not None:
                embed_id = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )
                if embed_id and embed_id in image_parts:
                    images.append((para_idx, image_parts[embed_id]))

    return text, images


def _extract_pdf(path: Path) -> str:
    """Extract text only from PDF (used by answer key parsing)."""
    from PyPDF2 import PdfReader

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_pdf_with_images(path: Path) -> tuple[str, list[tuple[int, bytes]]]:
    """Extract text and per-question cropped images from PDF.

    Returns (text, images) where images is a list of
    (line_offset, image_bytes) pairs — one cropped image per question.

    Uses PyMuPDF (fitz) text blocks to find question number positions,
    then crops the region for each question.
    Falls back to full-page images if fitz is unavailable.
    """
    import logging
    _logger = logging.getLogger(__name__)

    from PyPDF2 import PdfReader

    reader = PdfReader(str(path))
    pages_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages_text)

    images: list[tuple[int, bytes]] = []

    try:
        import fitz

        pdf_doc = fitz.open(str(path))
        _logger.info("Opened PDF with %d pages", len(pdf_doc))
        # Pattern to identify a question number at the start of a text span
        q_num_re = re.compile(r"^(\d{1,3})\s*[\.):\-]")

        line_offset = 0
        expected_next = 1  # Track expected question number across pages
        for page_idx, page_text in enumerate(pages_text):
            if page_idx >= len(pdf_doc):
                line_offset += page_text.count("\n") + 1
                continue

            page = pdf_doc[page_idx]
            dpi = 200
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)

            # Render full page as high-res image
            pix = page.get_pixmap(matrix=mat)
            full_img_bytes = pix.tobytes("png")

            # Use fitz text blocks to find question number positions directly
            # get_text("dict") gives us lines with their bounding boxes
            q_positions: list[tuple[int, float]] = []  # (q_num, y0)

            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
            for block in blocks:
                if block["type"] != 0:  # skip image blocks
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        span_text = span["text"].strip()
                        # Match question number at start of span text
                        m = q_num_re.match(span_text)
                        if m:
                            q_num = int(m.group(1))
                            if 1 <= q_num <= 200:
                                bbox = span["bbox"]
                                q_positions.append((q_num, bbox[1]))

            # Sort by Y position (top to bottom), then deduplicate
            q_positions.sort(key=lambda x: x[1])
            seen_nums: set[int] = set()
            deduped: list[tuple[int, float]] = []
            for q_num, y0 in q_positions:
                if q_num not in seen_nums:
                    seen_nums.add(q_num)
                    deduped.append((q_num, y0))
            q_positions = deduped

            # Filter: keep sequential question numbers, continuing from previous pages
            # This removes false positives (e.g. numbers in option text)
            if q_positions:
                # Use expected_next from previous page (or start from 1)
                if expected_next == 1:
                    # First page: find q_num=1 to start
                    start_idx = 0
                    for idx, (q_num, _) in enumerate(q_positions):
                        if q_num == 1:
                            start_idx = idx
                            break
                else:
                    # Continuation page: start from beginning
                    start_idx = 0

                # From start, keep only sequential numbers
                filtered: list[tuple[int, float]] = []
                expected = expected_next
                for q_num, y0 in q_positions[start_idx:]:
                    if q_num == expected:
                        filtered.append((q_num, y0))
                        expected += 1
                    elif q_num > expected:
                        # Allow small gaps (up to 2 missing)
                        if q_num <= expected + 2:
                            filtered.append((q_num, y0))
                            expected = q_num + 1
                        # If this is a continuation page and number is reasonable
                        elif expected_next > 1 and q_num >= expected_next:
                            filtered.append((q_num, y0))
                            expected = q_num + 1
                q_positions = filtered
                # Update expected_next for the next page
                if filtered:
                    expected_next = filtered[-1][0] + 1

            _logger.info("Page %d: found %d question positions", page_idx, len(q_positions))

            # Crop each question region from the rendered page image
            if q_positions:
                from io import BytesIO
                from PIL import Image

                full_img = Image.open(BytesIO(full_img_bytes))
                img_w, img_h = full_img.size

                for i, (q_num, y0) in enumerate(q_positions):
                    crop_top = max(0, int(y0 * zoom) - 3)

                    if i + 1 < len(q_positions):
                        crop_bottom = int(q_positions[i + 1][1] * zoom) - 3
                    else:
                        crop_bottom = img_h

                    crop_bottom = min(crop_bottom, img_h)

                    if crop_top >= crop_bottom:
                        continue

                    # Ensure minimum height of 50px for Telegram compatibility
                    if crop_bottom - crop_top < 50:
                        crop_bottom = min(crop_top + 50, img_h)
                    if crop_top >= crop_bottom:
                        continue

                    cropped = full_img.crop((0, crop_top, img_w, crop_bottom))

                    # Resize to fit Telegram photo limits (max width 800px)
                    # and convert to JPEG for smaller file size
                    max_w = 800
                    if cropped.width > max_w:
                        ratio = max_w / cropped.width
                        new_h = max(50, int(cropped.height * ratio))
                        cropped = cropped.resize(
                            (max_w, new_h), Image.LANCZOS
                        )

                    # Telegram requires aspect ratio between 1:20 and 20:1
                    # and w+h >= 200. If too flat, add white padding below.
                    w, h = cropped.size
                    if h > 0 and w / h > 19:
                        needed_h = max(int(w / 19) + 1, 50)
                        if w + needed_h < 200:
                            needed_h = 200 - w
                        from PIL import Image as _PILImage
                        padded = _PILImage.new("RGB", (w, needed_h), (255, 255, 255))
                        padded.paste(cropped.convert("RGB"), (0, 0))
                        cropped = padded
                    elif w + h < 200:
                        needed_h = 200 - w
                        from PIL import Image as _PILImage
                        padded = _PILImage.new("RGB", (w, needed_h), (255, 255, 255))
                        padded.paste(cropped.convert("RGB"), (0, 0))
                        cropped = padded

                    # Ensure minimum dimensions for Telegram
                    if cropped.width < 10 or cropped.height < 10:
                        continue

                    # Convert to RGB for JPEG (remove alpha channel)
                    if cropped.mode in ("RGBA", "P"):
                        cropped = cropped.convert("RGB")

                    buf = BytesIO()
                    cropped.save(buf, format="JPEG", quality=90)
                    img_bytes = buf.getvalue()

                    if img_bytes and len(img_bytes) > 200:
                        # Store (q_num, img_bytes) for direct index mapping
                        images.append((q_num, img_bytes))
            elif len(full_img_bytes) > 500:
                # No question numbers found — use whole page image (with offset 0)
                images.append((0, full_img_bytes))

            line_offset += page_text.count("\n") + 1

        pdf_doc.close()
    except ImportError:
        pass  # fitz not available — text-only

    return text, images


# ── Text parsing strategies ─────────────────────────────────

_OPTION_RE = re.compile(r"^\s*([A-Za-z])\s*[\.):\-]\s*(.+)$")
_QUESTION_NUM_RE = re.compile(r"^\s*(\d{1,3})\s*[\.):\-]\s*(.+)$")
_CORRECT_RE = re.compile(r"[✅✔✓\*]|\(correct\)|\(to'g'ri\)|\(тўғри\)", re.IGNORECASE)

# Matches option markers anywhere in a line (not just at the start)
_INLINE_OPT_MARKER_RE = re.compile(r"([A-Za-z])\s*[\.):\-]")


def _expand_inline_options(lines: list[str]) -> list[str]:
    """Split lines that contain multiple inline options into separate lines.

    Example input line:  "A) 22        B) 16     C) 32      D) 8"
    Output lines:        ["A) 22", "B) 16", "C) 32", "D) 8"]

    If a line has text before the first option marker, it is preserved
    as a separate line (treated as question text later).
    """
    result: list[str] = []
    for line in lines:
        markers = list(_INLINE_OPT_MARKER_RE.finditer(line))
        if len(markers) <= 1:
            # 0 or 1 marker — nothing to split
            result.append(line)
            continue

        first_start = markers[0].start()

        # Preserve any text before the first marker as its own line
        if first_start > 0 and line[:first_start].strip():
            result.append(line[:first_start].rstrip())

        # Split at each marker boundary
        for i, m in enumerate(markers):
            start = m.start()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(line)
            result.append(line[start:end].strip())

    return result


def _parse_text(text: str) -> list[ParsedQuestion]:
    """Split raw text into questions using numbered-list + option heuristics."""
    # Normalize
    t = text.replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # Strategy 1: Split by numbered list "1. ...", "1) ..."
    parts = re.split(r"(?:^|\n)\s*\d{1,3}[\.\\)]\s+", t)

    if len(parts) <= 1:
        # Fallback: split by double newline blocks
        blocks = [b.strip() for b in t.split("\n\n") if b.strip()]
    else:
        blocks = [b.strip() for b in parts[1:] if b.strip()]  # skip prefix

    questions: list[ParsedQuestion] = []
    for block in blocks:
        q = _parse_block(block)
        if q and q.options:
            questions.append(q)
    return questions


def _assign_images(
    questions: list[ParsedQuestion],
    raw_text: str,
    images: list[tuple[int, bytes]],
) -> None:
    """Assign extracted images to the corresponding questions.

    For PDF/DOCX with cropping: each image has (q_num, img_bytes) where q_num
    is the detected question number (1-indexed). We assign directly by index.

    Falls back to 1:1 assignment if counts match.
    """
    if not questions or not images:
        return

    # Check if images contain question numbers (from PDF cropping)
    # q_num values are 1-indexed question numbers (or 0 for whole-page fallback)
    q_nums = [img[0] for img in images]
    has_q_nums = any(n > 0 for n in q_nums)

    if has_q_nums:
        # Direct assignment by question number
        for q_num, img_bytes in images:
            if q_num > 0 and q_num <= len(questions):
                q_idx = q_num - 1  # Convert to 0-indexed
                if questions[q_idx].image_bytes is None:
                    questions[q_idx].image_bytes = img_bytes
        return

    # Fast path: equal count — assign 1:1 in order (for DOCX inline images)
    if len(images) == len(questions):
        for q, (_, img_bytes) in zip(questions, images):
            if q.image_bytes is None:
                q.image_bytes = img_bytes

    # Build a map: question_index -> first line offset in raw_text
    t = raw_text.replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # Split by numbered list to find where each question starts
    parts = re.split(r"(?:^|\n)\s*\d{1,3}[\.\\)]\s+", t)
    if len(parts) <= 1:
        blocks = [b.strip() for b in t.split("\n\n") if b.strip()]
        block_offsets = []
        offset = 0
        for block in blocks:
            # Find where this block starts in the normalized text
            idx = t.find(block, offset)
            if idx == -1:
                idx = offset
            block_offsets.append(idx)
            offset = idx + len(block)
    else:
        # parts[0] is prefix before first numbered item
        block_offsets = []
        search_start = 0
        for part in parts[1:]:
            stripped = part.strip()
            if stripped:
                idx = t.find(stripped, search_start)
                if idx == -1:
                    idx = search_start
                block_offsets.append(idx)
                search_start = idx + len(stripped)

    # Convert line_offsets from images to character offsets in raw_text
    lines = t.split("\n")
    line_char_offsets = []
    char_pos = 0
    for line in lines:
        line_char_offsets.append(char_pos)
        char_pos += len(line) + 1  # +1 for \n

    # Map each image to the closest question
    for img_line_offset, img_bytes in images:
        # Convert line offset to character offset
        if img_line_offset < len(line_char_offsets):
            img_char_offset = line_char_offsets[img_line_offset]
        else:
            img_char_offset = len(t)

        # Find the question whose block_offset is <= img_char_offset
        # and is closest to it
        best_q_idx = 0
        best_dist = float("inf")
        for q_idx, q_offset in enumerate(block_offsets):
            if q_offset <= img_char_offset:
                dist = img_char_offset - q_offset
                if dist < best_dist:
                    best_dist = dist
                    best_q_idx = q_idx

        if best_q_idx < len(questions):
            # Assign image — first image wins if multiple map to same question
            if questions[best_q_idx].image_bytes is None:
                questions[best_q_idx].image_bytes = img_bytes


def _parse_block(block: str) -> ParsedQuestion | None:
    """Parse a single question block into text + options."""
    lines = block.strip().split("\n")
    # Pre-process: expand inline options (e.g. "A) 22  B) 16  C) 32  D) 8")
    lines = _expand_inline_options(lines)

    question_lines: list[str] = []
    options: list[ParsedOption] = []
    correct_label: str | None = None
    seen_labels: set[str] = set()

    for line in lines:
        m = _OPTION_RE.match(line)
        if m:
            label = m.group(1).upper()
            # Skip duplicate labels (e.g. two D's from OCR noise)
            if label in seen_labels:
                continue
            seen_labels.add(label)
            opt_text = m.group(2).strip()
            if _CORRECT_RE.search(opt_text):
                opt_text = _CORRECT_RE.sub("", opt_text).strip()
                correct_label = label
            options.append(ParsedOption(label=label, text=opt_text))
        else:
            if not options:  # still in question text
                question_lines.append(line)

    if not question_lines and not options:
        return None

    return ParsedQuestion(
        text="\n".join(question_lines).strip(),
        options=options,
        correct_label=correct_label,
    )


def split_questions(text: str) -> list[str]:
    """Simple splitter — returns raw question text blocks (no option parsing)."""
    t = text.replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t).strip()

    # Numbered list: "1. ...", "1) ..."
    parts = re.split(r"(?:^|\n)\s*(\d{1,3}[\.|\)])\s+", t)
    if len(parts) > 1:
        bodies = []
        for i in range(2, len(parts), 2):
            bodies.append(parts[i].strip())
        return [b for b in bodies if b]

    # Bullet-list fallback
    lines = [x.strip("•-\t ").strip() for x in t.split("\n") if x.strip()]
    return [x for x in lines if len(x) >= 5]


# ── Answer key parsing ──────────────────────────────────────

_ANSWER_LINE_RE = re.compile(
    r"^\s*(\d{1,3})\s*[\.\)\:\-]?\s*([A-Da-d])\b", re.MULTILINE
)


def parse_answer_key(file_path: str | Path) -> dict[int, str]:
    """Parse an answer key file and return {question_number: label} dict.

    Supports formats like:
        1. A    1) B    1: C    1-A    1 B
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".docx":
        text = _extract_docx(path)
    elif suffix == ".pdf":
        text = _extract_pdf(path)
    elif suffix in (".xlsx", ".xls"):
        text = _extract_xlsx(path)
    else:
        text = path.read_text(encoding="utf-8")
    return _parse_answer_text(text)


def _parse_answer_text(text: str) -> dict[int, str]:
    """Extract answer mappings from text."""
    answers: dict[int, str] = {}
    for match in _ANSWER_LINE_RE.finditer(text):
        q_num = int(match.group(1))
        label = match.group(2).upper()
        answers[q_num] = label
    return answers


def _extract_xlsx(path: Path) -> str:
    """Extract text from Excel file for answer key parsing."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(str(path), read_only=True)
        lines = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                for cell in row:
                    if cell is not None:
                        lines.append(str(cell))
        return "\n".join(lines)
    except Exception:
        return ""
