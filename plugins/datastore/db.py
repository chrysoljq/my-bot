import aiosqlite
from nonebot import get_driver, logger
from pathlib import Path
from typing import Optional, List, Any

# Define database path
DB_PATH = Path("data/datastore/mybot.db")

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.conn = None
        return cls._instance

    def __init__(self):
        # Prevent re-init logic if needed, but __new__ handles singleton structure
        pass
        
    async def init(self):
        """Initialize database connection."""
        if self.conn:
            return
            
        # Ensure directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Connecting to database at {DB_PATH}...")
        self.conn = await aiosqlite.connect(DB_PATH)
        self.conn.row_factory = aiosqlite.Row
        logger.info("Database connected.")
        
        await self._create_tables()

    async def _create_tables(self):
        """Create necessary tables if they don't exist."""
        # We can implement a registry system here, or just let plugins call execute_script
        # For simplicity and centrality, let plugins define their schema elsewhere or here.
        # But per plan, plugins will register/execute their own CREATE table on their startup.
        # However, to avoid circular dependencies or complex init order, 
        # let's provide a method for plugins to init schema.
        pass

    async def close(self):
        if self.conn:
            await self.conn.close()
            self.conn = None
            logger.info("Database connection closed.")

    async def execute(self, sql: str, parameters: tuple = None):
        """Execute a write operation (INSERT, UPDATE, DELETE)."""
        if not self.conn:
            raise RuntimeError("Database not initialized")
        async with self.conn.cursor() as cursor:
            await cursor.execute(sql, parameters or ())
            await self.conn.commit()
            return cursor.lastrowid

    async def fetchone(self, sql: str, parameters: tuple = None) -> Optional[aiosqlite.Row]:
        """Execute a read operation returning one row."""
        if not self.conn:
            raise RuntimeError("Database not initialized")
        async with self.conn.cursor() as cursor:
            await cursor.execute(sql, parameters or ())
            return await cursor.fetchone()

    async def fetchall(self, sql: str, parameters: tuple = None) -> List[aiosqlite.Row]:
        """Execute a read operation returning all rows."""
        if not self.conn:
            raise RuntimeError("Database not initialized")
        async with self.conn.cursor() as cursor:
            await cursor.execute(sql, parameters or ())
            return await cursor.fetchall()
    
    async def execute_script(self, sql_script: str):
        """Execute a raw SQL script (multiple statements)."""
        if not self.conn:
            raise RuntimeError("Database not initialized")
        await self.conn.executescript(sql_script)
        await self.conn.commit()

# Singleton Instance
db = DatabaseManager()

# Lifecycle Hooks
driver = get_driver()

@driver.on_startup
async def connect_db():
    await db.init()

@driver.on_shutdown
async def disconnect_db():
    await db.close()
