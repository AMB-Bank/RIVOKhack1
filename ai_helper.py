import os
import json
import asyncio
from duckduckgo_search import DDGS
import google.generativeai as genai

# Настройка ключей
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Ошибка настройки Gemini: {e}")
        gemini_model = None
else:
    gemini_model = None

async def search_educational_resources(query: str):
    """
    Выполняет поиск реальных образовательных ресурсов.
    """
    results = []
    try:
        ddgs = DDGS()
        search_queries = [
            f"site:vk.com/video {query}",
            f"{query} образовательный материал",
            f"{query} урок видео"
        ]
        
        for sq in search_queries:
            try:
                # Ограничиваем время поиска
                search_results = list(ddgs.text(sq, max_results=2))
                for r in search_results:
                    results.append({"title": r['title'], "link": r['href']})
            except Exception as e:
                print(f"Search sub-query error: {e}")
        
        # Убираем дубликаты
        unique_results = []
        seen_links = set()
        for r in results:
            if r['link'] not in seen_links:
                unique_results.append(r)
                seen_links.add(r['link'])
        return unique_results[:5]
                
    except Exception as e:
        print(f"Global search error: {e}")
        
    return results

async def solve_problem(query: str, system_prompt: str = "Ты — помощник в учебе. Отвечай на русском языке."):
    """
    Основная функция для решения задач.
    """
    is_material_request = any(word in query.lower() for word in ["ссылки", "материалы", "видео", "почитать", "изучить"])
    
    context_info = ""
    
    if is_material_request:
        # Извлекаем тему для поиска
        topic = query
        if gemini_model:
            try:
                topic_resp = gemini_model.generate_content(f"Извлеки только тему (2-3 слова) из запроса: {query}")
                topic = topic_resp.text.strip()
            except: pass
        
        real_links = await search_educational_resources(topic)
        if real_links:
            links_str = "\n".join([f"- [{l['title']}]({l['link']})" for l in real_links])
            context_info = f"\n\nВот реальные найденные ссылки:\n{links_str}\n\nИспользуй их в ответе."
        else:
            context_info = "\n\n(Реальных ссылок не найдено, дай общие рекомендации)."

    # Попытка вызвать AI
    try:
        full_prompt = f"{system_prompt}\n\nПользователь: {query}{context_info}"
        
        # 1. Пробуем Gemini если есть ключ
        if gemini_model:
            response = gemini_model.generate_content(full_prompt)
            return response.text

        # 2. Пробуем OpenAI (системный Manus или пользовательский)
        from openai import OpenAI
        client = OpenAI() # Использует ключ из окружения
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query + context_info}
            ]
        )
        return resp.choices[0].message.content
        
    except Exception as e:
        err_msg = str(e)
        if "402" in err_msg or "credits" in err_msg:
            return "❌ Ошибка: На балансе OpenAI закончились средства. Пожалуйста, добавьте GEMINI_API_KEY в файл .env для бесплатной работы."
        return f"❌ Ошибка AI: {err_msg[:100]}"
