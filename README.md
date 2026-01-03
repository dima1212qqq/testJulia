# E-commerce Aggregator Bot

This is a Telegram bot that aggregates product prices from Ozon, Wildberries, and Yandex Market using Playwright for scraping and Meilisearch for storage/search.

## Features

- **Live Search**: Scrapes marketplaces on demand.
- **Caching**: Results are stored in Meilisearch for instant retrieval on repeat queries.
- **Anti-bot Handling**: Uses Playwright with stealth techniques (and graceful fallback mocks if blocked).
- **Asynchronous Architecture**: Uses `taskiq` + `redis` for non-blocking task processing.

## Tech Stack

- Python 3.11+
- Aiogram 3.x (Telegram Bot)
- Playwright (Scraping)
- TaskIQ + Redis (Task Queue)
- Meilisearch (Search Engine & Database)

## Setup

### Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (from @BotFather)

### Installation

1. Clone the repo.
2. Create `.env` file:
   ```env
   BOT_TOKEN=your_bot_token
   REDIS_URL=redis://redis:6379
   MEILISEARCH_URL=http://meilisearch:7700
   MEILISEARCH_KEY=masterKey
   ```
3. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

## Local Development (Without Docker)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Start Redis and Meilisearch locally.
3. Start the Worker:
   ```bash
   taskiq worker app.broker:broker
   ```
4. Start the Bot:
   ```bash
   python main.py
   ```

## Project Structure

- `app/bot.py`: Telegram bot entry point.
- `app/tasks.py`: Background tasks (scraping).
- `app/scrapers/`: Scraper logic for each marketplace.
- `app/storage.py`: Meilisearch wrapper.
