"""Download a primary textbook linked in the assignment; never add it to Git."""
import argparse
import sys
from pathlib import Path

import httpx
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
BOOKS = {
    'bishop': ('Bishop-Pattern-Recognition-and-Machine-Learning-2006.pdf',
               'https://www.microsoft.com/en-us/research/wp-content/uploads/2006/01/Bishop-Pattern-Recognition-and-Machine-Learning-2006.pdf'),
    'mitchell': ('MachineLearningTomMitchell.pdf', 'https://www.cs.cmu.edu/~tom/files/MachineLearningTomMitchell.pdf'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--book', choices=BOOKS, default='bishop')
    args = parser.parse_args()
    name, url = BOOKS[args.book]
    destination = ROOT / 'knowledge' / 'ml' / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        temporary = destination.with_suffix('.pdf.part')
        try:
            print(f'Downloading from {url}')
            with httpx.stream('GET', url, follow_redirects=True, timeout=180) as response:
                response.raise_for_status()
                with temporary.open('wb') as out:
                    for chunk in response.iter_bytes():
                        out.write(chunk)
            if temporary.read_bytes()[:4] != b'%PDF':
                raise ValueError('The server did not return a PDF. Download a textbook manually instead.')
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
    reader = PdfReader(destination)
    text_pages = sum(bool((p.extract_text() or '').strip()) for p in reader.pages)
    print(f'Saved {destination}\nReadable pages: {text_pages}/{len(reader.pages)}')
    if text_pages < 5:
        sys.exit('This copy needs OCR. Try --book bishop or upload an OCR-processed copy.')
    if destination.stat().st_size > 25 * 1024 * 1024:
        print('This PDF exceeds the UI upload limit. Use scripts/ingest_book.py with the backend stopped.')
    else:
        print('Upload this file in Knowledge base, or use scripts/ingest_book.py with the backend stopped.')


if __name__ == '__main__':
    main()
