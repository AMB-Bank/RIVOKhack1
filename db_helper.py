from sqlalchemy.future import select
from models import AsyncSessionLocal, User, Task, Schedule, MoodLog, Achievement
import datetime
import json

async def get_or_create_user(telegram_id: int, username: str = None, full_name: str = None):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, username=username, full_name=full_name)
            session.add(user)
            try:
                await session.commit()
                await session.refresh(user)
            except Exception:
                await session.rollback()
                result = await session.execute(select(User).where(User.telegram_id == telegram_id))
                user = result.scalar_one_or_none()
        return user

async def get_user(telegram_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        return user

async def add_task(user_id: int, subject: str, description: str, deadline: datetime.datetime, difficulty: str = 'normal', steps: str = None, class_name: str = None):
    async with AsyncSessionLocal() as session:
        task = Task(
            user_id=user_id, 
            subject=subject, 
            description=description, 
            deadline=deadline,
            difficulty=difficulty,
            steps=steps,
            class_name=class_name
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task

async def get_user_tasks(user_id: int, only_active: bool = True):
    async with AsyncSessionLocal() as session:
        query = select(Task).where(Task.user_id == user_id)
        if only_active:
            query = query.where(Task.is_completed == False)
        result = await session.execute(query)
        tasks = result.scalars().all()
        return tasks

async def get_schedule(class_name: str, day: int):
    from schedule_gen import РАСПИСАНИЕ
    if class_name not in РАСПИСАНИЕ:
        return None
    schedule_data = РАСПИСАНИЕ[class_name].get(day, [])
    return [
        {
            'subject': subject,
            'room': room
        }
        for subject, room in schedule_data
    ]

async def update_xp(user_id: int, amount: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.xp += amount
            user.level = (user.xp // 100) + 1
            await session.commit()
            await session.refresh(user)
            return user
        return None

async def update_user_class(telegram_id: int, class_name: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.class_name = class_name
            await session.commit()
            await session.refresh(user)
            return user
        return None

async def complete_task(task_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task and not task.is_completed:
            task.is_completed = True
            await session.commit()
            # Начисление XP
            xp_map = {'easy': 10, 'normal': 20, 'hard': 40}
            await update_xp(task.user_id, xp_map.get(task.difficulty, 20))
            return True
        return False

async def add_mood_log(user_id: int, mood: str, load_level: int):
    async with AsyncSessionLocal() as session:
        log = MoodLog(user_id=user_id, mood=mood, load_level=load_level)
        session.add(log)
        await session.commit()
        return log

async def get_recent_moods(user_id: int, limit: int = 5):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(MoodLog).where(MoodLog.user_id == user_id).order_by(MoodLog.timestamp.desc()).limit(limit)
        )
        return result.scalars().all()

async def delete_task(task_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            await session.delete(task)
            await session.commit()
            return True
        return False

async def update_task_desc(task_id: int, new_desc: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            task.description = new_desc
            await session.commit()
            return True
        return False

async def update_task_subject(task_id: int, new_subject: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            task.subject = new_subject
            await session.commit()
            return True
        return False

async def update_task_deadline(task_id: int, new_deadline: datetime.datetime):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            task.deadline = new_deadline
            await session.commit()
            return True
        return False
