#!/usr/bin/env python3
"""
Поиск слова в конкордансе
"""

import json
import sys
from pathlib import Path


def search_concordance(word, concordance_file):
    """Поиск слова в конкордансе"""
    if not concordance_file.exists():
        print("❌ Конкорданс не найден. Запустите сначала:")
        print("   python tools/build_concordance.py")
        return

    with open(concordance_file, 'r', encoding='utf-8') as f:
        concordance = json.load(f)

    word_lower = word.lower()

    if word_lower not in concordance:
        print(f"❌ Слово '{word}' не найдено в конкордансе")

        # Предложить похожие слова
        similar = [w for w in concordance.keys() if word_lower in w][:10]
        if similar:
            print(f"\nПохожие слова:")
            for w in similar:
                print(f"  - {w}")
        return

    entries = concordance[word_lower]
    print(f"\n📖 Слово '{word}' найдено в {len(entries)} местах:\n")

    for i, entry in enumerate(entries[:30], 1):
        print(f"{i}. {entry['file']}:{entry['line']}")
        print(f"   {entry['context']}\n")

    if len(entries) > 30:
        print(f"   ...и ещё {len(entries) - 30} упоминаний")


def main():
    if len(sys.argv) < 2:
        print("Использование: python search_concordance.py <слово>")
        print("\nПримеры:")
        print("  python tools/search_concordance.py docker")
        print("  python tools/search_concordance.py python")
        print("  python tools/search_concordance.py холодильник")
        return

    word = sys.argv[1]

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    concordance_file = root_dir / "concordance.json"

    search_concordance(word, concordance_file)


if __name__ == "__main__":
    main()
