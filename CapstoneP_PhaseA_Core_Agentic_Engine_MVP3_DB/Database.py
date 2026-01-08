"""
New Python file
"""

import pyodbc
from typing import Optional,List,Dict,Any

import os

def get_db_connection() -> pyodbc.Connection:
    try:
        conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=localhost\\SQLEXPRESS;'
                'DATABASE=chatbot_db;'
                'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        print(f"database connection failed: {e}")   
        raise e

def create_chat(chat_id: str, title: str) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            IF NOT EXISTS (SELECT 1 FROM chatbot_db.dbo.chats WHERE chat_id = ?)
            BEGIN
                INSERT INTO chatbot_db.dbo.chats (chat_id, title, created_at) VALUES (?, ?, GETDATE())
            END
            """, (chat_id, chat_id, title)
        )
        conn.commit()
        return True

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def save_message(chat_id: str, content: str, role: str):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chatbot_db.dbo.chat_messages (chat_id, content, role, created_at) VALUES (?, ?, ?, GETDATE())
            """,(chat_id, content, role)
        )
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def get_messages(chat_id: str) -> list[Dict[str, Any]]: #append dict to a list

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT role, content, created_at FROM chatbot_db.dbo.chat_messages 
            WHERE chat_id = ? 
            ORDER BY created_at ASC
            """,(chat_id,)
        )

        messages = [] #empty list to store messages
        for row in cursor.fetchall():
            message_dict = {
                    "role": row.role,
                    "content": row.content,
                    "created_at": row.created_at.isoformat() if row.created_at else None

            }
            messages.append(message_dict) #add dictionary to list

        return messages
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return []
    finally:
        if conn:
            conn.close()

def chat_exists(chat_id:str) -> bool:
    conn = None
    try:
        conn=get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM chatbot_db.dbo.chats WHERE chat_id = ?
            """,(chat_id,)
        )
        return cursor.fetchone() is not None
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_all_chats_db() -> List[Dict[str, Any]]:
    """
    Get all chats with titles.
    
    Returns:
        List of chat dictionaries
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chat_id, title, created_at
            FROM chats
            ORDER BY created_at DESC
        """)
        
        chats = []
        for row in cursor.fetchall():
            chats.append({
                "chat_id": row.chat_id,
                "title": row.title,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        return chats
    except Exception as e:
        print(f"❌ Error getting chats: {e}")
        return []
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":

    conn = get_db_connection()
    """
    try:
        #create_chat("1", "test")
        #save_message("1", "Hello, how are you?", "user")
        #save_message("1", "I'm fine, thank you!", "assistant")
        #messages = get_messages("1")
        #print(messages)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
    """