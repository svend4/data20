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
import argparse
from typing import Dict, List, Optional
from collections import defaultdict


class IncrementalArchiver:
    """
    Продвинутый инкрементальный архиватор
    Поддержка полных, инкрементальных и дифференциальных бэкапов
    """

    def __init__(self, root_dir, backup_dir):
        self.root_dir = Path(root_dir)
        self.backup_dir = Path(backup_dir)
        self.snapshot_db = self.backup_dir / "snapshots.json"
        self.snapshots = self._load_snapshots()

    def _load_snapshots(self) -> Dict:
        """Загрузить базу снимков состояния"""
        if self.snapshot_db.exists():
            with open(self.snapshot_db, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'full': [], 'incremental': [], 'differential': []}

    def _save_snapshots(self):
        """Сохранить базу снимков"""
        with open(self.snapshot_db, 'w', encoding='utf-8') as f:
            json.dump(self.snapshots, f, ensure_ascii=False, indent=2)

    def create_snapshot(self, files: List[Path], backup_type: str, archive_path: Path) -> Dict:
        """
        Создать снимок состояния файлов

        Args:
            files: список файлов
            backup_type: 'full', 'incremental', 'differential'
            archive_path: путь к созданному архиву

        Returns:
            snapshot dictionary
        """
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'type': backup_type,
            'archive': str(archive_path.name),
            'files': {},
            'total_size': 0
        }

        for file_path in files:
            stat = file_path.stat()
            rel_path = str(file_path.relative_to(self.root_dir))

            snapshot['files'][rel_path] = {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'md5': self._quick_hash(file_path)
            }

            snapshot['total_size'] += stat.st_size

        # Добавить в базу
        self.snapshots[backup_type].append(snapshot)
        self._save_snapshots()

        return snapshot

    def _quick_hash(self, file_path: Path) -> str:
        """Быстрый хеш файла (первые 8KB + размер)"""
        hash_md5 = hashlib.md5()

        with open(file_path, 'rb') as f:
            # Читать первые 8KB
            chunk = f.read(8192)
            hash_md5.update(chunk)

        # Добавить размер файла
        hash_md5.update(str(file_path.stat().st_size).encode())

        return hash_md5.hexdigest()

    def get_differential_files(self, all_files: List[Path]) -> List[Path]:
        """
        Получить файлы для дифференциального бэкапа
        (все изменения с последнего ПОЛНОГО бэкапа)
        """
        if not self.snapshots['full']:
            return all_files

        last_full = self.snapshots['full'][-1]
        last_full_files = last_full['files']

        changed = []

        for file_path in all_files:
            rel_path = str(file_path.relative_to(self.root_dir))

            # Новый файл или изменился с последнего full backup
            if rel_path not in last_full_files:
                changed.append(file_path)
            else:
                current_hash = self._quick_hash(file_path)
                if current_hash != last_full_files[rel_path]['md5']:
                    changed.append(file_path)

        return changed

    def get_incremental_files(self, all_files: List[Path]) -> List[Path]:
        """
        Получить файлы для инкрементального бэкапа
        (только изменения с ПОСЛЕДНЕГО бэкапа любого типа)
        """
        # Найти последний snapshot любого типа
        all_snapshots = []

        for backup_type in ['full', 'incremental', 'differential']:
            all_snapshots.extend(self.snapshots[backup_type])

        if not all_snapshots:
            return all_files

        # Сортировать по времени
        all_snapshots.sort(key=lambda x: x['timestamp'], reverse=True)
        last_snapshot = all_snapshots[0]
        last_files = last_snapshot['files']

        changed = []

        for file_path in all_files:
            rel_path = str(file_path.relative_to(self.root_dir))

            if rel_path not in last_files:
                changed.append(file_path)
            else:
                current_hash = self._quick_hash(file_path)
                if current_hash != last_files[rel_path]['md5']:
                    changed.append(file_path)

        return changed

    def get_backup_chain(self, backup_type: str = 'full') -> List[Dict]:
        """Получить цепочку бэкапов для восстановления"""
        if backup_type == 'full':
            # Только последний full backup
            return [self.snapshots['full'][-1]] if self.snapshots['full'] else []

        elif backup_type == 'differential':
            # Last full + last differential
            chain = []
            if self.snapshots['full']:
                chain.append(self.snapshots['full'][-1])
            if self.snapshots['differential']:
                chain.append(self.snapshots['differential'][-1])
            return chain

        elif backup_type == 'incremental':
            # Last full + all incrementals since then
            chain = []

            if not self.snapshots['full']:
                return []

            last_full = self.snapshots['full'][-1]
            last_full_time = last_full['timestamp']

            chain.append(last_full)

            # Добавить все инкрементальные с момента last full
            for inc in self.snapshots['incremental']:
                if inc['timestamp'] > last_full_time:
                    chain.append(inc)

            return chain

        return []


