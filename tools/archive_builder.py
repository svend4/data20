#!/usr/bin/env python3
"""
Archive Builder - Построитель архива
Создаёт полный архив базы знаний
"""

from pathlib import Path
import zipfile
import tarfile
from datetime import datetime


class ArchiveBuilder:
    """Построитель архива"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"

    def create_zip(self):
        """Создать ZIP архив"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"knowledge_backup_{timestamp}.zip"
        archive_path = self.root_dir / archive_name

        print(f"📦 Создание ZIP архива...\n")

        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for md_file in self.knowledge_dir.rglob("*.md"):
                arcname = md_file.relative_to(self.root_dir)
                zipf.write(md_file, arcname)

        file_size = archive_path.stat().st_size / 1024  # KB
        print(f"✅ ZIP архив: {archive_path} ({file_size:.1f} KB)")

        return archive_path

    def create_tar_gz(self):
        """Создать TAR.GZ архив"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"knowledge_backup_{timestamp}.tar.gz"
        archive_path = self.root_dir / archive_name

        print(f"📦 Создание TAR.GZ архива...\n")

        with tarfile.open(archive_path, 'w:gz') as tarf:
            tarf.add(self.knowledge_dir, arcname='knowledge')

        file_size = archive_path.stat().st_size / 1024  # KB
        print(f"✅ TAR.GZ архив: {archive_path} ({file_size:.1f} KB)")

        return archive_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Archive Builder')
    parser.add_argument('-f', '--format', choices=['zip', 'tar.gz', 'both'], default='zip',
                       help='Формат архива')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = ArchiveBuilder(root_dir)

    if args.format in ['zip', 'both']:
        builder.create_zip()

    if args.format in ['tar.gz', 'both']:
        builder.create_tar_gz()


if __name__ == "__main__":
    main()
