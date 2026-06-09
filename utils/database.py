import sqlite3
import os
import json
from datetime import datetime, date

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database")
DB_PATH = os.path.join(DB_DIR, "study_history.db")

def get_connection():
    """Returns a connection to the SQLite database, creating the directory if needed."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they do not exist."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Sessions table for study history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL, -- JSON formatted content
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. User analytics table (single row)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_analytics (
                id INTEGER PRIMARY KEY,
                streak_count INTEGER DEFAULT 0,
                last_active_date TEXT,
                total_time_spent INTEGER DEFAULT 0, -- in seconds
                total_quizzes_taken INTEGER DEFAULT 0,
                average_quiz_score REAL DEFAULT 0.0
            )
        """)
        
        # Ensure row 1 exists in analytics
        cursor.execute("SELECT id FROM user_analytics WHERE id = 1")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO user_analytics (id, streak_count, last_active_date, total_time_spent, total_quizzes_taken, average_quiz_score)
                VALUES (1, 0, NULL, 0, 0, 0.0)
            """)
            
        # 3. Progress logs for graphs/dashboard
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                topic TEXT NOT NULL,
                score REAL, -- null for non-quiz
                duration INTEGER DEFAULT 0, -- seconds
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()

# --- Sessions & History Helpers ---

def save_study_session(page: str, topic: str, content_dict: dict) -> int:
    """Saves a study session to the database history and logs the activity."""
    content_json = json.dumps(content_dict)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (page, topic, content) VALUES (?, ?, ?)",
            (page, topic, content_json)
        )
        session_id = cursor.lastrowid
        
        # Log to progress logs as well
        cursor.execute(
            "INSERT INTO progress_log (activity_type, topic, score) VALUES (?, ?, ?)",
            (page, topic, None)
        )
        conn.commit()
        return session_id

def get_study_sessions(page: str = None):
    """Retrieves list of previous sessions, filtered optionally by page."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if page:
            cursor.execute("SELECT id, page, topic, timestamp FROM sessions WHERE page = ? ORDER BY timestamp DESC", (page,))
        else:
            cursor.execute("SELECT id, page, topic, timestamp FROM sessions ORDER BY timestamp DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_session_by_id(session_id: int):
    """Retrieves full content of a specific study session."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            res = dict(row)
            res['content'] = json.loads(res['content'])
            return res
        return None

def delete_session(session_id: int):
    """Deletes a study session from history."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()

# --- Analytics & Streaks Helpers ---

def update_streak() -> dict:
    """
    Checks the last active date and updates the user's daily study streak.
    Returns the updated analytics row.
    """
    today_str = date.today().isoformat()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT streak_count, last_active_date FROM user_analytics WHERE id = 1")
        row = cursor.fetchone()
        
        streak = row['streak_count']
        last_date_str = row['last_active_date']
        
        if last_date_str is None:
            # First time using the app
            streak = 1
        elif last_date_str == today_str:
            # Already active today, streak stays the same
            pass
        else:
            last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
            delta = date.today() - last_date
            if delta.days == 1:
                # Active yesterday, increment streak
                streak += 1
            else:
                # Broke streak, reset to 1
                streak = 1
                
        cursor.execute(
            "UPDATE user_analytics SET streak_count = ?, last_active_date = ? WHERE id = 1",
            (streak, today_str)
        )
        conn.commit()
        
        return {
            "streak_count": streak,
            "last_active_date": today_str
        }

def log_study_time(seconds: int):
    """Adds elapsed seconds to total time spent."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE user_analytics SET total_time_spent = total_time_spent + ? WHERE id = 1", (seconds,))
        conn.commit()

def log_quiz_result(topic: str, score: float):
    """Logs quiz score, updates quiz metrics in analytics, and records in progress log."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Insert to progress logs
        cursor.execute(
            "INSERT INTO progress_log (activity_type, topic, score) VALUES (?, ?, ?)",
            ('quiz', topic, score)
        )
        
        # Recalculate average quiz score in user_analytics
        cursor.execute("SELECT total_quizzes_taken, average_quiz_score FROM user_analytics WHERE id = 1")
        row = cursor.fetchone()
        count = row['total_quizzes_taken'] + 1
        old_avg = row['average_quiz_score']
        
        new_avg = old_avg + (score - old_avg) / count
        
        cursor.execute(
            "UPDATE user_analytics SET total_quizzes_taken = ?, average_quiz_score = ? WHERE id = 1",
            (count, new_avg)
        )
        conn.commit()

def get_analytics() -> dict:
    """Fetches user analytics summary including streak, total time, quiz counts and averages."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_analytics WHERE id = 1")
        analytics = dict(cursor.fetchone())
        
        # Get count of total sessions from history
        cursor.execute("SELECT COUNT(*) as count FROM sessions")
        analytics['total_sessions'] = cursor.fetchone()['count']
        
        # Get count per page
        cursor.execute("SELECT page, COUNT(*) as count FROM sessions GROUP BY page")
        analytics['sessions_by_page'] = {row['page']: row['count'] for row in cursor.fetchall()}
        
        # Get recent progress log (last 10 entries)
        cursor.execute("SELECT activity_type, topic, score, timestamp FROM progress_log ORDER BY timestamp DESC LIMIT 10")
        analytics['recent_progress'] = [dict(row) for row in cursor.fetchall()]
        
        # Get history of activities per day for charting (last 7 active days)
        cursor.execute("""
            SELECT date(timestamp) as day, COUNT(*) as count 
            FROM progress_log 
            GROUP BY day 
            ORDER BY day DESC 
            LIMIT 7
        """)
        analytics['daily_activity'] = [dict(row) for row in cursor.fetchall()]
        
        return analytics
