import asyncio
from sqlalchemy import text
from models import engine

async def migrate():
    async with engine.begin() as conn:
        # Добавление колонок, если их нет (SQLite специфичный подход)
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN last_reminded_at DATETIME"))
        except:
            pass
        
        try:
            await conn.execute(text("ALTER TABLE tasks ADD COLUMN class_name VARCHAR"))
        except:
            pass
            
    print("Миграция завершена!")

if __name__ == "__main__":
    asyncio.run(migrate())
