#!/usr/bin/env python3
"""
Archive Builder - Продвинутый построитель архивов
Создаёт архивы базы знаний с продвинутыми функциями:
- Инкрементальные и дифференциальные бэкапы
- Ротация старых архивов
- Верификация целостности (MD5/SHA256)
- Метаданные и manifest
- Прогресс и статистика
- Гибкие фильтры включения/исключения

Вдохновлено: tar, rsync, Time Machine, Duplicity
"""

from pathlib import Path
import zipfile
import tarfile
from datetime import datetime
import json
import hashlib
import shutil
import re


class AdvancedArchiveBuilder:
    """Продвинутый построитель архивов"""

    def __init__(self, root_dir="."):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.backups_dir = self.root_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)

        # Настройки ротации
        self.max_backups = 10  # Максимум архивов каждого типа

        # Паттерны исключения
        self.exclude_patterns = [
            r'\.git',
            r'__pycache__',
            r'\.pyc$',
            r'\.DS_Store',
            r'Thumbs\.db'
        ]

    def calculate_file_hash(self, file_path, algorithm='md5'):
        """Вычислить хеш файла"""
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    def should_exclude(self, file_path):
        """Проверить, нужно ли исключить файл"""
        file_str = str(file_path)

        for pattern in self.exclude_patterns:
            if re.search(pattern, file_str):
                return True

        return False

    def collect_files(self):
        """Собрать список файлов для архивации"""
        files = []

        for file_path in self.knowledge_dir.rglob("*"):
            if file_path.is_file() and not self.should_exclude(file_path):
                files.append(file_path)

        return files

    def get_file_metadata(self, file_path):
        """Получить метаданные файла"""
        stat = file_path.stat()

        return {
            'path': str(file_path.relative_to(self.root_dir)),
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'md5': self.calculate_file_hash(file_path, 'md5')
        }

    def create_manifest(self, files):
        """Создать manifest с метаданными"""
        manifest = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(files),
            'total_size': sum(f.stat().st_size for f in files),
            'files': []
        }

        print(f"   Создание manifest для {len(files)} файлов...")

        for file_path in files:
            manifest['files'].append(self.get_file_metadata(file_path))

        return manifest

    def load_previous_manifest(self, archive_type='zip'):
        """Загрузить предыдущий manifest для инкрементального бэкапа"""
        # Найти последний архив
        pattern = f"knowledge_backup_*_full.{archive_type}"
        archives = sorted(self.backups_dir.glob(pattern))

        if not archives:
            return None

        last_archive = archives[-1]
        manifest_path = last_archive.with_suffix('.manifest.json')

        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        return None

    def get_changed_files(self, files):
        """Получить измененные файлы для инкрементального бэкапа"""
        previous_manifest = self.load_previous_manifest()

        if not previous_manifest:
            # Нет предыдущего бэкапа - все файлы новые
            return files

        # Создать словарь: путь -> md5
        previous_hashes = {
            f['path']: f['md5']
            for f in previous_manifest.get('files', [])
        }

        changed_files = []

        for file_path in files:
            rel_path = str(file_path.relative_to(self.root_dir))
            current_md5 = self.calculate_file_hash(file_path, 'md5')

            # Файл новый или изменился
            if rel_path not in previous_hashes or previous_hashes[rel_path] != current_md5:
                changed_files.append(file_path)

        return changed_files

    def create_zip(self, backup_type='full', compression_level=zipfile.ZIP_DEFLATED):
        """Создать ZIP архив"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"knowledge_backup_{timestamp}_{backup_type}.zip"
        archive_path = self.backups_dir / archive_name

        print(f"📦 Создание ZIP архива ({backup_type})...\n")

        # Собрать файлы
        all_files = self.collect_files()

        if backup_type == 'incremental':
            files_to_backup = self.get_changed_files(all_files)
            print(f"   Инкрементальный бэкап: {len(files_to_backup)} измененных из {len(all_files)}")
        else:
            files_to_backup = all_files
            print(f"   Полный бэкап: {len(files_to_backup)} файлов")

        if not files_to_backup:
            print("   ⚠️  Нет измененных файлов для бэкапа")
            return None

        # Создать manifest
        manifest = self.create_manifest(files_to_backup)

        # Создать архив
        with zipfile.ZipFile(archive_path, 'w', compression_level) as zipf:
            for i, file_path in enumerate(files_to_backup, 1):
                arcname = file_path.relative_to(self.root_dir)
                zipf.write(file_path, arcname)

                if i % 10 == 0 or i == len(files_to_backup):
                    print(f"   Прогресс: {i}/{len(files_to_backup)} файлов...", end='\r')

            # Добавить manifest в архив
            manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2)
            zipf.writestr('manifest.json', manifest_json)

        print()  # Новая строка после прогресса

        # Сохранить manifest отдельно для инкрементальных бэкапов
        manifest_path = archive_path.with_suffix('.manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # Статистика
        file_size = archive_path.stat().st_size / 1024  # KB
        compression_ratio = (manifest['total_size'] / archive_path.stat().st_size) if archive_path.stat().st_size > 0 else 0

        print(f"✅ ZIP архив: {archive_path.name}")
        print(f"   Размер: {file_size:.1f} KB")
        print(f"   Степень сжатия: {compression_ratio:.2f}x")
        print(f"   Файлов: {len(files_to_backup)}")
        print(f"   MD5: {self.calculate_file_hash(archive_path, 'md5')}")

        # Верификация
        if self.verify_archive(archive_path, 'zip'):
            print(f"   ✅ Верификация пройдена")
        else:
            print(f"   ❌ Ошибка верификации!")

        return archive_path

    def create_tar_gz(self, backup_type='full', compression_level=9):
        """Создать TAR.GZ архив"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_name = f"knowledge_backup_{timestamp}_{backup_type}.tar.gz"
        archive_path = self.backups_dir / archive_name

        print(f"\n📦 Создание TAR.GZ архива ({backup_type})...\n")

        # Собрать файлы
        all_files = self.collect_files()

        if backup_type == 'incremental':
            files_to_backup = self.get_changed_files(all_files)
            print(f"   Инкрементальный бэкап: {len(files_to_backup)} измененных из {len(all_files)}")
        else:
            files_to_backup = all_files
            print(f"   Полный бэкап: {len(files_to_backup)} файлов")

        if not files_to_backup:
            print("   ⚠️  Нет измененных файлов для бэкапа")
            return None

        # Создать manifest
        manifest = self.create_manifest(files_to_backup)

        # Создать архив
        with tarfile.open(archive_path, f'w:gz', compresslevel=compression_level) as tarf:
            for i, file_path in enumerate(files_to_backup, 1):
                arcname = file_path.relative_to(self.root_dir)
                tarf.add(file_path, arcname=arcname)

                if i % 10 == 0 or i == len(files_to_backup):
                    print(f"   Прогресс: {i}/{len(files_to_backup)} файлов...", end='\r')

        print()  # Новая строка после прогресса

        # Сохранить manifest
        manifest_path = archive_path.with_suffix('.manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        # Статистика
        file_size = archive_path.stat().st_size / 1024  # KB
        compression_ratio = (manifest['total_size'] / archive_path.stat().st_size) if archive_path.stat().st_size > 0 else 0

        print(f"✅ TAR.GZ архив: {archive_path.name}")
        print(f"   Размер: {file_size:.1f} KB")
        print(f"   Степень сжатия: {compression_ratio:.2f}x")
        print(f"   Файлов: {len(files_to_backup)}")
        print(f"   MD5: {self.calculate_file_hash(archive_path, 'md5')}")

        return archive_path

    def verify_archive(self, archive_path, archive_type='zip'):
        """Проверить целостность архива"""
        try:
            if archive_type == 'zip':
                with zipfile.ZipFile(archive_path, 'r') as zipf:
                    # testzip() возвращает имя первого битого файла или None
                    return zipf.testzip() is None
            elif archive_type in ['tar.gz', 'tar']:
                with tarfile.open(archive_path, 'r:*') as tarf:
                    # Попробовать прочитать все члены
                    for member in tarf.getmembers():
                        pass
                    return True
        except:
            return False

    def rotate_backups(self, archive_type='zip'):
        """Ротация старых бэкапов"""
        print(f"\n🔄 Ротация бэкапов ({archive_type})...")

        # Найти все архивы данного типа
        pattern = f"knowledge_backup_*.{archive_type}"
        archives = sorted(self.backups_dir.glob(pattern))

        if len(archives) <= self.max_backups:
            print(f"   Архивов: {len(archives)}/{self.max_backups}")
            return

        # Удалить самые старые
        to_delete = archives[:-self.max_backups]

        for archive_path in to_delete:
            print(f"   Удаление старого архива: {archive_path.name}")
            archive_path.unlink()

            # Удалить manifest
            manifest_path = archive_path.with_suffix('.manifest.json')
            if manifest_path.exists():
                manifest_path.unlink()

        print(f"   Удалено: {len(to_delete)} архивов")
        print(f"   Осталось: {len(archives) - len(to_delete)}")

    def list_backups(self):
        """Список всех бэкапов"""
        print("\n📋 Список бэкапов:\n")

        archives = sorted(self.backups_dir.glob("knowledge_backup_*"))

        if not archives:
            print("   Нет бэкапов")
            return

        for archive_path in archives:
            if archive_path.suffix in ['.zip', '.gz']:
                stat = archive_path.stat()
                size_kb = stat.st_size / 1024
                modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                print(f"   {archive_path.name}")
                print(f"      Размер: {size_kb:.1f} KB")
                print(f"      Дата: {modified}")

                # Показать manifest если есть
                manifest_path = archive_path.with_suffix('.manifest.json')
                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    print(f"      Файлов: {manifest.get('total_files', 0)}")

                print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Advanced Archive Builder')
    parser.add_argument('-f', '--format', choices=['zip', 'tar.gz', 'both'], default='zip',
                       help='Формат архива')
    parser.add_argument('-t', '--type', choices=['full', 'incremental'], default='full',
                       help='Тип бэкапа')
    parser.add_argument('-l', '--list', action='store_true',
                       help='Показать список бэкапов')
    parser.add_argument('-r', '--rotate', action='store_true',
                       help='Выполнить ротацию старых бэкапов')
    parser.add_argument('--max-backups', type=int, default=10,
                       help='Максимум бэкапов при ротации')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    builder = AdvancedArchiveBuilder(root_dir)
    builder.max_backups = args.max_backups

    if args.list:
        builder.list_backups()
        return

    if args.format in ['zip', 'both']:
        builder.create_zip(backup_type=args.type)
        if args.rotate:
            builder.rotate_backups('zip')

    if args.format in ['tar.gz', 'both']:
        builder.create_tar_gz(backup_type=args.type)
        if args.rotate:
            builder.rotate_backups('tar.gz')


if __name__ == "__main__":
    main()
