import json
import os
import numpy as np
from typing import List, Dict, Any, Union, Optional, Tuple

class VectorTable:
    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.vectors = []
        self.metadata = []
        
    def insert(self, vector: List[float], metadata: Dict[str, Any] = None):
        if len(vector) != self.dimension:
            raise ValueError(f"Vector dimension mismatch: expected {self.dimension}, got {len(vector)}")
        
        self.vectors.append(vector)
        self.metadata.append(metadata or {})
        
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[int, float, Dict]]:
        if not self.vectors:
            return []
            
        if len(query_vector) != self.dimension:
            raise ValueError(f"Query vector dimension mismatch: expected {self.dimension}, got {len(query_vector)}")
            
        query_np = np.array(query_vector)
        vectors_np = np.array(self.vectors)
        
        query_norm = query_np / np.linalg.norm(query_np)
        vectors_norm = vectors_np / np.linalg.norm(vectors_np, axis=1)[:, np.newaxis]
        
        similarities = np.dot(vectors_norm, query_norm)
        
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            index = int(idx)
            similarity = float(similarities[idx])
            results.append((index, similarity, self.metadata[idx]))
            
        return results

    def to_dict(self):
        dimension = int(self.dimension) if hasattr(self.dimension, 'item') else self.dimension
    
        vectors = []
        for vec in self.vectors:
            if hasattr(vec, 'tolist'):
                vectors.append([float(v) for v in vec.tolist()])
            else:
                vectors.append([float(v) for v in vec])
    
        return {
            "dimension": dimension,
            "vectors": vectors,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data):
        vector_table = cls(dimension=data["dimension"])
        vector_table.vectors = data["vectors"]
        vector_table.metadata = data["metadata"]
        return vector_table


class RelationalTable:
    def __init__(self, columns: List[str]):
        self.columns = columns
        self.rows = []
        self.column_types = {col: "text" for col in columns}
        
    def insert(self, row_data: Union[List, Dict]):
        if isinstance(row_data, dict):
            row = [row_data.get(col, None) for col in self.columns]
        else:
            if len(row_data) != len(self.columns):
                raise ValueError(f"Row has {len(row_data)} values but table has {len(self.columns)} columns")
            row = row_data
            
        self.rows.append(row)
        
    def select(self, conditions=None, columns=None):
        result_rows = self.rows
        
        if conditions:
            result_rows = [row for row in result_rows if conditions(row)]
            
        if columns:
            col_indices = [self.columns.index(col) for col in columns if col in self.columns]
            result_rows = [[row[i] for i in col_indices] for row in result_rows]
            result_columns = columns
        else:
            result_columns = self.columns
            
        return result_columns, result_rows
        
    def update(self, updates, conditions=None):
        update_indices = {self.columns.index(col): val for col, val in updates.items() if col in self.columns}
        
        for i, row in enumerate(self.rows):
            if conditions is None or conditions(row):
                for col_idx, new_val in update_indices.items():
                    row[col_idx] = new_val
                    
    def delete(self, conditions):
        self.rows = [row for row in self.rows if not conditions(row)]
        
    def to_dict(self):
        return {
            "columns": self.columns,
            "column_types": self.column_types,
            "rows": self.rows
        }
    
    @classmethod
    def from_dict(cls, data):
        table = cls(columns=data["columns"])
        table.rows = data["rows"]
        if "column_types" in data:
            table.column_types = data["column_types"]
        return table


class Database:
    def __init__(self, name: str, db_path: str):
        self.name = name
        self.db_path = os.path.join(db_path, name)
        self.relational_tables = {}
        self.vector_tables = {}
        
        os.makedirs(self.db_path, exist_ok=True)
        
    def create_table(self, name: str, columns: List[str]):
        self.relational_tables[name] = RelationalTable(columns)
        self._save_table(name, is_vector=False)
        
    def create_vector_table(self, name: str, dimension: int = 128):
        self.vector_tables[name] = VectorTable(dimension)
        self._save_table(name, is_vector=True)
        
    def drop_table(self, name: str, is_vector: bool = False):
        table_path = self._get_table_path(name, is_vector)
        
        if is_vector:
            if name in self.vector_tables:
                del self.vector_tables[name]
        else:
            if name in self.relational_tables:
                del self.relational_tables[name]
                
        if os.path.exists(table_path):
            os.remove(table_path)
            
    def _get_table_path(self, name: str, is_vector: bool = False):
        suffix = "vec" if is_vector else "rel"
        return os.path.join(self.db_path, f"{name}.{suffix}.db")
        
    def _save_table(self, name: str, is_vector: bool = False):
        table_path = self._get_table_path(name, is_vector)
        
        if is_vector:
            table_data = self.vector_tables[name].to_dict()
        else:
            table_data = self.relational_tables[name].to_dict()
            
        with open(table_path, "w") as f:
            json.dump(table_data, f)
            
    def _load_table(self, name: str, is_vector: bool = False) -> bool:
        table_path = self._get_table_path(name, is_vector)
        
        if not os.path.exists(table_path):
            return False
            
        try:
            with open(table_path, "r") as f:
                table_data = json.load(f)
                
            if is_vector:
                self.vector_tables[name] = VectorTable.from_dict(table_data)
            else:
                self.relational_tables[name] = RelationalTable.from_dict(table_data)
                
            return True
        except Exception as e:
            print(f"Error loading table {name}: {e}")
            return False


