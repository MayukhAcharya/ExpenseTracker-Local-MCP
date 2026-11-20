from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")


def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)


init_db()


@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    "Add a new expense to the database"
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
            (date, amount, category, subcategory, note),
        )
    return {"status": "ok", "id": cur.lastrowid}


@mcp.tool()
def list_expense(startDate, endDate):
    "Lists all the expenses in between start date and end date"
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (startDate, endDate),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


@mcp.tool()
def summarize_expense(category=None, startDate=None, endDate=None):
    "Summarizes the expenses according to category provided, if not provided list all the expenses"
    with sqlite3.connect(DB_PATH) as c:
        query = """
            SELECT category,
                   COUNT(*) AS count,
                   SUM(amount) AS total_amount,
                   AVG(amount) AS average_amount,
                   MIN(amount) AS min_amount,
                   MAX(amount) AS max_amount
            FROM expenses
            WHERE 1=1
        """
        params = []

        if startDate and endDate:
            query += " AND date BETWEEN ? AND ?"
            params.extend([startDate, endDate])
        elif startDate:
            query += " AND date >= ?"
            params.append(startDate)
        elif endDate:
            query += " AND date <= ?"
            params.append(endDate)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY total_amount DESC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

        # Round the floating point values for cleaner output
        for row in rows:
            row["total_amount"] = round(row["total_amount"] or 0, 2)
            row["average_amount"] = round(row["average_amount"] or 0, 2)

        return rows


if __name__ == "__main__":
    mcp.run()