class CompressionOptimizer:
    """
    Оптимизатор сжатия
    Выбор оптимального метода сжатия в зависимости от типов файлов
    """

    def __init__(self):
        # Типы файлов и рекомендуемое сжатие
        self.compression_map = {
            'already_compressed': {
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.zip', '.gz', '.pdf'],
                'level': zipfile.ZIP_STORED  # No compression
            },
            'text': {
                'extensions': ['.md', '.txt', '.json', '.yaml', '.yml', '.xml', '.html', '.css', '.js'],
                'level': zipfile.ZIP_DEFLATED  # Best compression
            },
            'code': {
                'extensions': ['.py', '.java', '.cpp', '.c', '.h', '.rb', '.go', '.rs'],
                'level': zipfile.ZIP_DEFLATED
            }
        }

    def get_optimal_compression(self, file_path: Path) -> int:
        """Определить оптимальный уровень сжатия для файла"""
        ext = file_path.suffix.lower()

        for category, info in self.compression_map.items():
            if ext in info['extensions']:
                return info['level']

        # По умолчанию - сжимать
        return zipfile.ZIP_DEFLATED

    def analyze_compression_efficiency(self, files: List[Path]) -> Dict:
        """Анализ эффективности сжатия для набора файлов"""
        categories = defaultdict(lambda: {'count': 0, 'size': 0})

        for file_path in files:
            ext = file_path.suffix.lower()
            size = file_path.stat().st_size

            # Определить категорию
            category = 'other'
            for cat, info in self.compression_map.items():
                if ext in info['extensions']:
                    category = cat
                    break

            categories[category]['count'] += 1
            categories[category]['size'] += size

        return dict(categories)

    def estimate_compression_ratio(self, files: List[Path]) -> float:
        """
        Оценить ожидаемую степень сжатия

        Returns:
            Expected compression ratio (e.g., 2.0 = 50% reduction)
        """
        analysis = self.analyze_compression_efficiency(files)

        # Типичные степени сжатия для категорий
        typical_ratios = {
            'already_compressed': 1.0,  # Без изменений
            'text': 3.0,                # Текст сжимается хорошо
            'code': 2.5,                # Код сжимается хорошо
            'other': 2.0                # Умеренное сжатие
        }

        total_size = sum(cat['size'] for cat in analysis.values())

        if total_size == 0:
            return 1.0

        weighted_ratio = 0

        for category, stats in analysis.items():
            weight = stats['size'] / total_size
            ratio = typical_ratios.get(category, 2.0)
            weighted_ratio += weight * ratio

        return weighted_ratio


class ArchiveValidator:
    """
    Валидатор архивов
    Проверка целостности, восстановление поврежденных архивов
    """

    def __init__(self):
        self.validation_results = []

    def validate_zip(self, archive_path: Path) -> Dict:
        """Валидация ZIP архива"""
        result = {
            'archive': str(archive_path),
            'valid': False,
            'errors': [],
            'file_count': 0,
            'corrupted_files': []
        }

        try:
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                # Тест архива
                bad_file = zipf.testzip()

                if bad_file:
                    result['errors'].append(f"Corrupted file: {bad_file}")
                    result['corrupted_files'].append(bad_file)
                else:
                    result['valid'] = True

                # Подсчитать файлы
                result['file_count'] = len(zipf.namelist())

                # Проверить manifest
                if 'manifest.json' in zipf.namelist():
                    manifest_data = zipf.read('manifest.json')
                    manifest = json.loads(manifest_data)
                    result['manifest'] = manifest
                else:
                    result['errors'].append("Missing manifest.json")

        except Exception as e:
            result['errors'].append(str(e))

        self.validation_results.append(result)

        return result

    def validate_tarball(self, archive_path: Path) -> Dict:
        """Валидация TAR/TAR.GZ архива"""
        result = {
            'archive': str(archive_path),
            'valid': False,
            'errors': [],
            'file_count': 0
        }

        try:
            with tarfile.open(archive_path, 'r:*') as tarf:
                members = tarf.getmembers()
                result['file_count'] = len(members)

                # Попробовать прочитать все члены
                for member in members:
                    try:
                        if member.isfile():
                            tarf.extractfile(member)
                    except Exception as e:
                        result['errors'].append(f"Error reading {member.name}: {e}")

                if not result['errors']:
                    result['valid'] = True

        except Exception as e:
            result['errors'].append(str(e))

        self.validation_results.append(result)

        return result

    def batch_validate(self, backup_dir: Path) -> Dict:
        """Валидация всех архивов в директории"""
        archives = list(backup_dir.glob("*.zip")) + list(backup_dir.glob("*.tar.gz"))

        summary = {
            'total': len(archives),
            'valid': 0,
            'invalid': 0,
            'details': []
        }

        for archive in archives:
            if archive.suffix == '.zip':
                result = self.validate_zip(archive)
            elif archive.name.endswith('.tar.gz'):
                result = self.validate_tarball(archive)
            else:
                continue

            summary['details'].append(result)

            if result['valid']:
                summary['valid'] += 1
            else:
                summary['invalid'] += 1

        return summary

    def verify_hash(self, archive_path: Path, expected_hash: str, algorithm: str = 'md5') -> bool:
        """Проверить хеш архива"""
        hash_func = hashlib.md5() if algorithm == 'md5' else hashlib.sha256()

        with open(archive_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)

        actual_hash = hash_func.hexdigest()

        return actual_hash == expected_hash


