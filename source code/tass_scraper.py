import json
import csv
import logging
import random
import re
import sys
import time
import datetime
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class NewsScraperConfig:

    def __init__(self):
        self.headlines_per_category = 20
        self.categories = ["politics", "world", "economy", "defense", "science",
                            "emergencies", "society", "pressreview", "sports"]
        self.max_workers = 2
        self.output_dir = "news_data"
        self.include_top_words = False
        self.min_delay = 0.2
        self.max_delay = 1.0
        self.max_retries = 3
        self.use_csv = False

    def validate(self):
        if self.headlines_per_category <= 0:
            raise ValueError("headlines_per_category must be positive")
        if self.max_workers <= 0:
            raise ValueError("max_workers must be positive")
        if self.min_delay >= self.max_delay:
            raise ValueError("min_delay must be less than max_delay")
        if not self.categories:
            raise ValueError("at least one category must be specified")




class Colors:

    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_RED = '\033[91m'
    LIGHT_BLUE = '\033[94m'
    RESET = '\033[0m'

    @classmethod
    def green(cls, text):
        return f"{cls.LIGHT_GREEN}{text}{cls.RESET}"

    @classmethod
    def yellow(cls, text):
        return f"{cls.LIGHT_YELLOW}{text}{cls.RESET}"

    @classmethod
    def red(cls, text):
        return f"{cls.LIGHT_RED}{text}{cls.RESET}"

    @classmethod
    def blue(cls, text):
        return f"{cls.LIGHT_BLUE}{text}{cls.RESET}"




