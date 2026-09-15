import sqlite3

DB_PATH = "chinook.db"
MAX_ROWS = 50

# Getting the schema of the database
def get_schema() -> str:
    # Opening a connection to the SQLite database in read-only mode
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()

    # Getting the list of tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    
    # creating a string that contains the schema of each table in the database
    schema = ""
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        schema += f"Table: {table_name}\n"
        schema += f"Columns: {', '.join(column_names)}\n\n"
    
    # Closing the connection to the SQLite database
    conn.close()
    return schema

# Running a SQL query and returning the results
def run_query(sql_query: str) -> dict:
    if not is_safe_query(sql_query):
        return {"success": False, "error": "Only SELECT statements are allowed."}

    # Opening a connection to the SQLite database in read-only mode
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()

    try:
        # Running the SQL query
        cursor.execute(sql_query)
        # Fetching the first MAX_ROWS results of the query
        results = cursor.fetchmany(MAX_ROWS)

        # Getting the column names of the results
        column_names = [col[0] for col in cursor.description] if cursor.description else []
        # Returning a dictionary with the results and the column names
        return {"success": True, "columns": column_names, "results": results}

    except sqlite3.Error as e:
        # Returning a dictionary with the error message
        return {"success": False, "error": str(e)}
        pass

    finally:
        conn.close()
        pass

def is_safe_query(query: str) -> bool:
    # Checking if the query is a SELECT statement using sqlglot
    try:
        import sqlglot
        from sqlglot import exp
        parsed_query = sqlglot.parse_one(query, read="sqlite")
        return isinstance(parsed_query, exp.Select)
    except Exception as e:
        return False
    pass