## Copyright & License

Copyright (c) 2025 Jagadeeshgowdayt

This project is open source under the MIT License. See LICENSE for details.
PDF extractor with metadata
==========================

This project downloads PDFs from UniVault search results, extracts metadata (title, school, etc.), and converts each PDF page to JPEG images using a normalized filename format.

Filename format
---------------
Each generated image filename follows the template:

    {course}_{school}_{page_no}.jpeg

Spaces are replaced by underscores. Unsafe filesystem characters are removed. Example:

    Design_and_Analysis_of_Algorithms_SOCSE_1.jpeg

Defaults
--------
- Image format: JPEG (quality 85)
- Metadata output: JSON lines (planned)
- PDF->image: PyMuPDF (no external poppler required)

Usage
-----
1. Install dependencies (use a venv):

```powershell
python -m pip install -r requirements.txt
```

2. Run the scaffold script (it's a starting point and contains a local test):

```powershell
python scripts\scrape_univault.py
```

Next steps
----------
  
- Add command-line options for max-results, image quality, lowercase filenames, and page limit.
- Add retries, rate limiting, and logging.
# PDF-extractor-with-metadata