class mascotDB:
    def __init__(self, root_path: str = "./db_files"):
        self.root_path = root_path
        self.databases = {}
        self.current_db = None
        
        os.makedirs(root_path, exist_ok=True)
        
        self._discover_databases()
        
    def _discover_databases(self):
        for item in os.listdir(self.root_path):
            full_path = os.path.join(self.root_path, item)
            if os.path.isdir(full_path):
                self.databases[item] = Database(item, self.root_path)
                
    def create_database(self, name: str):
        if name in self.databases:
            raise ValueError(f"Database '{name}' already exists")
            
        self.databases[name] = Database(name, self.root_path)
        self.current_db = self.databases[name]
        return self.current_db
        
    def drop_database(self, name: str):
        if name not in self.databases:
            raise ValueError(f"Database '{name}' does not exist")
            
        db_path = os.path.join(self.root_path, name)
        
        for file in os.listdir(db_path):
            os.remove(os.path.join(db_path, file))
            
        os.rmdir(db_path)
        
        del self.databases[name]
        
        if self.current_db and self.current_db.name == name:
            self.current_db = None
            
    def use_database(self, name: str) -> Optional[Database]:
        if name not in self.databases:
            return None
            
        self.current_db = self.databases[name]
        return self.current_db
        
    def list_databases(self) -> List[str]:
        return list(self.databases.keys())
        
    def list_tables(self, db_name: Optional[str] = None) -> Dict[str, List[str]]:
        if db_name is None:
            if self.current_db is None:
                return {"relational": [], "vector": []}
            db = self.current_db
        elif db_name in self.databases:
            db = self.databases[db_name]
        else:
            return {"relational": [], "vector": []}
            
        rel_tables = []
        vec_tables = []
        
        for file in os.listdir(db.db_path):
            if file.endswith(".rel.db"):
                table_name = file[:-7]
                rel_tables.append(table_name)
                
            elif file.endswith(".vec.db"):
                table_name = file[:-7]
                vec_tables.append(table_name)
                
        return {
            "relational": rel_tables,
            "vector": vec_tables
        }
    
    def _ensure_current_db(self):
        if self.current_db is None:
            raise ValueError("No database selected. Use 'USE DATABASE name' first.")
    
    def create_table(self, name: str, columns: List[str]):
        self._ensure_current_db()
        return self.current_db.create_table(name, columns)
        
    def create_vector_table(self, name: str, dimension: int = 128):
        self._ensure_current_db()
        return self.current_db.create_vector_table(name, dimension)
        
    def drop_table(self, name: str, is_vector: bool = False):
        self._ensure_current_db()
        return self.current_db.drop_table(name, is_vector)
        
    def insert(self, table_name: str, data, is_vector: bool = False, metadata: Dict = None):
        self._ensure_current_db()
        
        if is_vector:
            if table_name not in self.current_db.vector_tables:
                self.current_db._load_table(table_name, is_vector=True)
                
            if table_name in self.current_db.vector_tables:
                self.current_db.vector_tables[table_name].insert(data, metadata)
                self.current_db._save_table(table_name, is_vector=True)
            else:
                raise ValueError(f"Vector table '{table_name}' not found")
        else:
            if table_name not in self.current_db.relational_tables:
                self.current_db._load_table(table_name, is_vector=False)
                
            if table_name in self.current_db.relational_tables:
                self.current_db.relational_tables[table_name].insert(data)
                self.current_db._save_table(table_name, is_vector=False)
            else:
                raise ValueError(f"Relational table '{table_name}' not found")
                
    def select(self, table_name: str, conditions=None, columns=None):
        self._ensure_current_db()
        
        if table_name not in self.current_db.relational_tables:
            self.current_db._load_table(table_name, is_vector=False)
            
        if table_name in self.current_db.relational_tables:
            return self.current_db.relational_tables[table_name].select(conditions, columns)
        else:
            raise ValueError(f"Table '{table_name}' not found")
            
    def vector_search(self, table_name: str, query_vector: List[float], top_k: int = 5):
        self._ensure_current_db()
        
        if table_name not in self.current_db.vector_tables:
            self.current_db._load_table(table_name, is_vector=True)
            
        if table_name in self.current_db.vector_tables:
            return self.current_db.vector_tables[table_name].search(query_vector, top_k)
        else:
            raise ValueError(f"Vector table '{table_name}' not found")