import asyncio
import asyncpg
from app.core.config import settings

async def create_database():
    # Connect to the default 'postgres' database
    conn_url = "postgresql://postgres@localhost:5432/postgres"
    print(f"Connecting to database server at: {conn_url}")
    
    try:
        conn = await asyncpg.connect(conn_url)
        await conn.execute("CREATE DATABASE knowledge_assistant")
        print("Success: Database 'knowledge_assistant' has been created successfully!")
    except asyncpg.exceptions.DuplicateDatabaseError:
        print("Notice: Database 'knowledge_assistant' already exists.")
    except Exception as e:
        print(f"Error creating database: {str(e)}")
        print("\nPlease make sure PostgreSQL is running locally and your user has rights.")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(create_database())
