"""
Copyright (c) 2025 Jagadeeshgowdayt
This file is part of PDF-extractor-with-metadata, released under the MIT License.
See LICENSE in the project root for details.
"""
import re
import unicodedata

unsafe_chars = r"[\\/:*?\"<>|]"


def _clean_text(text: str) -> str:
    if text is None:
        return ""
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    # Trim
    text = text.strip()
    # Replace whitespace runs with single underscore
    text = re.sub(r"\s+", "_", text)
    # Remove filesystem-unsafe characters
    text = re.sub(unsafe_chars, "", text)
    # Remove other punctuation except - and _
    text = re.sub(r"[^\w\-\_]+", "", text)
    # Collapse multiple underscores
    text = re.sub(r"_+", "_", text)
    # Trim underscores
    text = text.strip("_")
    return text


def build_filename(course: str, school: str, page_no: int, ext: str = "jpeg", lowercase: bool = False) -> str:
    """Build normalized filename using the pattern {course}_{school}_{page_no}.{ext}

    Rules:
    - Replace spaces with underscore.
    - Remove unsafe characters.
    - Collapse multiple underscores.
    - Optionally lowercase the result.
    """
    course_part = _clean_text(course or "unknown")
    school_part = _clean_text(school or "unknown")
    name = f"{course_part}_{school_part}_{page_no}"
    if lowercase:
        name = name.lower()
    return f"{name}.{ext}"


if __name__ == "__main__":
    # Quick interactive demo
    examples = [
        ("Design and Analysis of Algorithms", "SOCSE", 1),
        ("  Intro to C++: notes ", " School of CS & Eng ", 12),
        (None, None, 3),
    ]
    for course, school, pg in examples:
        print(build_filename(course, school, pg))
