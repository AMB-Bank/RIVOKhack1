from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    full_name = Column(String)
    class_name = Column(String) # e.g., '6А', '7В'
    last_reminded_at = Column(DateTime)
    xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    
    tasks = relationship("Task", back_populates="user")
    schedules = relationship("Schedule", back_populates="user")
    mood_logs = relationship("MoodLog", back_populates="user")

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    day_of_week = Column(Integer)  # 0-6
    lesson_name = Column(String, nullable=False)
    start_time = Column(String)  # HH:MM
    
    user = relationship("User", back_populates="schedules")

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    subject = Column(String, nullable=False)
    description = Column(Text)
    deadline = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    difficulty = Column(String)  # 'easy', 'normal', 'hard'
    steps = Column(Text)  # JSON-like string for sub-tasks
    class_name = Column(String)
    
    user = relationship("User", back_populates="tasks")

class MoodLog(Base):
    __tablename__ = 'mood_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    mood = Column(String)  # 'happy', 'neutral', 'stressed'
    load_level = Column(Integer) # 1-10
    
    user = relationship("User", back_populates="mood_logs")

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    earned_at = Column(DateTime, default=datetime.datetime.utcnow)

# Database Setup
DATABASE_URL = "sqlite+aiosqlite:///./diary.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
