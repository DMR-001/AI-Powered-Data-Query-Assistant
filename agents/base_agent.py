import os
import requests
import re
import json
from agents.query_execution_agent import QueryExecutionAgent


class BaseAgent:
    def __init__(self, query_execution_agent: QueryExecutionAgent):
        """
        Initialize the BaseAgent with Groq API configuration and context management.
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API Key is not set.")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.conversation_context = {}  
        self.schema_info = {}  
        self.feedback_data = []  
        self.query_execution_agent = query_execution_agent  

    def process_user_query(self, query: str, conversation_id: str) -> str:
        """
        Converts a natural language query into SQL using the Groq API with context and schema support.
        """
        try:
            # Automatically fetch schema from the connected database
            schema = self.query_execution_agent.get_schema_description()
            print(f"✅ Fetched Schema for LLM:\n{schema}")

            # Initialize conversation context if not already present
            if conversation_id not in self.conversation_context:
                self.conversation_context[conversation_id] = []

            # Store the current query into the conversation history
            self.conversation_context[conversation_id].append(query)

            # promt for LLM
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a SQL query generator. Return only the SQL query as output. "
                        "Ensure all columns are fully qualified and strictly use the schema provided:\n"
                        f"{schema}\n"
                    )
                },
                {"role": "user", "content": query}
            ]

            # Prepare API request payload
            payload = {
                "model": "llama-3.3-70b-specdec",
                "messages": messages,
                "max_tokens": 3000,
                "temperature": 0.0,
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            # Send request to Groq API
            response = requests.post(self.api_url, json=payload, headers=headers)

            # Debugging the schema being sent
            print(f"Groq API Response: {response.status_code} - {response.text}")

            # Check for errors in API response
            if response.status_code != 200:
                raise ValueError(f"Groq API Error: {response.status_code} - {response.text}")

            # Extract the SQL query from API response
            full_response = response.json()["choices"][0]["message"]["content"].strip()

            # Clean SQL output by removing markdown artifacts
            sql_cleaned = re.sub(r"```sql|```", "", full_response).strip()

            # Ensure SQL has a SELECT and FROM clause for validation
            sql_match = re.search(r"(SELECT\s+.*?FROM\s+\w+.*?;)", sql_cleaned, re.DOTALL)

            # If no valid SQL detected, raise error
            if not sql_cleaned or not sql_match:
                raise ValueError("Groq API returned an invalid response. No complete SQL detected.")

            # Use regex match or fallback to cleaned SQL
            sql = sql_match.group(1).strip() if sql_match else sql_cleaned
            print(f"✅ Generated SQL: {sql}")

            # Verify SQL has proper table references
            if not re.search(r"FROM\s+\w+", sql, re.IGNORECASE):
                raise ValueError("Generated SQL is incomplete. Missing table reference after FROM clause.")

            return sql

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in process_user_query: {error_details}")
            raise ValueError(f"Error processing query: {str(e)}")
        
         

    def validate_sql(self, sql: str) -> bool:
        """Basic SQL validation ensuring it contains SELECT or INSERT statements."""
        return bool(re.search(r"(SELECT|INSERT)\s+", sql, re.IGNORECASE))

    def load_schema(self, schema_info: str):
        """
        Load schema information for improved query generation.
        """
        try:
            self.schema_info = json.loads(schema_info)
        except json.JSONDecodeError:
            raise ValueError("Invalid schema format. Must be a valid JSON string.")

    def get_schema_info(self):
        """Retrieve the loaded schema information."""
        return self.schema_info

    def update_context(self, conversation_id: str, query: str):
        """Update conversation context with a new query."""
        if conversation_id not in self.conversation_context:
            self.conversation_context[conversation_id] = []
        self.conversation_context[conversation_id].append(query)

    def get_context(self, conversation_id: str):
        """Retrieve conversation context."""
        return self.conversation_context.get(conversation_id, [])

    def clear_context(self, conversation_id: str):
        """Clear context for a specific conversation."""
        if conversation_id in self.conversation_context:
            del self.conversation_context[conversation_id]

    def collect_feedback(self, conversation_id: str, query: str, feedback: str):
        """Collect feedback for query refinement."""
        feedback_entry = {
            "conversation_id": conversation_id,
            "query": query,
            "feedback": feedback
        }
        self.feedback_data.append(feedback_entry)

        # Optionally save feedback for long-term analysis
        with open("feedback_data.json", "a") as f:
            json.dump(feedback_entry, f)
            f.write("\n")

        print("✅ Feedback recorded successfully.")

    def get_feedback(self):
        """Retrieve all collected feedback."""
        return self.feedback_data
