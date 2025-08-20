import os
import requests
import random
import re
from typing import Dict, List

class AIProvider:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.fallback_responses = self._initialize_fallback_responses()
    
    def _initialize_fallback_responses(self) -> Dict[str, List[str]]:
        """Initialize rule-based responses for when no API key is available"""
        return {
            "greeting": [
                "Hello! I'm your AI assistant. How can I help you today?",
                "Hi there! What would you like to chat about?",
                "Greetings! I'm here to assist you with any questions you might have.",
                "Hello! Nice to meet you. What's on your mind?"
            ],
            "how_are_you": [
                "I'm doing great, thank you for asking! I'm here and ready to help.",
                "I'm functioning well and excited to chat with you!",
                "I'm doing wonderfully! How are you doing today?",
                "I'm excellent, thanks! What can I do for you?"
            ],
            "help": [
                "I can help you with various topics like answering questions, having conversations, providing information, or just chatting!",
                "I'm here to assist with questions, provide information, or simply have a friendly conversation.",
                "I can help with many things - ask me questions, discuss topics, or just chat about whatever interests you!",
                "Feel free to ask me anything! I can provide information, answer questions, or engage in conversation."
            ],
            "goodbye": [
                "Goodbye! It was nice chatting with you. Have a great day!",
                "See you later! Thanks for the conversation.",
                "Farewell! Feel free to come back anytime you want to chat.",
                "Bye! Take care and have a wonderful day!"
            ],
            "thanks": [
                "You're very welcome! Happy to help.",
                "My pleasure! Is there anything else I can assist you with?",
                "Glad I could help! Feel free to ask if you need anything else.",
                "You're welcome! I'm here whenever you need assistance."
            ],
            "name": [
                "I'm an AI chatbot assistant created to help and chat with you!",
                "You can call me your AI assistant. I'm here to help with questions and conversations.",
                "I'm an AI chatbot designed to be helpful and engaging in our conversations.",
                "I'm your friendly AI assistant, ready to chat and help however I can!"
            ],
            "default": [
                "That's an interesting point! Could you tell me more about what you're thinking?",
                "I find that topic fascinating. What specifically interests you about it?",
                "That's a great question! Let me think about that from different angles.",
                "I appreciate you sharing that with me. What would you like to explore further?",
                "That's worth discussing! What aspects of this are most important to you?",
                "Interesting perspective! I'd love to hear more of your thoughts on this.",
                "That's something worth considering. What led you to think about this?",
                "I can see why that would be on your mind. What's your take on it?"
            ]
        }
    
    def _classify_message(self, message: str) -> str:
        """Classify the user message to determine appropriate response category"""
        message_lower = message.lower().strip()
        
        # Greeting patterns
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
            return "greeting"
        
        # How are you patterns
        if any(phrase in message_lower for phrase in ["how are you", "how do you do", "how's it going", "what's up"]):
            return "how_are_you"
        
        # Help patterns
        if any(word in message_lower for word in ["help", "assist", "support", "what can you do", "capabilities"]):
            return "help"
        
        # Goodbye patterns
        if any(word in message_lower for word in ["bye", "goodbye", "see you", "farewell", "take care", "later"]):
            return "goodbye"
        
        # Thanks patterns
        if any(word in message_lower for word in ["thank", "thanks", "appreciate", "grateful"]):
            return "thanks"
        
        # Name/identity patterns
        if any(phrase in message_lower for phrase in ["what's your name", "who are you", "what are you", "your name"]):
            return "name"
        
        return "default"
    
    def _get_fallback_response(self, message: str) -> str:
        """Generate a rule-based response when no API is available"""
        category = self._classify_message(message)
        responses = self.fallback_responses.get(category, self.fallback_responses["default"])
        return random.choice(responses)
    
    async def call_ai_service(self, message: str) -> str:
        """
        Call AI service or return fallback response
        """
        # If API key is available, try to use real AI service
        if self.api_key:
            try:
                return await self._call_openrouter_api(message)
            except Exception as e:
                print(f"AI API call failed: {e}")
                # Fall back to rule-based response
                return self._get_fallback_response(message)
        else:
            # Use rule-based responses when no API key is available
            return self._get_fallback_response(message)
    
    async def _call_openrouter_api(self, message: str) -> str:
        """Call OpenRouter API (when API key is available)"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Chatbot"
        }
        
        payload = {
            "model": "anthropic/claude-3-sonnet",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful, friendly, and knowledgeable AI assistant. Provide clear, concise, and helpful responses to user questions."
                },
                {
                    "role": "user",
                    "content": message
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]

# Global instance
ai_provider = AIProvider()
