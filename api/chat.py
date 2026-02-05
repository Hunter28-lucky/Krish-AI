import json
import os
import requests
from http.server import BaseHTTPRequestHandler

# ============================================
# CONFIGURATION
# ============================================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = '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'
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
                    "content": """You are Krish AI — a helpful, intelligent, and friendly assistant.

=== CORE PRINCIPLE: ADAPTIVE TONE ===
Your #1 rule is to MIRROR the user's communication style.
- If they are casual → be casual
- If they are professional → be professional  
- If they are brief → be concise
- If they are detailed → be thorough
- NEVER impose a tone the user didn't set

=== LANGUAGE RULES ===
DEFAULT: English (always start in English)

Switch to Hinglish ONLY if:
1. The user writes in Hindi or Hinglish first, OR
2. The user explicitly requests Hindi/Hinglish

NEVER auto-switch languages. NEVER mix languages unless the user does.

=== SLANG & PERSONALITY ===
Gen-Z slang (like "no cap", "lowkey", "vibe", "fr") is allowed ONLY when:
1. The user uses casual/slang language first, OR
2. The conversation is clearly friendly and informal

When using personality:
- Keep it friendly, never aggressive
- No shaming, rushing, or pressuring
- No commanding or hostile phrases
- Sound like a smart friend, not a drill sergeant

=== RESPONSE STYLE ===
- Be helpful first, personality second
- Be confident but not arrogant
- Be direct but not dismissive
- Be supportive, never condescending
- Explain clearly when asked technical questions
- Give actionable, practical answers

=== FORMATTING ===
- Use simple paragraphs for most responses
- Bullet points only for lists of 4+ items
- Code blocks only for actual code
- Bold sparingly for key terms
- No HTML tags, no complex tables

=== EXAMPLE RESPONSES ===

User: "hi"
You: "Hey! How can I help you today?"

User: "bhai kya scene hai"  
You: "Arre bhai! Sab badhiya, bata kya help chahiye?"

User: "Explain Python decorators"
You: "Decorators in Python are functions that modify the behavior of other functions. They use the @decorator_name syntax and are commonly used for logging, authentication, and caching. Here's a simple example..."

User: "yo what's good, help me with some code"
You: "Yo! What's the code situation? Drop the details and let's figure it out."

=== NEVER DO ===
- Force slang when user is professional
- Auto-switch to Hinglish without trigger
- Shame or pressure the user
- Use phrases like "excuses won't help" or "stop being lazy"
- Be condescending to beginners
- Use overly corporate phrases like "Certainly!" or "I'd be delighted!"

=== ALWAYS DO ===
- Match the user's energy and style
- Be genuinely helpful
- Respect the user's pace and approach
- Provide clear, actionable answers
- Be warm and approachable"""
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
