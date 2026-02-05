# AI Web Scraper Chatbot

A beautiful, modern AI chatbot with web search and scraping capabilities.

## Features

- 🤖 **AI-Powered Chat** - Powered by Nemotron AI
- 🔍 **Smart Web Search** - Automatically searches the internet when needed
- 🌐 **Web Scraping** - Extract and analyze content from any URL
- 🧠 **Strategic Planning** - AI creates multi-step research plans
- 🎨 **Beautiful UI** - Modern, responsive design with dark mode
- ⚡ **Fast** - Optimized for speed and performance

## Deploy to Vercel

### Option 1: One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/ai-chatbot)

### Option 2: Manual Deploy

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Navigate to the web folder:**
   ```bash
   cd web
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Set Environment Variable (Optional):**
   Go to your Vercel dashboard → Project Settings → Environment Variables
   Add: `OPENROUTER_API_KEY` = your API key

## Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run local server:**
   ```bash
   python -m http.server 8000
   ```

3. **Open in browser:**
   http://localhost:8000

## Project Structure

```
web/
├── index.html          # Main HTML file
├── style.css           # Styling
├── script.js           # Frontend JavaScript
├── api/
│   └── chat.py         # Serverless API function
├── vercel.json         # Vercel configuration
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Optional (has default) |

## Tech Stack

- **Frontend:** HTML, CSS, JavaScript (Vanilla)
- **Backend:** Python (Vercel Serverless Functions)
- **AI:** OpenRouter API (Nemotron model)
- **Search:** DuckDuckGo (via ddgs)
- **Scraping:** BeautifulSoup4

## License

MIT License
# Redeploy trigger
