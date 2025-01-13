import psycopg
import mysql.connector
import pandas as pd

class QueryExecutionAgent:
    def __init__(self, db_config: dict, timeout: int = 55, db_type: str = "postgresql"):
        """
        Initialize the database connection agent with support for PostgreSQL and MySQL.
        """
        self.db_config = db_config
        self.timeout = timeout
        self.db_type = db_type.lower()
        self.connection = None
        self.connect()

    def connect(self):
        """
        Establish a database connection for PostgreSQL and MySQL.
        """
        try:
            if self.db_type == "postgresql":
                self.connection = psycopg.connect(
                    dbname=self.db_config["dbname"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    connect_timeout=self.timeout
                )
            elif self.db_type == "mysql":
                self.connection = mysql.connector.connect(
                    host=self.db_config["host"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                    database=self.db_config["dbname"],
                    port=self.db_config["port"],
                    connection_timeout=self.timeout
                )
            print("✅ Database connection established successfully.")
        except Exception as e:
            raise ConnectionError(f"Failed to establish a database connection: {e}")

    def validate_connection(self) -> bool:
        """
        Validate the database connection and reconnect if necessary.
        """
        try:
            if self.db_type == "postgresql":
                if not self.connection or self.connection.closed:
                    print("⚠️ PostgreSQL connection closed. Reconnecting...")
                    self.connect()
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchall()

            elif self.db_type == "mysql":
                if not self.connection or not self.connection.is_connected():
                    print("⚠️ MySQL connection closed. Reconnecting...")
                    self.connect()
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
                cursor.close()
                
            return True
        except Exception as e:
            print(f"Error validating connection: {e}")
            return False

    def execute_query(self, sql: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a DataFrame.
        """
        try:
            if not self.validate_connection():
                raise ConnectionError("Database connection not validated.")
                
            if self.db_type == "postgresql":
                with self.connection.cursor() as cursor:
                    cursor.execute(sql)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    return pd.DataFrame(rows, columns=columns)
                    
            elif self.db_type == "mysql":
                cursor = self.connection.cursor()
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()
                return pd.DataFrame(rows, columns=columns)
                
        except Exception as e:
            print(f"Error executing query: {e}")
            raise ValueError(f"Error executing query: {e}")

    # Query Optimization Insights Using EXPLAIN ANALYZE
    def execute_query_with_analysis(self, sql: str) -> dict:
        """
        Execute a SQL query with performance analysis using EXPLAIN ANALYZE (PostgreSQL) and EXPLAIN (MySQL).
        """
        try:
            if not self.validate_connection():
                raise ConnectionError("Database connection not validated.")
                
            if self.db_type == "postgresql":
                with self.connection.cursor() as cursor:
                    # Run EXPLAIN ANALYZE for performance insights
                    cursor.execute(f"EXPLAIN ANALYZE {sql}")
                    performance_analysis = cursor.fetchall()
                    analysis_results = "\n".join([str(item[0]) for item in performance_analysis])

                    # Execute the actual query
                    cursor.execute(sql)
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    results = pd.DataFrame(rows, columns=columns)

            elif self.db_type == "mysql":
                cursor = self.connection.cursor()
                cursor.execute(f"EXPLAIN {sql}")
                performance_analysis = cursor.fetchall()
                analysis_results = "\n".join([" | ".join(map(str, row)) for row in performance_analysis])

                # Execute the actual query after analysis
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                results = pd.DataFrame(rows, columns=columns)
                cursor.close()

            else:
                raise ValueError("Database not supported for analysis.")
        
            # Return both results and performance insights
            return {"results": results, "performance_analysis": analysis_results}

        except Exception as e:
            print(f"Error during query execution with analysis: {e}")
            raise ValueError(f"Error executing query with analysis: {str(e)}")

    def close_connection(self):
        """
        Close the database connection.
        """
        try:
            if self.db_type == "postgresql" and self.connection and not self.connection.closed:
                self.connection.close()
                print("✅ PostgreSQL connection closed.")
            elif self.db_type == "mysql" and self.connection and self.connection.is_connected():
                self.connection.close()
                print("✅ MySQL connection closed.")
        except Exception as e:
            print(f"Error closing the database connection: {e}")

    # Schema Extraction
    def get_schema_description(self) -> str:
        """
        Automatically fetch the schema from the connected database.
        """
        try:
            if not self.validate_connection():
                raise ConnectionError("Database connection not validated.")

            if self.db_type == "postgresql":
                query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                """
            elif self.db_type == "mysql":
                query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                """
            else:
                raise ValueError("Unsupported database type for schema extraction.")

            # Execute the schema extraction query
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                schema_info = cursor.fetchall()

            # Format schema into a human-readable string for LLM context
            schema_text = ""
            current_table = None
            for table_name, column_name, data_type in schema_info:
                if table_name != current_table:
                    schema_text += f"\nTable: {table_name}\n"
                    current_table = table_name
                schema_text += f" - {column_name} ({data_type})\n"

            return schema_text

        except Exception as e:
            raise ValueError(f"Error fetching schema: {e}")
