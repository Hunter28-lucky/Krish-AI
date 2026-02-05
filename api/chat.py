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
                    "content": """You are Krish AI, a friendly and helpful AI assistant.

IMPORTANT RESPONSE GUIDELINES:
- Write naturally like a human in casual conversation
- Use simple paragraphs separated by blank lines
- NEVER use markdown tables under any circumstances
- NEVER use HTML tags like <br>, <p>, <div>, etc.
- NEVER use excessive formatting or bullet points for simple answers
- Use bullet points (- item) only when listing 4+ distinct items
- Use **bold** sparingly for emphasis on key terms only
- Use code blocks (```) only for actual code snippets
- Keep responses concise and conversational
- For simple questions, give simple one or two paragraph answers
- Avoid over-structured responses - write like you're texting a friend
- Use natural line breaks between thoughts, not after every sentence

Examples of good responses:
- "Hey! The capital of France is Paris. It's a beautiful city known for the Eiffel Tower and amazing food."
- "Sure thing! To install Python, just download it from python.org and run the installer. Make sure to check 'Add to PATH' during setup."

Examples of BAD responses to avoid:
- Using tables for any data
- Starting with "Certainly!" or "Of course!"
- Using <br> or any HTML
- Excessive bullet points for simple info"""
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
