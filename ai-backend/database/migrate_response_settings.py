import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [r[1] for r in cursor.fetchall()]

    new_columns = [
        ("response_show_translation", "INTEGER NOT NULL DEFAULT 1"),
        ("response_show_furigana", "INTEGER NOT NULL DEFAULT 1"),
        ("response_highlight_grammar", "INTEGER NOT NULL DEFAULT 1"),
        ("response_show_romaji", "INTEGER NOT NULL DEFAULT 1"),
        ("response_grammar_breakdown", "INTEGER NOT NULL DEFAULT 1"),
        ("response_audio_speech", "INTEGER NOT NULL DEFAULT 1"),
        ("response_bilingual_mode", "VARCHAR(20) NOT NULL DEFAULT 'interlinear'")
    ]

    for col_name, col_def in new_columns:
        if col_name not in existing_cols:
            print(f"Adding column '{col_name}' to 'users' table...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
        else:
            print(f"Column '{col_name}' already exists.")

    conn.commit()
    conn.close()
    print("Migration of response settings completed successfully!")

if __name__ == "__main__":
    migrate()

