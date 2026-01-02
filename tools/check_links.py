#!/usr/bin/env python3
"""
Dead Links Checker - Проверка битых ссылок
Находит несуществующие файлы и битые ссылки

Проверяет:
- Внутренние ссылки на файлы
- Якорные ссылки на заголовки
- Относительные пути
"""

from pathlib import Path
import re
import yaml


class LinkChecker:
    """Проверка ссылок"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.broken_links = []

    def extract_content(self, file_path):
        """Извлечь содержимое"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.match(r'^---\s*\n.*?\n---\s*\n(.*)', content, re.DOTALL)
            if match:
                return match.group(1)
        except:
            pass
        return None

    def extract_headings(self, content):
        """Извлечь заголовки для проверки якорей"""
        headings = []
        for line in content.split('\n'):
            match = re.match(r'^#{1,6}\s+(.+)$', line)
            if match:
                text = match.group(1).strip()
                # Создать якорь
                anchor = text.lower()
                anchor = re.sub(r'[^\w\s-]', '', anchor)
                anchor = re.sub(r'\s+', '-', anchor)
                anchor = re.sub(r'-+', '-', anchor)
                anchor = anchor.strip('-')
                headings.append(anchor)
        return headings

    def check_file(self, file_path):
        """Проверить ссылки в файле"""
        content = self.extract_content(file_path)
        if not content:
            return

        article_path = str(file_path.relative_to(self.root_dir))

        # Получить заголовки этого файла
        local_anchors = set(self.extract_headings(content))

        # Найти все ссылки
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for text, link in links:
            # Пропустить внешние ссылки
            if link.startswith('http'):
                continue

            # Разделить на файл и якорь
            if '#' in link:
                file_part, anchor_part = link.split('#', 1)
            else:
                file_part = link
                anchor_part = None

            # Проверить файл
            if file_part:
                # Разрешить относительный путь
                target = (file_path.parent / file_part).resolve()

                if not target.exists():
                    self.broken_links.append({
                        'article': article_path,
                        'link_text': text,
                        'link': link,
                        'type': 'broken_file',
                        'target': str(target.relative_to(self.root_dir)) if target.is_relative_to(self.root_dir) else str(target)
                    })

            # Проверить якорь
            if anchor_part:
                if file_part:
                    # Якорь в другом файле - читаем тот файл
                    target = (file_path.parent / file_part).resolve()
                    if target.exists():
                        target_content = self.extract_content(target)
                        if target_content:
                            target_anchors = set(self.extract_headings(target_content))
                            if anchor_part not in target_anchors:
                                self.broken_links.append({
                                    'article': article_path,
                                    'link_text': text,
                                    'link': link,
                                    'type': 'broken_anchor',
                                    'target': file_part,
                                    'anchor': anchor_part
                                })
                else:
                    # Якорь в текущем файле
                    if anchor_part not in local_anchors:
                        self.broken_links.append({
                            'article': article_path,
                            'link_text': text,
                            'link': link,
                            'type': 'broken_anchor',
                            'anchor': anchor_part
                        })

    def check_all(self):
        """Проверить все файлы"""
        print("🔗 Проверка ссылок...\n")

        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "INDEX.md":
                continue

            self.check_file(md_file)

        print(f"   Найдено битых ссылок: {len(self.broken_links)}\n")

    def generate_report(self):
        """Создать отчёт"""
        lines = []
        lines.append("# 🔗 Отчёт: Проверка ссылок\n\n")

        lines.append(f"**Найдено битых ссылок**: {len(self.broken_links)}\n\n")

        if not self.broken_links:
            lines.append("✅ Все ссылки работают!\n")
        else:
            # Группировать по типу
            by_type = {'broken_file': [], 'broken_anchor': []}

            for link in self.broken_links:
                link_type = link['type']
                by_type[link_type].append(link)

            # Битые файлы
            if by_type['broken_file']:
                lines.append(f"## ❌ Битые ссылки на файлы ({len(by_type['broken_file'])})\n\n")

                for link in by_type['broken_file']:
                    lines.append(f"### {link['article']}\n\n")
                    lines.append(f"- **Текст**: {link['link_text']}\n")
                    lines.append(f"- **Ссылка**: `{link['link']}`\n")
                    lines.append(f"- **Цель**: `{link['target']}`\n\n")

            # Битые якоря
            if by_type['broken_anchor']:
                lines.append(f"## ⚓ Битые якорные ссылки ({len(by_type['broken_anchor'])})\n\n")

                for link in by_type['broken_anchor']:
                    lines.append(f"### {link['article']}\n\n")
                    lines.append(f"- **Текст**: {link['link_text']}\n")
                    lines.append(f"- **Ссылка**: `{link['link']}`\n")
                    lines.append(f"- **Якорь**: `{link['anchor']}`\n")
                    if 'target' in link:
                        lines.append(f"- **Файл**: `{link['target']}`\n")
                    lines.append("\n")

        output_file = self.root_dir / "BROKEN_LINKS.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Отчёт: {output_file}")


def main():
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    checker = LinkChecker(root_dir)
    checker.check_all()
    checker.generate_report()


if __name__ == "__main__":
    main()
