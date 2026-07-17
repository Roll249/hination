#!/usr/bin/env python3
"""
Disaster News Scraper for Vietnam
Part of Hination - AI Weather Warning System
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data" / "disasters"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class DisasterNewsScraper:
    """Scraper for disaster-related news from Vietnamese sources"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def fetch_vnexpress_disasters(self) -> list[dict]:
        """Fetch disaster news from VnExpress"""
        logger.info("Fetching VnExpress disaster news...")
        articles = []

        # Try different VnExpress sections
        urls = [
            'https://vnexpress.net/thoi-su/thien-tai',
            'https://vnexpress.net/thoi-su/lu-lut',
        ]

        for url in urls:
            try:
                response = self.session.get(url, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')

                # VnExpress article structure
                for article in soup.find_all('article', class_=['item_news', 'list_news']):
                    try:
                        title_elem = article.find('h3') or article.find('h2') or article.find('a', class_='title')
                        title = title_elem.get_text(strip=True) if title_elem else ''

                        link_elem = article.find('a')
                        link = link_elem.get('href', '') if link_elem else ''

                        date_elem = article.find('span', class_='time') or article.find('time')
                        date = date_elem.get_text(strip=True) if date_elem else ''

                        desc_elem = article.find('p', class_='description')
                        desc = desc_elem.get_text(strip=True) if desc_elem else ''

                        if title and link:
                            articles.append({
                                'title': title,
                                'link': link,
                                'date': date,
                                'description': desc,
                                'source': 'vnexpress.net',
                                'category': 'disaster',
                                'fetched_at': datetime.now().isoformat()
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing article: {e}")
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")

        return articles

    def fetch_baochinh_disasters(self) -> list[dict]:
        """Fetch disaster news from Nhandan/Bao Chinh phu"""
        logger.info("Fetching Nhandan disaster news...")
        articles = []

        try:
            response = self.session.get(
                'https://nhandan.vn/search/?q=thi%C3%AAn+tai',
                timeout=30
            )
            soup = BeautifulSoup(response.text, 'html.parser')

            for article in soup.find_all('article'):
                try:
                    title_elem = article.find('h3') or article.find('h2')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    link_elem = article.find('a')
                    link = link_elem.get('href', '') if link_elem else ''

                    if title and link and '/tin/' in link:
                        articles.append({
                            'title': title,
                            'link': f"https://nhandan.vn{link}" if not link.startswith('http') else link,
                            'source': 'nhandan.vn',
                            'category': 'disaster',
                            'fetched_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
        except Exception as e:
            logger.error(f"Error fetching Nhandan: {e}")

        return articles

    def fetch_tuoitre_disasters(self) -> list[dict]:
        """Fetch disaster news from Tuoi Tre"""
        logger.info("Fetching TuoiTre disaster news...")
        articles = []

        try:
            response = self.session.get(
                'https://tuoitre.vn/tim-kiem.htm?keywords=thiên+tai&type=0',
                timeout=30
            )
            soup = BeautifulSoup(response.text, 'html.parser')

            for article in soup.find_all('div', class_='item'):
                try:
                    title_elem = article.find('h3') or article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    link_elem = article.find('a')
                    link = link_elem.get('href', '') if link_elem else ''

                    if title and link:
                        articles.append({
                            'title': title,
                            'link': link if link.startswith('http') else f"https://tuoitre.vn{link}",
                            'source': 'tuoitre.vn',
                            'category': 'disaster',
                            'fetched_at': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Error parsing article: {e}")
        except Exception as e:
            logger.error(f"Error fetching TuoiTre: {e}")

        return articles

    def fetch_weather_warnings(self) -> list[dict]:
        """Fetch official weather warnings"""
        logger.info("Fetching weather warnings...")
        warnings = []

        # National Center for Hydro-Meteorological Forecasting
        urls = [
            'https://nchmf.gov.vn/Website/vi/VBDT',
            'https://nchmf.gov.vn/Website/vi/CBND',
        ]

        for url in urls:
            try:
                response = self.session.get(url, timeout=30)
                soup = BeautifulSoup(response.text, 'html.parser')

                for item in soup.find_all(['tr', 'div'], class_=['row', 'item', 'warning-item']):
                    try:
                        content = item.get_text(strip=True)
                        link_elem = item.find('a')

                        if content and len(content) > 20:
                            warnings.append({
                                'content': content,
                                'link': link_elem.get('href', '') if link_elem else '',
                                'source': 'nchmf.gov.vn',
                                'type': 'weather_warning',
                                'fetched_at': datetime.now().isoformat()
                            })
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")

        return warnings

    def fetch_dien_bien_news(self) -> list[dict]:
        """Fetch news specifically about Dien Bien province"""
        logger.info("Fetching Dien Bien specific news...")
        articles = []

        try:
            # Search for Dien Bien news
            response = self.session.get(
                'https://dienbien.gov.vn/',
                timeout=30
            )
            soup = BeautifulSoup(response.text, 'html.parser')

            for article in soup.find_all(['article', 'div'], class_=['news-item', 'post-item']):
                try:
                    title_elem = article.find('h3') or article.find('h4') or article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    link_elem = article.find('a')
                    link = link_elem.get('href', '') if link_elem else ''

                    if title and link:
                        articles.append({
                            'title': title,
                            'link': link if link.startswith('http') else f"https://dienbien.gov.vn{link}",
                            'source': 'dienbien.gov.vn',
                            'category': 'provincial',
                            'fetched_at': datetime.now().isoformat()
                        })
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Error fetching Dien Bien news: {e}")

        return articles

    def save_results(self, name: str, data: list):
        """Save scraped data to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = DATA_DIR / f"{name}_{timestamp}.json"

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'name': name,
                'fetched_at': datetime.now().isoformat(),
                'count': len(data),
                'data': data
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(data)} items to {filepath}")
        return filepath


def main():
    """Main function to run all disaster scrapers"""
    logger.info("=" * 60)
    logger.info("Starting Disaster News Collection")
    logger.info("=" * 60)

    scraper = DisasterNewsScraper()
    all_results = {}

    # Fetch from various sources
    sources = [
        ('vnexpress', scraper.fetch_vnexpress_disasters),
        ('baochinh', scraper.fetch_baochinh_disasters),
        ('tuoitre', scraper.fetch_tuoitre_disasters),
        ('weather_warnings', scraper.fetch_weather_warnings),
        ('dien_bien', scraper.fetch_dien_bien_news),
    ]

    for name, fetch_func in sources:
        logger.info(f"\nFetching from {name}...")
        results = fetch_func()
        all_results[name] = results
        scraper.save_results(name, results)
        logger.info(f"Found {len(results)} items")

    # Save combined results
    combined_path = DATA_DIR / f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(combined_path, 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'sources': list(all_results.keys()),
            'total_items': sum(len(v) for v in all_results.values()),
            'data': all_results
        }, f, ensure_ascii=False, indent=2)

    logger.info(f"\nTotal items collected: {sum(len(v) for v in all_results.values())}")
    return all_results


if __name__ == '__main__':
    main()
