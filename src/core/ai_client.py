"""AI client for ChatGPT and Gemini."""
import os, json, logging
from typing import Dict
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self, provider="chatgpt", model=None):
        self.provider = provider
        self.model    = model or os.getenv("DEFAULT_MODEL", "gpt-4.1")

        if provider == "chatgpt":
            import openai
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self._chat = client.chat.completions.create
        elif provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self._chat = genai.GenerativeModel(model_name=self.model)
            self._chat_session = None  # Will hold the persistent chat session
        else:
            raise ValueError(provider)

    def ask(self, messages, json_mode=True) -> Dict:
        """Send chat & return JSON dict (raises if model fails)."""
        if self.provider == "chatgpt":
            resp = self._chat(
                model=self.model,
                messages=messages,
                temperature=0.2,
                response_format={"type": "json_object"} if json_mode else None
            )
            return json.loads(resp.choices[0].message.content)
        else:  # Gemini
            # Either start a new chat session or use an existing one
            if not self._chat_session:
                self._chat_session = self._chat.start_chat(history=[
                    {"role": msg["role"], "parts": [msg["content"]]} 
                    for msg in messages[:-1]  # Convert all but last message to Gemini format
                ])
            
            # Send the latest message to the ongoing chat session
            resp = self._chat_session.send_message(messages[-1]["content"])
            return json.loads(resp.text)
