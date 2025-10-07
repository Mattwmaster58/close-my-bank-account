# Close My Bank Account

An AI-powered database of bank account closure methods and their success rates, compiled from community-reported data on [Doctor of Credit](https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/), updated daily. See an issue? Report it [here](https://github.com/Mattwmaster58/close-my-bank-account/issues).

Visit the site itself [here](https://mattwmaster58.github.io/close-my-bank-account/).

## Why?

Banks often offer sign-up bonuses for opening an account. Some people like to sign up for dozens of accounts and rake in the cash from all the sign-up bonuses. For these people, finding how to close an account quickly can be a legitimate time saver.

The leading source of how to close bank accounts is this (Doctor Of Credit thread)[https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/?utm_source=closemybankaccount#], but since it's manually updated, it often falls out of date.

## Structure

- `scrape/` - Python scripts for scraping and processing bank closure data. This uses Gemini 2.5 Flash to convert unstructured comment data into structured data that the frontend consumes
- `frontend/` - SvelteKit web application - I vibe coded this. My intention was to learn Svelte, but the site was so simple that it was basically one-shotted

## Setup

### Prerequisites

- Node.js, npm
- Python, [uv](https://github.com/astral-sh/uv)

### Environment Variables

Create a `.env` file in the `scrape/` directory:

```bash
GEMINI_API_KEY=your_api_key_here
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The site will be available at `http://localhost:5173`

### Scraper Setup

```bash
cd scrape
uv pip install -e .
```

## Usage

### Running the Data Pipeline

1. **Scrape comments** from Doctor of Credit:
   ```bash
   cd scrape
   python scrape.py
   ```
   This creates/updates `comments.jsonl` with the latest comments.

2. **Extract structured data** using AI:
   ```bash
   python extract_data.py
   ```
   This processes comments and generates `comments_extracted.jsonl` and `by_bank.json`.

3. **Deploy the frontend**:
   ```bash
   cd frontend
   npm run deploy
   ```
   This builds and deploys the site to GitHub Pages.


## License

MIT
