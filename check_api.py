import requests
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def check():
    print(f"Проверка токена: {TOKEN[:10]}...")
    try:
        # Пробуем через разные эндпоинты
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.json()}")
    except Exception as e:
        print(f"Ошибка при подключении: {e}")

if __name__ == "__main__":
    check()
