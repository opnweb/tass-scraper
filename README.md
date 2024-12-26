# TASS News Scraper

A **powerful and free TASS web scraper** designed to efficiently aggregate news articles from `tass.com`. This data extraction tool enables journalists, researchers, and organizations to gather large datasets of Russian state media content for analysing propaganda patterns and narratives.

## 🔥 Features

- [x] Scrape as many news articles as you need
- [x] Multiple news categories
- [x] Built-in top 10 words analysis algorithm
- [x] Export to both JSON and CSV formats
- [x] Configurable concurrent workers for faster scraping
- [x] Automatic retry mechanism for failed requests
- [x] Adjustable parameters for best performance and personal customization
- [x] Control it through your computer's terminal / command prompt

## ✨ Demonstration (2.5x speed)

![](https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExODAzejh6Z3BsYnQ2dHJ6NnVlYWZ0eGlxajNsbmo2YXBtOTVkNTI1ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/cluf8IiSUkq7uiKwXa/giphy.gif)

## 💿 Setup

### ⊞ Windows
1. Download `tass_scraper` from the [releases folder](releases/windows)
2. Open Command Prompt or PowerShell
3. Navigate to the download location of `tass_scraper`
4. Run the executable using the instructions below

###  macOS
1. Download `tass_scraper` from the [releases folder](releases/macos)
2. Open Terminal
3. Navigate to the download location of `tass_scraper`
4. Make the file executable in your terminal. The `chmod +x` command grants the necessary execute permission to run the program:
   ```powershell
   chmod +x tass_scraper
   ```
5. Run the executable using the instructions below

### 🗂️ Compile from source
1. Clone this repository or copy the code from the [source file](source%20code/tass_scraper.py)
2. Install Python 3.8 or higher
3. Install the required libraries for the scraper:
   ```powershell
   pip install requests beautifulsoup4 lxml
   ```
4. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
5. Create an executable file:
   ```powershell
   pyinstaller --name tass_scraper --onefile --console --clean tass_scraper.py
   ```
   
### 🐍 Run as a Python file
Alternatively, you can simply run it as a [Python scraper](source%20code/tass_scraper.py) in your environment.
1. You must have Python installed (3.8 or higher)
2. You must install the required `requests`, `beautifulsoup4`, and `lxml` libraries
3. For ease of use, run the `.py` file from your terminal. For example:
```powershell
python3 tass_scraper.py --headlines 100 --categories politics
```


## 🛠️ How to use TASS scraper

### 1. Navigate to the scraper folder

First, navigate to the folder where `tass_scraper` is located on your computer, for example:


**On Windows:**
```powershell
cd C:/Users/my-user/projects/tass_news
```
-----


**On macOS:**

```powershell
cd /Users/my-user/projects/tass_news
```
-----
### 2. Run the TASS scraper


Basic usage with default settings _(scrapes 20 news articles from each category)_:
```powershell
./tass_scraper
```
-----

> [!NOTE]
> The scraper outputs data to the same directory from where you ran it. For example, if you run the scraper from `C:/Users/my-user`, the `news_data` folder will be saved in the same path.

Example with custom parameters:
```powershell
./tass_scraper --headlines 50 --categories world politics defense --workers 5 --csv --top-words
```
-----

> [!CAUTION]
> Use a reasonable value for `--workers`. The default is `2` workers, which is good for most tasks. A good rule of thumb is to set workers to the number of CPU cores for optimal performance. Too many workers can overload your system and reduce efficiency. Additionally, TASS **may block your IP address** if you make too many requests per minute.


You can use as many paramters as you need.

If you want to specify your custom folder where to save all the data, you can do it using the `--output-dir` flag, for instance:

```powershell
./tass_scraper --output-dir /Users/my-user/Documents/my-custom-folder
```



## ⚙️ All Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `-h` | - | View the help page |
| `--headlines` | `20` | Number of headlines to scrape per category |
| `--categories` | `all` | Categories to scrape (see available categories below) |
| `--csv` | `false` | Save output in CSV format instead of JSON |
| `--workers` | `2` | Maximum number of concurrent workers |
| `--output-dir` | `./news_data` | Output directory for scraped data |
| `--top-words` | `false` | Enable top 10 words analysis |
| `--min-delay` | `0.2` | Minimum delay between requests in seconds |
| `--max-delay` | `1.0` | Maximum delay between requests in seconds |
| `--max-retries` | `3` | Maximum number of retry attempts |

### 📚 Available Categories
- `politics`: Russian Politics & Diplomacy
- `world`: World
- `economy`: Business & Economy
- `defense`: Military & Defense
- `science`: Science & Space
- `emergencies`: Emergencies
- `society`: Society & Culture
- `pressreview`: Press Review
- `sports`: Sports

## 📤 Output

The scraper creates a directory named `news_data` (or your specified output directory) containing:
- One file per category (JSON or CSV) with scraped articles (see both examples [here](example%20outputs))
- A `logs` subdirectory with detailed execution logs

### JSON Output Format

See an [example JSON file](example%20outputs/politics_20.json) with 20 headlines and analysed top words.

```json
[
    {
        "...": "..."
    },
    {
        "title": "Lavrov to hold online news conference on December 26 — spokeswoman",
        "description": "Maria Zakharova underlined that there is a lot of topics",
        "date": "2024-12-24 15:00:33",
        "link": "https://tass.com/politics/1892567",
        "content": [
            "Maria Zakharova underlined that there is a lot of topics",
            "MOSCOW, December 24. /TASS/. Russian Foreign Minister Sergey Lavrov will hold an online news conference for foreign journalists on December 26, Russian Foreign Ministry Spokeswoman Maria Zakharova said.",
            "\"The day after tomorrow (December 26 - TASS), the top Russian diplomat will speak with foreign correspondents,\" she told the Rossiya-24 television channel.",
            "\"It is going to be hot because there is a lot of topics. He will outline the conclusions on some aspects of the international situation,\" she said, adding that Lavrov’s plans for December 25 also include an interview with the 60 Minutes program on the Rossiya-1 television channel."
        ]
    },
    {
        "...": "..."
    }
]
```

### CSV Output Format

See an [example CSV file](example%20outputs/politics_20.csv) with 20 headlines and analysed top words.

Each article is flattened into a single row with columns:
- title
- description
- date
- link
- content
- top_word_1 to top_word_10 (if enabled)
- top_word_1_count to top_word_10_count (if enabled)
