import httpx
import json
from typing import List, Dict, Optional
from app.config import settings
from app.schemas import AIRequest, AIResponse


class AIService:
    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_response(self, messages: List[Dict]) -> AIResponse:
        """Генерация ответа от AI"""
        
        # Форматируем сообщения для OpenAI API
        formatted_messages = []
        for msg in messages:
            role = "user" if msg["sender"] == "user" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": msg["content"]
            })
        
        # Добавляем системное сообщение
        system_message = {
            "role": "system",
            "content": "Ты полезный AI ассистент. Отвечай на русском языке. Будь вежливым и полезным."
        }
        formatted_messages.insert(0, system_message)
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens_used = data["usage"]["total_tokens"]
                    
                    return AIResponseResponse(
                        content=content,
                        tokens_used=tokens_used
                    )
                else:
                    error_msg = f"AI API Error: {response.status_code} - {response.text}"
                    raise Exception(error_msg)
                    
            except httpx.RequestError as e e:
                raise Exception(f"Request failed: {str(e)}")
    
    def format_chat_history(self, messages: List[Dict]) -> str:
        """Форматирование истории чата для контекста"""
        history = []
        for msg in messages[-10:]:  # Берем последние 10 сообщений
            sender = "Пользователь" if msg["sender"] == "user" else "Ассистент"
            history.append(f"{sender}: {msg['content']}")
        
        return "\n".join(history)


# Альтернативный вариант - локальная модель (например, через transformers)
class LocalAIService:
    """Локальный AI сервис для тестирования без API ключа"""
    
    async def generate_response(self, messages: List[Dict]) -> AIResponse:
        # Простой эхо-бот для тестирования
        last_message = messages[-1]["content"] if messages else "Привет!"
        
        responses = [
            f"Я получил ваше сообщение: '{last_message}'. Чем еще могу помочь?",
            f"Понял вас: '{last_message}'. Есть что-то еще?",
            f"Спасибо за сообщение! '{last_message}' - интересно. Что дальше?",
            f"Записал: '{last_message}'. Продолжаем диалог!",
            f"Отличный вопрос! '{last_message}'. Что вы думаете об этом?"
        ]
        
        import random
        response = random.choice(responses)
        
        return AIResponse(
            content=response,
            tokens_used=len(response.split())
        )


# Выбор сервиса в зависимости от наличия API ключа
if settings.AI_API_KEY and settings.AI_API_KEY != "your-openai-api-key":
    ai_service = AIService()
else:
    print("⚠️  OpenAI API ключ не найден. Используется локальный эхо-бот для тестирования.")
    ai_service = LocalAIService()
