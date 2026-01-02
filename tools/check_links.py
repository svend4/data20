#!/usr/bin/env python3
"""
Advanced Link Health Monitor - Продвинутый мониторинг здоровья ссылок

Комплексная система проверки ссылок с поддержкой:
- Внутренние ссылки (файлы, якоря)
- Внешние HTTP/HTTPS ссылки с полной валидацией
- SSL сертификаты и безопасность
- Цепочки редиректов
- Производительность ссылок
- Исторический трекинг статуса
- Автоматические предложения замены
- Health scoring (0-100)

Inspired by: LinkChecker, W3C Link Checker, Broken Link Checker

Author: Advanced Knowledge Management System
Version: 2.0
"""

from pathlib import Path
import re
import yaml
import json
import hashlib
import time
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse, urljoin
import argparse

# Optional dependencies для HTTP checking
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import ssl
    import socket
    from OpenSSL import crypto
    SSL_AVAILABLE = True
except ImportError:
    SSL_AVAILABLE = False


class LinkHealthMonitor:
    """
    Продвинутый монитор здоровья ссылок

    Features:
    - Internal link validation (files, anchors)
    - External link checking (HTTP/HTTPS)
    - SSL certificate validation
    - Redirect chain detection (А→B→C→D)
    - Link performance metrics (response time)
    - Historical status tracking
    - Health scoring (0-100)
    - Broken link suggestions
    - Link freshness tracking
    """

    def __init__(self, root_dir=".", cache_file=".link_health_cache.json"):
        self.root_dir = Path(root_dir)
        self.knowledge_dir = self.root_dir / "knowledge"
        self.cache_file = self.root_dir / cache_file

        # Результаты проверки
        self.links = []  # Все найденные ссылки
        self.broken_links = []

        # Historical tracking
        self.history = self.load_history()

        # Performance tracking
        self.performance_stats = defaultdict(list)

        # External link cache (чтобы не проверять один URL много раз)
        self.external_cache = {}

        # HTTP session с retry logic
        if REQUESTS_AVAILABLE:
            self.session = self.create_http_session()
        else:
            self.session = None

    def create_http_session(self, retries=3, backoff_factor=0.3):
        """Создать HTTP session с автоматическими повторами"""
        session = requests.Session()

        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # User-Agent чтобы не блокировали
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; LinkHealthMonitor/2.0; +https://github.com)'
        })

        return session

    def load_history(self):
        """Загрузить историю проверок"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def save_history(self):
        """Сохранить историю проверок"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def get_link_hash(self, url):
        """Хэш ссылки для tracking"""
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def extract_content(self, file_path):
        """Извлечь содержимое из markdown файла"""
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
                # Создать якорь (GitHub-style)
                anchor = text.lower()
                anchor = re.sub(r'[^\w\s-]', '', anchor)
                anchor = re.sub(r'\s+', '-', anchor)
                anchor = re.sub(r'-+', '-', anchor)
                anchor = anchor.strip('-')
                headings.append(anchor)
        return headings

    def check_internal_link(self, file_path, link, link_text):
        """Проверить внутреннюю ссылку (файл/якорь)"""
        result = {
            'url': link,
            'type': 'internal',
            'link_text': link_text,
            'source': str(file_path.relative_to(self.root_dir)),
            'status': 'ok',
            'health_score': 100.0,
            'issues': []
        }

        # Разделить на файл и якорь
        if '#' in link:
            file_part, anchor_part = link.split('#', 1)
        else:
            file_part = link
            anchor_part = None

        # Проверить файл
        if file_part:
            target = (file_path.parent / file_part).resolve()

            if not target.exists():
                result['status'] = 'broken_file'
                result['health_score'] = 0.0
                result['issues'].append(f"File not found: {file_part}")
                result['target'] = str(target.relative_to(self.root_dir)) if target.is_relative_to(self.root_dir) else str(target)
                self.broken_links.append(result)
                return result

        # Проверить якорь
        if anchor_part:
            if file_part:
                # Якорь в другом файле
                target = (file_path.parent / file_part).resolve()
                if target.exists():
                    target_content = self.extract_content(target)
                    if target_content:
                        target_anchors = set(self.extract_headings(target_content))
                        if anchor_part not in target_anchors:
                            result['status'] = 'broken_anchor'
                            result['health_score'] = 30.0  # Файл есть, якоря нет
                            result['issues'].append(f"Anchor not found: #{anchor_part}")
                            result['anchor'] = anchor_part
                            result['available_anchors'] = list(target_anchors)[:5]  # Первые 5 для подсказки
                            self.broken_links.append(result)
            else:
                # Якорь в текущем файле
                content = self.extract_content(file_path)
                if content:
                    local_anchors = set(self.extract_headings(content))
                    if anchor_part not in local_anchors:
                        result['status'] = 'broken_anchor'
                        result['health_score'] = 50.0
                        result['issues'].append(f"Local anchor not found: #{anchor_part}")
                        result['anchor'] = anchor_part
                        self.broken_links.append(result)

        return result

    def check_ssl_certificate(self, hostname, port=443):
        """Проверить SSL сертификат"""
        if not SSL_AVAILABLE:
            return {'valid': None, 'days_remaining': None, 'issuer': None}

        try:
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_bin = ssock.getpeercert(binary_form=True)
                    cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_bin)

                    # Expiry date
                    expiry_date = datetime.strptime(cert.get_notAfter().decode(), '%Y%m%d%H%M%SZ')
                    days_remaining = (expiry_date - datetime.now()).days

                    # Issuer
                    issuer = dict(cert.get_issuer().get_components())
                    issuer_cn = issuer.get(b'CN', b'Unknown').decode()

                    return {
                        'valid': True,
                        'days_remaining': days_remaining,
                        'issuer': issuer_cn,
                        'expiry_date': expiry_date.isoformat()
                    }
        except Exception as e:
            return {'valid': False, 'error': str(e)}

    def check_redirect_chain(self, url, max_redirects=5):
        """Отследить цепочку редиректов: A→B→C→D"""
        chain = []
        current_url = url

        for i in range(max_redirects):
            try:
                response = self.session.get(current_url, allow_redirects=False, timeout=10)

                chain.append({
                    'url': current_url,
                    'status': response.status_code,
                    'step': i + 1
                })

                # Если не редирект - выходим
                if response.status_code not in [301, 302, 303, 307, 308]:
                    break

                # Следующий URL в цепочке
                if 'Location' in response.headers:
                    next_url = response.headers['Location']
                    # Относительный URL -> абсолютный
                    if not next_url.startswith('http'):
                        next_url = urljoin(current_url, next_url)
                    current_url = next_url
                else:
                    break

            except Exception as e:
                chain.append({'url': current_url, 'error': str(e), 'step': i + 1})
                break

        return chain

    def check_external_link(self, url, link_text, source_file):
        """Проверить внешнюю HTTP/HTTPS ссылку"""
        # Проверить кэш
        url_hash = self.get_link_hash(url)
        if url in self.external_cache:
            cached = self.external_cache[url].copy()
            cached['cached'] = True
            return cached

        result = {
            'url': url,
            'type': 'external',
            'link_text': link_text,
            'source': str(source_file.relative_to(self.root_dir)),
            'status': 'unknown',
            'health_score': 0.0,
            'issues': [],
            'timestamp': datetime.now().isoformat()
        }

        if not REQUESTS_AVAILABLE:
            result['issues'].append("requests library not available")
            return result

        start_time = time.time()

        try:
            # Сначала HEAD запрос (быстрее)
            response = self.session.head(url, timeout=10, allow_redirects=True)

            # Некоторые сайты не поддерживают HEAD - пробуем GET
            if response.status_code == 405:
                response = self.session.get(url, timeout=10, stream=True)
                response.close()  # Не скачиваем тело

            elapsed_ms = (time.time() - start_time) * 1000

            # Статус код
            status_code = response.status_code
            result['status_code'] = status_code
            result['response_time_ms'] = round(elapsed_ms, 2)

            # Health score на основе статуса
            if status_code == 200:
                result['status'] = 'ok'
                result['health_score'] = 100.0
            elif status_code in [301, 302, 303, 307, 308]:
                result['status'] = 'redirect'
                result['health_score'] = 80.0
                result['issues'].append(f"Redirect: {status_code}")
                result['final_url'] = response.url
            elif status_code == 404:
                result['status'] = 'not_found'
                result['health_score'] = 0.0
                result['issues'].append("404 Not Found")
                self.broken_links.append(result)
            elif status_code == 403:
                result['status'] = 'forbidden'
                result['health_score'] = 50.0
                result['issues'].append("403 Forbidden")
            elif status_code >= 500:
                result['status'] = 'server_error'
                result['health_score'] = 20.0
                result['issues'].append(f"Server error: {status_code}")
            else:
                result['status'] = 'other'
                result['health_score'] = 60.0

            # Проверить редиректы
            if len(response.history) > 0:
                result['redirect_count'] = len(response.history)
                if len(response.history) > 3:
                    result['issues'].append(f"Too many redirects: {len(response.history)}")
                    result['health_score'] -= 10

            # SSL сертификат для HTTPS
            if url.startswith('https://'):
                parsed = urlparse(url)
                ssl_info = self.check_ssl_certificate(parsed.hostname)
                result['ssl'] = ssl_info

                if ssl_info.get('valid') is False:
                    result['issues'].append(f"SSL error: {ssl_info.get('error')}")
                    result['health_score'] -= 20
                elif ssl_info.get('days_remaining') is not None:
                    days = ssl_info['days_remaining']
                    if days < 30:
                        result['issues'].append(f"SSL expires soon: {days} days")
                        result['health_score'] -= 10

            # Performance warning
            if elapsed_ms > 5000:
                result['issues'].append(f"Slow response: {elapsed_ms:.0f}ms")
                result['health_score'] -= 5

            # Запомнить в истории
            if url_hash not in self.history:
                self.history[url_hash] = {'url': url, 'checks': []}

            self.history[url_hash]['checks'].append({
                'timestamp': result['timestamp'],
                'status_code': status_code,
                'response_time_ms': elapsed_ms,
                'health_score': result['health_score']
            })

            # Ограничить историю до 10 последних проверок
            self.history[url_hash]['checks'] = self.history[url_hash]['checks'][-10:]

        except requests.exceptions.Timeout:
            result['status'] = 'timeout'
            result['health_score'] = 10.0
            result['issues'].append("Request timeout (>10s)")
            self.broken_links.append(result)
        except requests.exceptions.SSLError as e:
            result['status'] = 'ssl_error'
            result['health_score'] = 0.0
            result['issues'].append(f"SSL error: {str(e)[:100]}")
            self.broken_links.append(result)
        except requests.exceptions.ConnectionError as e:
            result['status'] = 'connection_error'
            result['health_score'] = 0.0
            result['issues'].append(f"Connection error: {str(e)[:100]}")
            self.broken_links.append(result)
        except Exception as e:
            result['status'] = 'error'
            result['health_score'] = 0.0
            result['issues'].append(f"Error: {str(e)[:100]}")

        # Кэшировать результат
        self.external_cache[url] = result

        return result

    def check_file(self, file_path, check_external=True):
        """Проверить все ссылки в файле"""
        content = self.extract_content(file_path)
        if not content:
            return

        # Найти все markdown ссылки [text](url)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for text, link in links:
            # Внешние ссылки
            if link.startswith('http://') or link.startswith('https://'):
                if check_external:
                    result = self.check_external_link(link, text, file_path)
                    self.links.append(result)
            # Внутренние ссылки
            else:
                result = self.check_internal_link(file_path, link, text)
                self.links.append(result)

    def check_all(self, check_external=True):
        """Проверить все файлы"""
        print("🔗 Link Health Monitor - Проверка ссылок...\n")

        md_files = list(self.knowledge_dir.rglob("*.md"))
        print(f"   Файлов для проверки: {len(md_files)}")

        for i, md_file in enumerate(md_files, 1):
            if md_file.name == "INDEX.md":
                continue

            if i % 10 == 0:
                print(f"   Обработано: {i}/{len(md_files)}")

            self.check_file(md_file, check_external=check_external)

        print(f"\n   Всего ссылок: {len(self.links)}")
        print(f"   Битых/проблемных: {len(self.broken_links)}\n")

        # Сохранить историю
        if check_external:
            self.save_history()

    def calculate_link_freshness(self, url_hash):
        """Свежесть ссылки (когда последний раз проверялась)"""
        if url_hash not in self.history:
            return None

        checks = self.history[url_hash].get('checks', [])
        if not checks:
            return None

        last_check = datetime.fromisoformat(checks[-1]['timestamp'])
        age_hours = (datetime.now() - last_check).total_seconds() / 3600

        return {
            'last_check': last_check.isoformat(),
            'age_hours': round(age_hours, 2),
            'freshness': 'fresh' if age_hours < 24 else 'stale' if age_hours < 168 else 'old'
        }

    def suggest_replacement(self, broken_link):
        """Предложить замену для битой ссылки"""
        suggestions = []

        # Для битых внутренних файлов - найти похожие файлы
        if broken_link['type'] == 'internal' and broken_link['status'] == 'broken_file':
            target = broken_link.get('target', '')
            # Найти файлы с похожими именами
            target_name = Path(target).stem.lower()

            for md_file in self.knowledge_dir.rglob("*.md"):
                file_name = md_file.stem.lower()
                # Простая Levenshtein distance
                if self.levenshtein_distance(target_name, file_name) <= 3:
                    suggestions.append(str(md_file.relative_to(self.root_dir)))

        # Для битых якорей - показать доступные якоря
        elif broken_link['status'] == 'broken_anchor':
            available = broken_link.get('available_anchors', [])
            if available:
                suggestions.extend([f"#{anchor}" for anchor in available])

        return suggestions[:5]  # Максимум 5 предложений

    def levenshtein_distance(self, s1, s2):
        """Расстояние Левенштейна для поиска похожих слов"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def generate_statistics(self):
        """Статистика по ссылкам"""
        stats = {
            'total_links': len(self.links),
            'internal_links': sum(1 for l in self.links if l['type'] == 'internal'),
            'external_links': sum(1 for l in self.links if l['type'] == 'external'),
            'broken_links': len(self.broken_links),
            'health_distribution': defaultdict(int),
            'status_distribution': defaultdict(int),
            'avg_response_time': 0.0,
        }

        # Распределение по health score
        for link in self.links:
            score = link['health_score']
            if score >= 90:
                stats['health_distribution']['excellent'] += 1
            elif score >= 70:
                stats['health_distribution']['good'] += 1
            elif score >= 50:
                stats['health_distribution']['fair'] += 1
            else:
                stats['health_distribution']['poor'] += 1

            stats['status_distribution'][link['status']] += 1

        # Средняя скорость ответа для внешних ссылок
        response_times = [l['response_time_ms'] for l in self.links if 'response_time_ms' in l]
        if response_times:
            stats['avg_response_time'] = round(sum(response_times) / len(response_times), 2)

        return stats

    def generate_report(self, format='markdown'):
        """Создать отчёт"""
        stats = self.generate_statistics()

        if format == 'json':
            return self.generate_json_report(stats)
        elif format == 'html':
            return self.generate_html_report(stats)
        else:
            return self.generate_markdown_report(stats)

    def generate_markdown_report(self, stats):
        """Markdown отчёт"""
        lines = []
        lines.append("# 🔗 Link Health Report\n\n")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Статистика
        lines.append("## 📊 Summary Statistics\n\n")
        lines.append(f"- **Total links**: {stats['total_links']}\n")
        lines.append(f"- **Internal links**: {stats['internal_links']}\n")
        lines.append(f"- **External links**: {stats['external_links']}\n")
        lines.append(f"- **Broken/Issues**: {stats['broken_links']}\n")
        if stats['avg_response_time'] > 0:
            lines.append(f"- **Avg response time**: {stats['avg_response_time']:.0f}ms\n")
        lines.append("\n")

        # Health distribution
        lines.append("### Health Distribution\n\n")
        lines.append(f"- 🟢 **Excellent (90-100)**: {stats['health_distribution']['excellent']}\n")
        lines.append(f"- 🟡 **Good (70-89)**: {stats['health_distribution']['good']}\n")
        lines.append(f"- 🟠 **Fair (50-69)**: {stats['health_distribution']['fair']}\n")
        lines.append(f"- 🔴 **Poor (0-49)**: {stats['health_distribution']['poor']}\n\n")

        # Status distribution
        lines.append("### Status Distribution\n\n")
        for status, count in sorted(stats['status_distribution'].items(), key=lambda x: -x[1]):
            lines.append(f"- **{status}**: {count}\n")
        lines.append("\n")

        # Битые ссылки
        if self.broken_links:
            lines.append(f"## ❌ Broken/Problematic Links ({len(self.broken_links)})\n\n")

            for i, link in enumerate(self.broken_links[:50], 1):  # Первые 50
                lines.append(f"### {i}. {link['status'].upper()}\n\n")
                lines.append(f"- **URL**: `{link['url']}`\n")
                lines.append(f"- **Source**: {link['source']}\n")
                lines.append(f"- **Health score**: {link['health_score']:.1f}/100\n")

                if link.get('issues'):
                    lines.append(f"- **Issues**: {', '.join(link['issues'])}\n")

                if link.get('status_code'):
                    lines.append(f"- **Status code**: {link['status_code']}\n")

                if link.get('response_time_ms'):
                    lines.append(f"- **Response time**: {link['response_time_ms']:.0f}ms\n")

                # Предложения замены
                suggestions = self.suggest_replacement(link)
                if suggestions:
                    lines.append(f"- **Suggestions**: {', '.join(f'`{s}`' for s in suggestions)}\n")

                lines.append("\n")
        else:
            lines.append("## ✅ All Links Healthy!\n\n")

        output_file = self.root_dir / "LINK_HEALTH_REPORT.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print(f"✅ Markdown report: {output_file}")
        return output_file

    def generate_json_report(self, stats):
        """JSON отчёт"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'all_links': self.links,
            'broken_links': self.broken_links
        }

        output_file = self.root_dir / "link_health.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ JSON report: {output_file}")
        return output_file


def main():
    parser = argparse.ArgumentParser(description='Advanced Link Health Monitor')
    parser.add_argument('--no-external', action='store_true',
                       help='Skip external link checking (only internal)')
    parser.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                       help='Report format (default: markdown)')
    parser.add_argument('--cache', default='.link_health_cache.json',
                       help='Cache file for historical data')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    root_dir = script_dir.parent

    monitor = LinkHealthMonitor(root_dir, cache_file=args.cache)
    monitor.check_all(check_external=not args.no_external)
    monitor.generate_report(format=args.format)


if __name__ == "__main__":
    main()