class ProgressBar:

    def __init__(self, total, length=50):
        self.total = total
        self.length = length
        self.start_time = time.time()
        

    def update(self, progress):
        if progress >= self.total:
            sys.stdout.write('\r' + self._format_bar(progress) + '\n')
        else:
            sys.stdout.write('\r' + self._format_bar(progress))
        sys.stdout.flush()
        

    def _format_bar(self, progress):
        percent = int((progress / self.total) * 100)
        filled_length = int(self.length * progress // self.total)
        
        bar = f"[{Colors.LIGHT_GREEN}{'#' * filled_length}{Colors.RESET}{' ' * (self.length - filled_length)}] {Colors.LIGHT_YELLOW}{percent}%{Colors.RESET}"
        
        elapsed_time = time.time() - self.start_time
        avg_time_per_item = elapsed_time / max(progress, 1)
        remaining_items = self.total - progress
        eta = avg_time_per_item * remaining_items
        
        eta_seconds = int(eta)
        minutes, seconds = divmod(eta_seconds, 60)
        bar += f"  ETA: {Colors.LIGHT_BLUE}{minutes:02}:{seconds:02}{Colors.RESET}"
            
        return bar




class ColoredLogger(logging.Logger):

    def info(self, msg, *args, **kwargs):
        if "Fetching news list for category:" in str(msg):
            category = msg.split(": ")[1]
            msg = f"Fetching news list for category: {Colors.yellow(category)}"
        super().info(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        super().error(Colors.red(msg), *args, **kwargs)




class UserAgentRotator:

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.chrome_versions = self._get_chrome_versions()
        self.firefox_versions = self._get_firefox_versions()
        self.user_agents = self._generate_user_agents()
        self.usage_counts = {ua: 0 for ua in self.user_agents}


    def _get_chrome_versions(self):
        try:
            response = requests.get('https://versionhistory.googleapis.com/v1/chrome/platforms/win/channels/stable/versions')
            data = response.json()
            versions = []
            for i in range(2, 30, 3):
                major_version = data['versions'][i]['version'].split('.')[0]
                version = f"{major_version}.0.0.0"
                versions.append(version)
            return versions * 2
        except Exception:
            return ['131.0.0.0', '131.0.0.0', '131.0.0.0', '131.0.0.0','131.0.0.0',
                    '130.0.0.0', '130.0.0.0', '130.0.0.0', '130.0.0.0', '129.0.0.0',
                    '131.0.0.0', '131.0.0.0', '131.0.0.0', '131.0.0.0', '131.0.0.0',
                    '130.0.0.0', '130.0.0.0', '130.0.0.0', '130.0.0.0', '129.0.0.0']


    def _get_firefox_versions(self):
        try:
            response = requests.get('https://product-details.mozilla.org/1.0/firefox_versions.json')
            current_major = int(response.json()["LATEST_FIREFOX_VERSION"].split('.')[0])
            
            versions = []
            versions.extend([f"{current_major}.0"] * 10)
            versions.extend([f"{current_major - 1}.0"] * 8)
            versions.extend([f"{current_major - 2}.0"] * 2)
            
            return versions
        except Exception:
            return ['133.0', '133.0', '133.0', '133.0', '133.0',
                    '133.0', '133.0', '133.0', '133.0', '133.0',
                    '132.0', '132.0', '132.0', '132.0', '132.0',
                    '132.0', '132.0', '132.0', '131.0', '131.0']


    def _generate_user_agents(self):
        user_agents = []
        
        os_configs = {
            'windows': {
                'platform': 'Windows NT 10.0; Win64; x64',
                'weight': 0.65
            },
            'macos': {
                'architectures': [
                    ('Intel Mac OS X', 0.7),
                    ('Apple Silicon Mac OS X', 0.3)
                ],
                'chrome_version': '10_15_7',
                'firefox_version': '10.15',
                'weight': 0.30
            },
            'linux': {
                'platform': 'X11; Linux x86_64',
                'weight': 0.05
            }
        }

        # Generate Chrome user agents
        for version in self.chrome_versions:
            os_type = random.choices(
                list(os_configs.keys()),
                weights=[config['weight'] for config in os_configs.values()]
            )[0]
            
            if os_type == 'macos':
                arch = random.choices(
                    [a[0] for a in os_configs['macos']['architectures']],
                    weights=[a[1] for a in os_configs['macos']['architectures']]
                )[0]
                platform = f'Macintosh; {arch} {os_configs["macos"]["chrome_version"]}'
            else:
                platform = os_configs[os_type]['platform']
                
            chrome_agent = f'Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36'
            user_agents.append(chrome_agent)

        # Generate Firefox user agents  
        for version in self.firefox_versions:
            os_type = random.choices(
                list(os_configs.keys()),
                weights=[config['weight'] for config in os_configs.values()]
            )[0]
            
            if os_type == 'macos':
                arch = random.choices(
                    [a[0] for a in os_configs['macos']['architectures']],
                    weights=[a[1] for a in os_configs['macos']['architectures']]
                )[0]
                platform = f'Macintosh; {arch} {os_configs["macos"]["firefox_version"]}'
            else:
                platform = os_configs[os_type]['platform']
                
            firefox_agent = f'Mozilla/5.0 ({platform}; rv:{version}) Gecko/20100101 Firefox/{version}'
            user_agents.append(firefox_agent)

        return user_agents


    def get_next_user_agent(self):
        min_usage = min(self.usage_counts.values())
        least_used = [ua for ua, count in self.usage_counts.items() if count == min_usage]
        
        selected_agent = random.choice(least_used)
        self.usage_counts[selected_agent] += 1
        
        return selected_agent




class NewsScraper:

    CATEGORY_MAP = {
        "politics": 4954,
        "world": 4844,
        "economy": 4845,
        "defense": 4953,
        "science": 4957,
        "emergencies": 4992,
        "society": 4956,
        "pressreview": 4981,
        "sports": 4869
    }


    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "logs").mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
        self.session = self._setup_session()
        self.user_agent_rotator = UserAgentRotator(self.logger)
        self.errors_occurred = False
        

    def _setup_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session


    def _setup_logger(self):
        logging.setLoggerClass(ColoredLogger)
        logger = logging.getLogger('NewsScraper')
        logger.setLevel(logging.INFO)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)
        
        log_path = Path(self.config.output_dir) / 'logs' / 'scraper.log'
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger
        

    def get_top_words(self, text_data):
        if not self.config.include_top_words:
            return []
            
        stop_words = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
            "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", 
            "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
            "theirs", "themselves", "what", "which", "who", "whom", "this", "that", 
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
            "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
            "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", 
            "at", "by", "for", "with", "about", "against", "between", "into", "through", 
            "during", "before", "after", "above", "below", "to", "from", "up", "down", 
            "in", "out", "on", "off", "over", "under", "again", "further", "then", 
            "once", "here", "there", "when", "where", "why", "how", "all", "any", 
            "both", "each", "few", "more", "most", "other", "some", "such", "no", 
            "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can", 
            "will", "just", "now", "should", "would", "could", "might", "must", 
            "shall", "may", "also", "still", "yet", "ever", "never"
        ])

        words = re.findall(r"\b\w+'\w+|\w+\b", " ".join(text_data).lower())
        words = [re.sub(r"'s$", "", word) for word in words if word != "s"]
        filtered_words = [w for w in words if w not in stop_words and not w.isdigit()]
        
        return [{"word": word, "count": count} 
                for word, count in Counter(filtered_words).most_common(10)]


    def fetch_article_content(self, article):
        headers = {
            "User-Agent": self.user_agent_rotator.get_next_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        
        time.sleep(random.uniform(self.config.min_delay, self.config.max_delay))
        
        try:
            response = self.session.get(article["link"], headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "lxml")
            contents = []
            
            if header_lead := soup.select_one("div.news-header__lead"):
                contents.append(header_lead.text.strip())
                
            for p in soup.select("div.text-block p"):
                contents.append(p.text.strip())
                
            if not contents:
                raise ValueError("No content found in article")
                
            article["content"] = contents
            if self.config.include_top_words:
                article["top_words"] = self.get_top_words(contents)
            return article
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while fetching {article['link']}: {e}")
            self.errors_occurred = True
            raise
        except Exception as e:
            self.logger.error(f"Error processing {article['link']}: {e}")
            self.errors_occurred = True
            raise


    def get_news_list(self, category):
        self.logger.info(f"Fetching news list for category: {category}")
        
        headers = {
            "Host": "tass.com",
            "User-Agent": self.user_agent_rotator.get_next_user_agent(),
            "Accept": "application/json",
            "Content-Type": "application/json;charset=utf-8",
            "Origin": "https://tass.com",
            "DNT": "1",
            "Referer": f"https://tass.com/{category}",
        }

        payload = {
            "sectionId": self.CATEGORY_MAP[category],
            "limit": self.config.headlines_per_category,
            "type": "all",
            "imageSize": 434
        }

        try:
            response = self.session.post(
                "https://tass.com/userApi/categoryNewsList",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            news_list = response.json()["newsList"]
            return [{
                "title": item["title"],
                "description": item["lead"],
                "date": str(datetime.datetime.fromtimestamp(item["date"])),
                "link": f"https://tass.com{item['link']}"
            } for item in news_list]
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error while fetching news list for {category}: {e}")
            self.errors_occurred = True
            raise
        except Exception as e:
            self.logger.error(f"Error processing news list for {category}: {e}")
            self.errors_occurred = True
            raise


    def save_to_csv(self, articles, output_path):
        if not articles:
            return

        flattened_articles = []
        for article in articles:
            flat_article = {
                'title': article['title'],
                'description': article['description'],
                'date': article['date'],
                'link': article['link'],
                'content': ' '.join(article['content'])
            }
            
            if self.config.include_top_words and 'top_words' in article:
                for i, word_info in enumerate(article['top_words'], 1):
                    flat_article[f'top_word_{i}'] = word_info['word']
                    flat_article[f'top_word_{i}_count'] = word_info['count']

            flattened_articles.append(flat_article)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if flattened_articles:
                writer = csv.DictWriter(f, fieldnames=flattened_articles[0].keys())
                writer.writeheader()
                writer.writerows(flattened_articles)


    def process_category(self, category):
        try:
            news_list = self.get_news_list(category)
            progress_bar = ProgressBar(len(news_list))
            processed_articles = []
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_article = {
                    executor.submit(self.fetch_article_content, article): article 
                    for article in news_list
                }
                
                for i, future in enumerate(future_to_article, 1):
                    try:
                        article = future.result()
                        processed_articles.append(article)
                        progress_bar.update(i)
                    except Exception as e:
                        self.logger.error(f"Error processing article: {e}")
                        self.errors_occurred = True
            
            extension = 'csv' if self.config.use_csv else 'json'
            output_path = Path(self.config.output_dir) / f"{category}_{self.config.headlines_per_category}.{extension}"
            
            if self.config.use_csv:
                self.save_to_csv(processed_articles, output_path)
            else:
                with open(output_path, "w", encoding='utf-8') as f:
                    json.dump(processed_articles, f, indent=4, ensure_ascii=False)
                
            self.logger.info(f"Successfully processed {len(processed_articles)} articles for {category}")
                
        except Exception as e:
            self.logger.error(f"Error processing category {category}: {e}")
            self.errors_occurred = True

    def run(self):
        self.config.validate()
        for category in self.config.categories:
            if category in self.CATEGORY_MAP:
                self.process_category(category)
                print()
            else:
                self.logger.error(f"Invalid category: {category}")
                self.errors_occurred = True
                
        if not self.errors_occurred:
            self.logger.info(Colors.green("All tasks have finished successfully."))
        else:
            self.logger.error("Some tasks failed during execution.")




def main():
    class CustomFormatter(argparse.HelpFormatter):

        def __init__(self, prog):
            super().__init__(prog, max_help_position=50, width=100)
        

        def _format_action_invocation(self, action):
            if not action.option_strings:
                metavar = self._metavar_formatter(action, action.dest)(1)
                return metavar
            else:
                parts = []
                if action.nargs == 0:
                    parts.extend(action.option_strings)
                else:
                    default = action.dest.upper()
                    args_string = self._format_args(action, default)
                    for option_string in action.option_strings:
                        parts.append('%s %s' % (option_string, args_string))
                return ', '.join(parts)
        

        def _format_text(self, text):
            if text.startswith("Available categories:"):
                return text
            return super()._format_text(text)


    categories_help = "Available categories:\n"
    category_desc = {
        "politics": "Russian Politics & Diplomacy",
        "world": "World",
        "economy": "Business & Economy",
        "defense": "Military & Defense",
        "science": "Science & Space",
        "emergencies": "Emergencies",
        "society": "Society & Culture",
        "pressreview": "Press Review",
        "sports": "Sports"
    }
    for category in NewsScraper.CATEGORY_MAP:
        for cat in category_desc:
            if category == cat:
                categories_help += f"  • {category} -- {category_desc[category]}\n"
    
    parser = argparse.ArgumentParser(
        description="TASS News Scraper",
        formatter_class=CustomFormatter,
        epilog=categories_help
    )
    
    parser.add_argument("--headlines", 
                       type=int, 
                       default=20,
                       metavar="N",
                       help="Number of headlines per category (default: 20)")
    
    parser.add_argument("--categories", 
                       nargs="+", 
                       default=["politics", "world",
                                "economy", "defense",
                                "science", "emergencies",
                                "society", "pressreview",
                                "sports"
                                ],
                       metavar="CATEGORY",
                       help="Categories to scrape (default: All categories)")
    
    parser.add_argument("--csv",
                       action="store_true",
                       help="Save output in CSV format instead of JSON")
    
    parser.add_argument("--workers", 
                       type=int, 
                       default=2,
                       metavar="N",
                       help="Maximum number of concurrent workers (default: 2)")
    
    parser.add_argument("--output-dir", 
                       default="news_data",
                       metavar="DIR",
                       help="Output directory for scraped data (default: ./news_data)")
    
    parser.add_argument("--top-words", 
                       action="store_true",
                       help="Enable top words analysis (disabled by default)")
    
    parser.add_argument("--min-delay", 
                       type=float, 
                       default=0.2,
                       metavar="SEC",
                       help="Minimum delay between requests in seconds (default: 0.2)")
    
    parser.add_argument("--max-delay", 
                       type=float, 
                       default=1.0,
                       metavar="SEC",
                       help="Maximum delay between requests in seconds (default: 1.0)")
    
    parser.add_argument("--max-retries", 
                       type=int, 
                       default=3,
                       metavar="N",
                       help="Maximum number of retry attempts (default: 3)")

    args = parser.parse_args()
    
    config = NewsScraperConfig()
    config.headlines_per_category = args.headlines
    config.categories = args.categories
    config.use_csv = args.csv
    config.max_workers = args.workers
    config.output_dir = args.output_dir
    config.include_top_words = args.top_words
    config.min_delay = args.min_delay
    config.max_delay = args.max_delay
    config.max_retries = args.max_retries
    
    try:
        scraper = NewsScraper(config)
        scraper.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
