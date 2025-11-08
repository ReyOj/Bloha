"""AI helper for generating responses using OpenAI API."""
import os
from typing import Optional
import openai

# Инициализация клиента OpenAI
openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_ai_advice(query: str) -> Optional[str]:
    """Генерирует мудрый совет или цитату с помощью OpenAI.
    
    Args:
        query: Текст запроса/ситуации, для которой нужен совет
        
    Returns:
        str: Сгенерированный текст совета/цитаты или None если API недоступен
    """
    if not openai.api_key:
        return "Мудрец сегодня недоступен. Попробуйте позже."
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "Ты — мудрый советчик. Отвечай короткими, но глубокими цитатами "
                    "или советами в стиле дзен-буддизма. Ответ должен быть не длиннее "
                    "1 предложения и содержать мудрость, применимую к ситуации."
                )},
                {"role": "user", "content": query}
            ],
            max_tokens=100,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "Мудрец погрузился в медитацию. Попробуйте позже."