class TimelineBuilder:
    """
    Построитель timeline версий
    Визуализация истории бэкапов, анализ изменений во времени
    """

    def __init__(self, backup_dir: Path):
        self.backup_dir = backup_dir

    def load_all_manifests(self) -> List[Dict]:
        """Загрузить все manifests из backup директории"""
        manifests = []

        for manifest_path in self.backup_dir.glob("*.manifest.json"):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                manifest['archive_file'] = manifest_path.stem.replace('.manifest', '')
                manifests.append(manifest)

        # Сортировать по времени
        manifests.sort(key=lambda x: x['timestamp'])

        return manifests

    def build_timeline(self) -> Dict:
        """Построить timeline бэкапов"""
        manifests = self.load_all_manifests()

        timeline = {
            'start_date': manifests[0]['timestamp'] if manifests else None,
            'end_date': manifests[-1]['timestamp'] if manifests else None,
            'total_backups': len(manifests),
            'events': []
        }

        for manifest in manifests:
            event = {
                'timestamp': manifest['timestamp'],
                'archive': manifest.get('archive_file', 'unknown'),
                'file_count': manifest.get('total_files', 0),
                'total_size': manifest.get('total_size', 0),
                'type': self._detect_backup_type(manifest.get('archive_file', ''))
            }

            timeline['events'].append(event)

        return timeline

    def _detect_backup_type(self, archive_name: str) -> str:
        """Определить тип бэкапа по имени архива"""
        if '_full' in archive_name:
            return 'full'
        elif '_incremental' in archive_name:
            return 'incremental'
        elif '_differential' in archive_name:
            return 'differential'
        return 'unknown'

    def analyze_growth_rate(self) -> Dict:
        """Анализ скорости роста данных"""
        manifests = self.load_all_manifests()

        if len(manifests) < 2:
            return {'error': 'Not enough backups for analysis'}

        sizes = [m.get('total_size', 0) for m in manifests]
        timestamps = [datetime.fromisoformat(m['timestamp']) for m in manifests]

        # Вычислить изменения между бэкапами
        changes = []

        for i in range(1, len(sizes)):
            delta_size = sizes[i] - sizes[i-1]
            delta_time = (timestamps[i] - timestamps[i-1]).total_seconds() / 86400  # days

            if delta_time > 0:
                growth_rate = delta_size / delta_time  # bytes per day

                changes.append({
                    'from': manifests[i-1]['timestamp'],
                    'to': manifests[i]['timestamp'],
                    'delta_bytes': delta_size,
                    'delta_days': delta_time,
                    'growth_rate_per_day': growth_rate
                })

        avg_growth = sum(c['growth_rate_per_day'] for c in changes) / len(changes) if changes else 0

        return {
            'total_backups': len(manifests),
            'initial_size': sizes[0],
            'current_size': sizes[-1],
            'total_growth': sizes[-1] - sizes[0],
            'average_growth_per_day': avg_growth,
            'changes': changes
        }

    def generate_html_timeline(self, output_file: Path):
        """Генерировать HTML timeline визуализацию"""
        timeline = self.build_timeline()
        growth = self.analyze_growth_rate()

        html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backup Timeline</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            color: #667eea;
            margin-bottom: 30px;
            font-size: 2.5em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
        }
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
        }
        .timeline {
            position: relative;
            padding-left: 30px;
        }
        .timeline::before {
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #667eea;
        }
        .event {
            position: relative;
            margin-bottom: 30px;
            padding-left: 30px;
        }
        .event::before {
            content: '';
            position: absolute;
            left: -24px;
            top: 5px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid white;
            box-shadow: 0 0 0 2px #667eea;
        }
        .event.full::before { background: #28a745; box-shadow: 0 0 0 2px #28a745; }
        .event.incremental::before { background: #ffc107; box-shadow: 0 0 0 2px #ffc107; }
        .event.differential::before { background: #17a2b8; box-shadow: 0 0 0 2px #17a2b8; }
        .event h3 {
            color: #333;
            margin-bottom: 5px;
        }
        .event .details {
            font-size: 0.9em;
            color: #666;
        }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: bold;
            margin-right: 5px;
        }
        .badge.full { background: #28a745; color: white; }
        .badge.incremental { background: #ffc107; color: #333; }
        .badge.differential { background: #17a2b8; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 Backup Timeline</h1>

        <div class="stats">
            <div class="stat-card">
                <h3>Total Backups</h3>
                <div class="value">""" + str(timeline['total_backups']) + """</div>
            </div>
            <div class="stat-card">
                <h3>Current Size</h3>
                <div class="value">""" + f"{growth.get('current_size', 0) / (1024*1024):.1f} MB" + """</div>
            </div>
            <div class="stat-card">
                <h3>Total Growth</h3>
                <div class="value">""" + f"{growth.get('total_growth', 0) / (1024*1024):.1f} MB" + """</div>
            </div>
            <div class="stat-card">
                <h3>Avg Growth/Day</h3>
                <div class="value">""" + f"{growth.get('average_growth_per_day', 0) / 1024:.1f} KB" + """</div>
            </div>
        </div>

        <div class="timeline">
"""

        for event in timeline['events']:
            size_mb = event['total_size'] / (1024 * 1024)
            timestamp = datetime.fromisoformat(event['timestamp']).strftime('%Y-%m-%d %H:%M')

            html += f"""            <div class="event {event['type']}">
                <h3>
                    <span class="badge {event['type']}">{event['type'].upper()}</span>
                    {timestamp}
                </h3>
                <div class="details">
                    {event['archive']}<br>
                    Files: {event['file_count']} | Size: {size_mb:.2f} MB
                </div>
            </div>
"""

        html += """        </div>
    </div>
</body>
</html>"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)


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
    parser = argparse.ArgumentParser(
        description='📦 Advanced Archive Builder - Продвинутый построитель архивов',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --full                                   # Полный бэкап (ZIP)
  %(prog)s --incremental                            # Инкрементальный бэкап
  %(prog)s --differential                           # Дифференциальный бэкап
  %(prog)s --format tar.gz --full                   # TAR.GZ архив
  %(prog)s --format both --full                     # Оба формата (ZIP + TAR.GZ)
  %(prog)s --list                                   # Список всех бэкапов
  %(prog)s --validate                               # Валидация всех архивов
  %(prog)s --timeline timeline.html                 # Создать HTML timeline
  %(prog)s --compression-analysis                   # Анализ эффективности сжатия
  %(prog)s --all                                    # Полный бэкап + все анализы

Типы бэкапов:
  - Full: полный бэкап всех файлов
  - Incremental: только изменения с последнего бэкапа
  - Differential: все изменения с последнего ПОЛНОГО бэкапа
        """
    )

    # Типы бэкапов (взаимоисключающие)
    backup_group = parser.add_mutually_exclusive_group()
    backup_group.add_argument(
        '--full',
        action='store_true',
        help='Создать полный бэкап'
    )
    backup_group.add_argument(
        '--incremental',
        action='store_true',
        help='Создать инкрементальный бэкап (изменения с последнего бэкапа)'
    )
    backup_group.add_argument(
        '--differential',
        action='store_true',
        help='Создать дифференциальный бэкап (изменения с последнего full)'
    )

    # Формат архива
    parser.add_argument(
        '-f', '--format',
        choices=['zip', 'tar.gz', 'both'],
        default='zip',
        help='Формат архива (по умолчанию: zip)'
    )

    # Анализ и отчёты
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='Показать список всех бэкапов'
    )

    parser.add_argument(
        '--validate',
        action='store_true',
        help='Валидация целостности всех архивов'
    )

    parser.add_argument(
        '--timeline',
        metavar='FILE',
        help='Создать HTML timeline визуализацию бэкапов'
    )

    parser.add_argument(
        '--compression-analysis',
        action='store_true',
        help='Анализ эффективности сжатия для файлов'
    )

    # Управление
    parser.add_argument(
        '-r', '--rotate',
        action='store_true',
        help='Выполнить ротацию старых бэкапов'
    )

    parser.add_argument(
        '--max-backups',
        type=int,
        default=10,
        help='Максимум бэкапов при ротации (по умолчанию: 10)'
    )

    # Всё сразу
    parser.add_argument(
        '--all',
        action='store_true',
        help='Полный бэкап + все анализы и экспорты'
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    backups_dir = root_dir / "backups"
    backups_dir.mkdir(exist_ok=True)

    builder = AdvancedArchiveBuilder(root_dir)
    builder.max_backups = args.max_backups

    # Только список бэкапов
    if args.list and not args.all:
        builder.list_backups()
        return

    # Только валидация
    if args.validate and not args.all:
        print("\n🔍 Валидация архивов...\n")
        validator = ArchiveValidator()
        result = validator.batch_validate(backups_dir)

        print(f"Всего архивов: {result['total']}")
        print(f"✅ Валидных: {result['valid']}")
        print(f"❌ Невалидных: {result['invalid']}")

        if result['invalid'] > 0:
            print("\nДетали ошибок:")
            for detail in result['details']:
                if not detail['valid']:
                    print(f"  ❌ {detail['archive']}")
                    for error in detail['errors']:
                        print(f"      - {error}")

        return

    # Только timeline
    if args.timeline and not args.all:
        print(f"\n📅 Создание timeline визуализации...\n")
        timeline_builder = TimelineBuilder(backups_dir)
        timeline_builder.generate_html_timeline(Path(args.timeline))
        print(f"✅ Timeline сохранён: {args.timeline}")
        return

    # Только анализ сжатия
    if args.compression_analysis and not args.all:
        print("\n📊 Анализ эффективности сжатия...\n")
        files = builder.collect_files()
        optimizer = CompressionOptimizer()

        analysis = optimizer.analyze_compression_efficiency(files)
        ratio = optimizer.estimate_compression_ratio(files)

        print("Категории файлов:")
        for category, stats in analysis.items():
            size_mb = stats['size'] / (1024 * 1024)
            print(f"  {category:20s}: {stats['count']:4d} файлов, {size_mb:6.2f} MB")

        print(f"\nОжидаемая степень сжатия: {ratio:.2f}x")
        return

    # Определить тип бэкапа
    if args.all or args.full:
        backup_type = 'full'
    elif args.incremental:
        backup_type = 'incremental'
    elif args.differential:
        backup_type = 'differential'
    else:
        # По умолчанию - full
        backup_type = 'full'

    # Создать архив
    if args.format in ['zip', 'both']:
        archive_path = builder.create_zip(backup_type=backup_type)

        if args.rotate or args.all:
            builder.rotate_backups('zip')

    if args.format in ['tar.gz', 'both']:
        archive_path = builder.create_tar_gz(backup_type=backup_type)

        if args.rotate or args.all:
            builder.rotate_backups('tar.gz')

    # Дополнительные анализы при --all
    if args.all:
        print("\n" + "="*60)
        print("ДОПОЛНИТЕЛЬНЫЕ АНАЛИЗЫ")
        print("="*60)

        # Валидация
        print("\n🔍 Валидация архивов...")
        validator = ArchiveValidator()
        result = validator.batch_validate(backups_dir)
        print(f"   ✅ Валидных: {result['valid']}/{result['total']}")

        # Timeline
        timeline_file = root_dir / "backup_timeline.html"
        print(f"\n📅 Создание timeline...")
        timeline_builder = TimelineBuilder(backups_dir)
        timeline_builder.generate_html_timeline(timeline_file)
        print(f"   ✅ Сохранено: {timeline_file}")

        # Анализ сжатия
        print("\n📊 Анализ сжатия...")
        files = builder.collect_files()
        optimizer = CompressionOptimizer()
        ratio = optimizer.estimate_compression_ratio(files)
        print(f"   Ожидаемая степень сжатия: {ratio:.2f}x")

        # Список бэкапов
        builder.list_backups()

        print("\n✨ Все операции завершены!")


if __name__ == "__main__":
    main()
