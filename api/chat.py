import json
import re
import os
import requests

# Try to import optional packages
try:
    from bs4 import BeautifulSoup
    from duckduckgo_search import DDGS
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

# ============================================
# CONFIGURATION
# ============================================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')
MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"

# ============================================
# HELPER FUNCTIONS
# ============================================
def search_internet(query, max_results=3):
    """Search the internet using DuckDuckGo."""
    if not DEPENDENCIES_AVAILABLE:
        return None
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return results
    except Exception as e:
        print(f"Search error: {e}")
        return None

def scrape_webpage(url, max_chars=4000):
    """Scrape content from a webpage."""
    if not DEPENDENCIES_AVAILABLE:
        return {"error": "Dependencies not available", "status": "error"}
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        title = soup.title.string if soup.title else "No title"
        
        main_content = None
        for selector in ['main', 'article', '[role="main"]', '.content', '#content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.body if soup.body else soup
        
        text = main_content.get_text(separator='\n', strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        if len(text) > max_chars:
            text = text[:max_chars] + "...[truncated]"
        
        return {"url": url, "title": title, "content": text, "status": "success"}
        
    except Exception as e:
        return {"error": str(e), "status": "error"}

def extract_urls(text):
    """Extract URLs from text."""
    url_pattern = r'https?://[^\s<>"\'}\])]+'
    return re.findall(url_pattern, text)

def chat_completion(messages):
    """Send messages to the API."""
    response = requests.post(
        url=API_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": MODEL,
            "messages": messages,
            "provider": {"sort": "throughput"}
        })
    )
    return response.json()

def create_search_plan(user_message):
    """AI creates a strategic plan for searching."""
    plan_messages = [
        {
            "role": "system",
            "content": """You are an intelligent research assistant. Analyze the user's question and decide if internet search is needed.

Respond with ONLY a JSON object:
{
    "needs_search": true/false,
    "reasoning": "Brief explanation",
    "searches": [
        {"query": "search query 1", "purpose": "what this finds"},
        {"query": "search query 2", "purpose": "what this finds"}
    ]
}

Search IS needed for: current events, news, real-time info, recent products, specific facts.
Search NOT needed for: general knowledge, math, coding, creative writing, historical facts.

Respond with ONLY JSON."""
        },
        {"role": "user", "content": user_message}
    ]
    
    try:
        response = requests.post(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({"model": MODEL, "messages": plan_messages})
        )
        result = response.json()
        
        if 'choices' in result:
            content = result['choices'][0]['message'].get('content', '')
            content = content.strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content
                content = content.rsplit('```', 1)[0] if '```' in content else content
            
            return json.loads(content)
    except:
        pass
    
    return {"needs_search": False, "reasoning": "", "searches": []}

def execute_search_plan(plan):
    """Execute the search plan and gather results."""
    if not plan.get('searches'):
        return "", []
    
    all_results = []
    executed_searches = []
    
    for search in plan['searches'][:3]:
        query = search.get('query', '')
        purpose = search.get('purpose', '')
        
        if not query:
            continue
        
        results = search_internet(query, max_results=3)
        
        if results:
            executed_searches.append({"query": query, "purpose": purpose})
            search_block = f"\n--- Search: '{query}' ---\n"
            for j, result in enumerate(results, 1):
                title = result.get('title', 'No title')
                body = result.get('body', '')[:300]
                href = result.get('href', '')
                search_block += f"\n{j}. {title}\n   {body}\n   Source: {href}\n"
            all_results.append(search_block)
    
    if all_results:
        combined = "\n\n[RESEARCH RESULTS]\n"
        combined += f"Strategy: {plan.get('reasoning', 'N/A')}\n"
        combined += "\n".join(all_results)
        combined += "\n[END RESEARCH RESULTS]\n"
        combined += "\nUse the research above to provide a comprehensive answer. Cite sources."
        return combined, executed_searches
    
    return "", []

# ============================================
# VERCEL SERVERLESS HANDLER
# ============================================
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            user_message = data.get('userMessage', '')
            conversation = data.get('messages', [])
            
            search_info = {"searches": []}
            context = ""
            
            # Check for URLs to scrape
            urls = extract_urls(user_message)
            if urls and DEPENDENCIES_AVAILABLE:
                for url in urls[:2]:
                    result = scrape_webpage(url)
                    if result.get('status') == 'success':
                        context += f"\n\n[SCRAPED: {result['title']}]\n{result['content']}\n[END SCRAPED]\n"
            
            # Create search plan if no URLs
            if not urls and DEPENDENCIES_AVAILABLE:
                plan = create_search_plan(user_message)
                
                if plan.get('needs_search') and plan.get('searches'):
                    search_context, executed = execute_search_plan(plan)
                    context += search_context
                    search_info = {"searches": executed, "reasoning": plan.get('reasoning', '')}
            
            # Build messages for API
            api_messages = [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant with web search capabilities. Provide comprehensive, well-formatted answers. Use markdown for formatting. Cite sources when using search results."
                }
            ]
            
            # Add conversation history
            for msg in conversation[-10:]:
                api_messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
            
            # Add current message with context
            if context:
                api_messages.append({
                    "role": "user",
                    "content": user_message + context
                })
            else:
                api_messages.append({
                    "role": "user", 
                    "content": user_message
                })
            
            # Get response from AI
            ai_response = chat_completion(api_messages)
            
            if 'choices' in ai_response:
                content = ai_response['choices'][0]['message'].get('content', '')
            else:
                error_msg = ai_response.get('error', {}).get('message', 'Unknown error')
                content = f"I'm sorry, I couldn't process your request. Error: {error_msg}"
            
            response_data = {
                "content": content,
                "searchInfo": search_info
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
