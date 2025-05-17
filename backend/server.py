from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from engine import mascotDB
import re
import json
from typing import List, Dict, Any, Optional

app = FastAPI(title="mascotDB API", description="A lightweight RDBMS with vector capabilities")
db = mascotDB()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SQLParser:
    @staticmethod
    def parse_create_database(command: str) -> str:
        match = re.match(r"CREATE DATABASE\s+(\w+)", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid CREATE DATABASE syntax. Expected: CREATE DATABASE database_name")
        return match.group(1)
    
    @staticmethod
    def parse_use_database(command: str) -> str:
        match = re.match(r"USE\s+DATABASE\s+(\w+)", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid USE DATABASE syntax. Expected: USE DATABASE database_name")
        return match.group(1)
    
    @staticmethod
    def parse_drop_database(command: str) -> str:
        match = re.match(r"DROP DATABASE\s+(\w+)", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid DROP DATABASE syntax. Expected: DROP DATABASE database_name")
        return match.group(1)
    
    @staticmethod
    def parse_create_table(command: str) -> tuple:
        match = re.match(r"CREATE TABLE\s+(\w+)\s*\((.*)\)", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid CREATE TABLE syntax. Expected: CREATE TABLE table_name (col1, col2, ...)")
        
        table_name = match.group(1)
        columns_str = match.group(2)
        
        columns = [col.strip() for col in columns_str.split(",")]
        
        return table_name, columns
    
    @staticmethod
    def parse_create_vector_table(command: str) -> tuple:
        match = re.match(r"CREATE VECTOR TABLE\s+(\w+)\s+DIMENSION\s+(\d+)", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid CREATE VECTOR TABLE syntax. Expected: CREATE VECTOR TABLE table_name DIMENSION 128")
        
        table_name = match.group(1)
        dimension = int(match.group(2))
        
        return table_name, dimension
    
    @staticmethod
    def parse_drop_table(command: str) -> tuple:
        match = re.match(r"DROP\s+(VECTOR)?\s*TABLE\s+(\w+)", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid DROP TABLE syntax. Expected: DROP [VECTOR] TABLE table_name")
        
        is_vector = bool(match.group(1))
        table_name = match.group(2)
        
        return table_name, is_vector
    
    @staticmethod
    def parse_insert(command: str) -> tuple:
        match = re.match(r"INSERT INTO\s+(\w+)\s+VALUES\s+(\(.*\))", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid INSERT INTO syntax. Expected: INSERT INTO table_name VALUES (val1, val2, ...)")
        
        table_name = match.group(1)
        values_str = match.group(2)
        
        try:
            values = eval(values_str)
            return table_name, values, False
        except Exception as e:
            raise ValueError(f"Error parsing values: {str(e)}")
    
    @staticmethod
    def parse_insert_vector(command: str) -> tuple:
        pattern = r"INSERT VECTOR INTO\s+(\w+)\s+VALUES\s+(\[.*\])\s*(WITH METADATA\s+(\{.*\}))?"
        match = re.match(pattern, command, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ValueError("Invalid INSERT VECTOR syntax. Expected: INSERT VECTOR INTO table_name VALUES [v1, v2, ...] [WITH METADATA {...}]")
        
        table_name = match.group(1)
        vector_str = match.group(2)
        metadata_str = match.group(4)
        
        try:
            vector = json.loads(vector_str)
            metadata = json.loads(metadata_str) if metadata_str else {}
            
            return table_name, vector, True, metadata
        except Exception as e:
            raise ValueError(f"Error parsing vector data: {str(e)}")
    
    @staticmethod
    def parse_select(command: str) -> tuple:
        match = re.match(r"SELECT\s+\*\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?", command, re.IGNORECASE)
        if not match:
            raise ValueError("Invalid SELECT syntax. Expected: SELECT * FROM table_name [WHERE condition]")
        
        table_name = match.group(1)
        condition_str = match.group(2)
        
        return table_name, None
    
    @staticmethod
    def parse_vector_search(command: str) -> tuple:
        pattern = r"VECTOR SEARCH\s+(\w+)\s+QUERY\s+(\[.*\])\s+TOP\s+(\d+)"
        match = re.match(pattern, command, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid VECTOR SEARCH syntax. Expected: VECTOR SEARCH table_name QUERY [v1, v2, ...] TOP 5")
        
        table_name = match.group(1)
        vector_str = match.group(2)
        top_k = int(match.group(3))
        
        try:
            query_vector = json.loads(vector_str)
            return table_name, query_vector, top_k
        except Exception as e:
            raise ValueError(f"Error parsing vector query: {str(e)}")


@app.post("/query")
async def handle_query(request: Request):
    body = await request.json()
    command = body.get("command", "").strip()
    
    try:
        if command.upper().startswith("CREATE DATABASE"):
            db_name = SQLParser.parse_create_database(command)
            db.create_database(db_name)
            return {"status": "success", "message": f"Database '{db_name}' created"}
            
        elif command.upper().startswith("USE DATABASE"):
            db_name = SQLParser.parse_use_database(command)
            database = db.use_database(db_name)
            if database:
                return {"status": "success", "message": f"Using database '{db_name}'"}
            else:
                return {"status": "error", "message": f"Database '{db_name}' not found"}
                
        elif command.upper().startswith("DROP DATABASE"):
            db_name = SQLParser.parse_drop_database(command)
            db.drop_database(db_name)
            return {"status": "success", "message": f"Database '{db_name}' dropped"}
            
        elif command.upper() == "SHOW DATABASES":
            databases = db.list_databases()
            return {"status": "success", "databases": databases}
            
        elif command.upper() == "SHOW TABLES":
            tables = db.list_tables()
            return {"status": "success", "tables": tables}
        
        elif command.upper().startswith("CREATE TABLE"):
            table_name, columns = SQLParser.parse_create_table(command)
            db.create_table(table_name, columns)
            return {"status": "success", "message": f"Table '{table_name}' created", "columns": columns}
            
        elif command.upper().startswith("CREATE VECTOR TABLE"):
            table_name, dimension = SQLParser.parse_create_vector_table(command)
            db.create_vector_table(table_name, dimension)
            return {"status": "success", "message": f"Vector table '{table_name}' created with dimension {dimension}"}
            
        elif command.upper().startswith("DROP TABLE") or command.upper().startswith("DROP VECTOR TABLE"):
            table_name, is_vector = SQLParser.parse_drop_table(command)
            db.drop_table(table_name, is_vector)
            table_type = "vector" if is_vector else "relational"
            return {"status": "success", "message": f"{table_type.capitalize()} table '{table_name}' dropped"}
        
        elif command.upper().startswith("INSERT INTO"):
            table_name, values, _ = SQLParser.parse_insert(command)
            db.insert(table_name, values)
            return {"status": "success", "message": f"Row inserted into '{table_name}'", "values": values}
            
        elif command.upper().startswith("INSERT VECTOR"):
            table_name, vector, is_vector, metadata = SQLParser.parse_insert_vector(command)
            db.insert(table_name, vector, is_vector, metadata)
            return {"status": "success", "message": f"Vector inserted into '{table_name}'"}
            
        elif command.upper().startswith("SELECT"):
            table_name, conditions = SQLParser.parse_select(command)
            columns, rows = db.select(table_name, conditions)
            return {"status": "success", "columns": columns, "rows": rows}
            
        elif command.upper().startswith("VECTOR SEARCH"):
            table_name, query_vector, top_k = SQLParser.parse_vector_search(command)
            results = db.vector_search(table_name, query_vector, top_k)
            return {
                "status": "success", 
                "results": [
                    {"index": idx, "similarity": sim, "metadata": meta} 
                    for idx, sim, meta in results
                ]
            }
            
        else:
            return {"status": "error", "message": f"Unsupported command: {command}"}
            
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}


@app.get("/")
async def root():
    return {
        "name": "mascotDB API",
        "version": "1.0.0",
        "description": "A lightweight RDBMS with vector database capabilities",
        "endpoints": {
            "/query": "Execute database commands",
            "/": "API information"
        },
        "supported_commands": [
            "CREATE DATABASE db_name",
            "USE DATABASE db_name",
            "DROP DATABASE db_name",
            "SHOW DATABASES",
            "SHOW TABLES",
            "CREATE TABLE table_name (col1, col2, ...)",
            "CREATE VECTOR TABLE table_name DIMENSION 128",
            "DROP TABLE table_name",
            "DROP VECTOR TABLE table_name",
            "INSERT INTO table_name VALUES (val1, val2, ...)",
            "INSERT VECTOR INTO table_name VALUES [v1, v2, ...] WITH METADATA {...}",
            "SELECT * FROM table_name",
            "VECTOR SEARCH table_name QUERY [v1, v2, ...] TOP 5"
        ]
    }