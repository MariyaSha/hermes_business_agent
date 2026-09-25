import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path("/opt/data/state.db")


def get_today_range():
    now = datetime.now().astimezone()

    start = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    end = now.replace(
        hour=23,
        minute=59,
        second=59,
        microsecond=999999,
    )

    return start.timestamp(), end.timestamp(), start.date()


def main():
    start_ts, end_ts, report_date = get_today_range()

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    sessions = connection.execute(
        """
        SELECT
            id,
            user_id,
            chat_id,
            display_name,
            title,
            started_at
        FROM sessions
        WHERE source = 'telegram'
          AND started_at BETWEEN ? AND ?
        ORDER BY started_at
        """,
        (start_ts, end_ts),
    ).fetchall()

    conversations = []
    customer_messages = 0
    assistant_messages = 0
    unique_customers = set()

    for session in sessions:
        if session["user_id"]:
            unique_customers.add(session["user_id"])

        messages = connection.execute(
            """
            SELECT
                role,
                content,
                timestamp
            FROM messages
            WHERE session_id = ?
              AND active = 1
              AND role IN ('user', 'assistant')
              AND content IS NOT NULL
            ORDER BY timestamp
            """,
            (session["id"],),
        ).fetchall()

        conversation = []

        for message in messages:
            content = message["content"].strip()

            if not content:
                continue

            if message["role"] == "user":
                customer_messages += 1
                speaker = "CUSTOMER"
            else:
                assistant_messages += 1
                speaker = "EMBER"

            conversation.append(f"{speaker}: {content}")

        if conversation:
            conversations.append(
                "\n".join(conversation)
            )

    connection.close()

    print(f"DRAGONDASH SUPPORT DATA — {report_date}")
    print()
    print(f"Customer conversations: {len(conversations)}")
    print(f"Unique customers: {len(unique_customers)}")
    print(f"Customer messages: {customer_messages}")
    print(f"Ember responses: {assistant_messages}")
    print()

    if not conversations:
        print("No customer conversations were recorded today.")
        return

    print("CONVERSATIONS")
    print("=============")

    for number, conversation in enumerate(conversations, 1):
        print()
        print(f"--- Conversation {number} ---")
        print(conversation)


if __name__ == "__main__":
    main()