"""Index a local book without the HTTP upload limit. Stop the backend first."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.config import Settings
from backend.app.knowledge import KnowledgeBase
from backend.app.storage import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--role', choices=['ml', 'backend'], default='ml')
    args = parser.parse_args()
    settings = Settings()
    Store(settings.data_dir)
    kb = KnowledgeBase(settings)
    try:
        count = kb.ingest(args.path.name, args.path.read_bytes(), args.role, 'assignment textbook', max_bytes=100 * 1024 * 1024)
        print(f'Indexed {count} chunks using {kb.embedder.signature}. Start the backend now.')
    finally:
        kb.client.close()


if __name__ == '__main__':
    main()
