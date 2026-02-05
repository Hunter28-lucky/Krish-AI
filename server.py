#!/usr/bin/env python3
"""
Local development server for the AI Chatbot.
Run this to test the chatbot locally before deploying to Vercel.
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
import sys
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import required packages
try:
    import requests
    from bs4 import BeautifulSoup
    from ddgs import DDGS
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install requests beautifulsoup4 ddgs")
    sys.exit(1)

# ============================================
# CONFIGURATION
# ============================================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')
MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
PORT = 3000

# ============================================
# HELPER FUNCTIONS
# ============================================
def search_internet(query, max_results=3):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as e:
        print(f"Search error: {e}")
        return None

def scrape_webpage(url, max_chars=4000):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
        
        title = soup.title.string if soup.title else "No title"
        main = soup.select_one('main, article, .content') or soup.body
        text = main.get_text(separator='\n', strip=True) if main else ""
        text = re.sub(r'\n{3,}', '\n\n', text)[:max_chars]
        
        return {"title": title, "content": text, "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

def extract_urls(text):
    return re.findall(r'https?://[^\s<>"\'}\]]+', text)

def chat_completion(messages):
    response = requests.post(
        url=API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        data=json.dumps({
            "model": MODEL,
            "messages": messages,
            "reasoning": {"enabled": True},
            "provider": {"sort": "throughput"}
        })
    )
    return response.json()

def create_search_plan(user_message):
    plan_messages = [
        {
            "role": "system",
            "content": """Analyze if internet search is needed. Respond with ONLY JSON:
{"needs_search": true/false, "reasoning": "why", "searches": [{"query": "...", "purpose": "..."}]}"""
        },
        {"role": "user", "content": user_message}
    ]
    
    try:
        result = requests.post(
            url=API_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({"model": MODEL, "messages": plan_messages})
        ).json()
        
        if 'choices' in result:
            content = result['choices'][0]['message'].get('content', '').strip()
            if content.startswith('```'):
                content = content.split('\n', 1)[1].rsplit('```', 1)[0]
            return json.loads(content)
    except:
        pass
    return {"needs_search": False, "searches": []}

def execute_search_plan(plan):
    if not plan.get('searches'):
        return "", []
    
    results_text = ""
    executed = []
    
    for search in plan['searches'][:3]:
        query = search.get('query', '')
        if not query:
            continue
        
        results = search_internet(query)
        if results:
            executed.append(search)
            results_text += f"\n--- Search: '{query}' ---\n"
            for r in results:
                results_text += f"• {r.get('title', '')}\n  {r.get('body', '')[:200]}\n  Source: {r.get('href', '')}\n"
    
    if results_text:
        return f"\n[RESEARCH]\n{results_text}\n[END RESEARCH]\nCite sources in your answer.", executed
    return "", []

# ============================================
# HTTP HANDLER
# ============================================
class ChatHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            user_message = data.get('userMessage', '')
            conversation = data.get('messages', [])
            
            print(f"\n📩 User: {user_message[:50]}...")
            
            search_info = {"searches": []}
            context = ""
            
            # Check for URLs
            urls = extract_urls(user_message)
            if urls:
                print(f"🌐 Scraping {len(urls)} URL(s)...")
                for url in urls[:2]:
                    result = scrape_webpage(url)
                    if result.get('status') == 'success':
                        context += f"\n[SCRAPED: {result['title']}]\n{result['content']}\n"
            else:
                # Create search plan
                print("🧠 Creating search plan...")
                plan = create_search_plan(user_message)
                
                if plan.get('needs_search') and plan.get('searches'):
                    print(f"🔍 Executing {len(plan['searches'])} search(es)...")
                    search_context, executed = execute_search_plan(plan)
                    context += search_context
                    search_info = {"searches": executed}
                else:
                    print("✓ No search needed")
            
            # Build API messages
            api_messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Use markdown formatting. Cite sources when available."}
            ]
            for msg in conversation[-10:]:
                api_messages.append(msg)
            api_messages.append({"role": "user", "content": user_message + context})
            
            # Get AI response
            print("🤖 Getting AI response...")
            response = chat_completion(api_messages)
            
            if 'choices' in response:
                content = response['choices'][0]['message'].get('content', '')
            else:
                content = f"Error: {response.get('error', {}).get('message', 'Unknown error')}"
            
            print(f"✅ Response: {content[:50]}...")
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"content": content, "searchInfo": search_info}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        if '/api/' not in args[0]:
            print(f"📄 {args[0]}")

# ============================================
# MAIN
# ============================================
if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════╗
║     🤖 AI Chatbot - Local Development Server     ║
╠══════════════════════════════════════════════════╣
║  Open in browser: http://localhost:{PORT}           ║
║  Press Ctrl+C to stop                            ║
╚══════════════════════════════════════════════════╝
""")
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(('localhost', PORT), ChatHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        server.shutdown()
