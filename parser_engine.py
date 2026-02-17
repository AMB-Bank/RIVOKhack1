import re
import datetime
from ai_helper import split_task_into_steps

class DataParser:
    """
    Архитектура: Принять - Обработать - Отдать
    Этот класс отвечает за интеллектуальный разбор пользовательского ввода и его трансформацию в структурированные данные.
    """
    
    @staticmethod
    async def accept_input(raw_text: str):
        """
        ПРИНЯТЬ: Получение сырого текста от пользователя.
        """
        return raw_text.strip()

    @staticmethod
    async def process_task(text: str):
        """
        ОБРАБОТАТЬ: Анализ текста, извлечение предмета и дедлайна, декомпозиция задачи.
        """
        # 1. Извлечение предмета (первое слово или слово перед двоеточием)
        subject = "Общее"
        match_subject = re.match(r"^([\w\s]+):", text)
        if match_subject:
            subject = match_subject.group(1).strip()
            text = text[len(match_subject.group(0)):].strip()
        
        # 2. Поиск даты (простой парсер для примера)
        deadline = datetime.datetime.now() + datetime.timedelta(days=1)
        if "завтра" in text.lower():
            deadline = datetime.datetime.now() + datetime.timedelta(days=1)
        elif "послезавтра" in text.lower():
            deadline = datetime.datetime.now() + datetime.timedelta(days=2)
            
        # 3. Декомпозиция через AI
        steps = await split_task_into_steps(text)
        
        return {
            "subject": subject,
            "description": text,
            "deadline": deadline,
            "steps": steps
        }

    @staticmethod
    async def deliver_response(processed_data: dict):
        """
        ОТДАТЬ: Формирование финального ответа для пользователя.
        """
        response = f"✅ **Задание принято и обработано!**\n\n"
        response += f"📚 **Предмет:** {processed_data['subject']}\n"
        response += f"📅 **Дедлайн:** {processed_data['deadline'].strftime('%d.%m.%Y')}\n\n"
        response += f"📝 **План выполнения:**\n{processed_data['steps']}\n\n"
        response += "Удачи с выполнением! Я напомню тебе о дедлайне. 😉"
        return response

async def handle_user_task_input(raw_text: str):
    """
    Pipeline: Accept -> Process -> Deliver
    """
    # Accept
    input_text = await DataParser.accept_input(raw_text)
    
    # Process
    processed_data = await DataParser.process_task(input_text)
    
    # Deliver
    final_output = await DataParser.deliver_response(processed_data)
    
    return final_output, processed_data
