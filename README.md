# Close My Bank Account

A searchable database of bank account closure methods and their success rates, compiled from community-reported data on [Doctor of Credit](https://www.doctorofcredit.com/complete-list-of-ways-to-close-bank-accounts-at-each-bank/), updated daily. See an issue? Report it [here](/issues).

## Project Structure

- `frontend/` - SvelteKit web application - I vibe coded this. My intention was to learn Svelte, but the site was so simple that it was basically one shotted.
- `scrape/` - Python scripts for scraping and processing bank closure data

## Setup

### Prerequisites

- Node.js (see `frontend/.nvmrc` for version)
- Python 3.13+ (for scraping)
- [uv](https://github.com/astral-sh/uv) package manager (recommended for Python)

### Environment Variables

Create a `.env` file in the `scrape/` directory:

```bash
GEMINI_API_KEY=your_api_key_here
```

You can obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

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
