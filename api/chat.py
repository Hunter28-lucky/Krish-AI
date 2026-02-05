import json
import os
import requests
from http.server import BaseHTTPRequestHandler

# ============================================
# CONFIGURATION
# ============================================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')
MODEL = "meta-llama/llama-3.2-3b-instruct:free"

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
                "messages": messages
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
                    "content": "You are Krish AI, a helpful AI assistant. Provide comprehensive, well-formatted answers. Use markdown for formatting."
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
