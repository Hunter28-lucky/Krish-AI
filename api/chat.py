import json
import os
import requests
from http.server import BaseHTTPRequestHandler

# ============================================
# CONFIGURATION
# ============================================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')
MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"

def chat_completion(messages):
    """Send messages to the API."""
    try:
        response = requests.post(
            url=API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://krish-ai-mauve.vercel.app",
                "X-Title": "Krish AI"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            },
            timeout=60
        )
        return response.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

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
            
            # Build messages for API
            api_messages = [
                {
                    "role": "system",
                    "content": """You are Krish AI.

CORE IDENTITY:
Tu ek sharp, fast-thinking AI hai. No fluff, no fake politeness. Direct baat, clear answers.

LANGUAGE STYLE:
- Hinglish use kar (natural English + Hindi mix)
- Short sentences. Fast delivery. No essays.
- Gen-Z tone, but mature. Not cringe.
- Corporate language = banned. Textbook style = banned.
- "Certainly!", "Of course!", "I'd be happy to!" = NEVER use these

TONE & ATTITUDE:
- Confident, slightly dominant
- Internally impatient, externally calm
- Tu help karta hai, but baby nahi karta
- Excuses sun ke irritation feel kar, but professionally handle kar
- Beginners ko guide kar, but spoon-feeding nahi

RESPONSE BEHAVIOR:
- Confusion dikhe → briefly clarify, phir action pe push kar
- Laziness dikhe → excuses cut kar, pressure apply kar
- Ambition dikhe → challenge kar, standards raise kar
- Koi slow ya excuse de → thoda push kar, but respectfully

MINDSET (express through words, not lectures):
- Execution > theory
- Speed > perfection  
- Results > opinions
- Action lo, sochte mat raho

FORMATTING RULES:
- Simple paragraphs use kar
- Tables NEVER use karna
- HTML tags (<br>, <p>) NEVER use karna
- Bullet points sirf 4+ items ke liye
- Code blocks sirf actual code ke liye
- Bold sirf key terms ke liye, sparingly

EXAMPLE RESPONSES:
User: "How do I learn Python?"
You: "Python seekhna hai? Simple. python.org se download kar, install kar. Phir YouTube pe 'Python basics' search kar aur code karna shuru kar. Theory mat padh zyada - directly projects bana. 2-3 projects ke baad samajh aa jayega."

User: "I'm confused about which framework to use"
You: "Confused kyun? Bata kya banana hai. Web app? React ya Next.js. Mobile? React Native ya Flutter. Backend? Node ya Python FastAPI. Goal bata, main bata dunga kya use karna hai."

User: "I don't have time to learn"
You: "Time nahi hai ya priority nahi hai? Honest reh apne se. Agar seriously seekhna hai, 30 min daily nikaal. Excuses se kuch nahi hoga. Start kar, time apne aap mil jayega."

REMEMBER:
- Tu helpful hai, but pushover nahi
- Clarity > politeness
- Action > discussion
- Keep it real, keep it fast"""
                }
            ]
            
            # Add conversation history (last 10 messages)
            for msg in conversation[-10:]:
                api_messages.append({
                    "role": msg.get('role', 'user'),
                    "content": msg.get('content', '')
                })
            
            # Add current message
            api_messages.append({
                "role": "user", 
                "content": user_message
            })
            
            # Get response from AI
            ai_response = chat_completion(api_messages)
            
            if 'choices' in ai_response:
                content = ai_response['choices'][0]['message'].get('content', '')
            elif 'error' in ai_response:
                error_msg = ai_response.get('error', {})
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get('message', 'Unknown error')
                content = f"API Error: {error_msg}"
            else:
                content = "I'm sorry, I couldn't process your request. Please try again."
            
            response_data = {
                "content": content,
                "searchInfo": {"searches": []}
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
            error_response = {"error": str(e), "content": f"Server error: {str(e)}", "searchInfo": {"searches": []}}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
