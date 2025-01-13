from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from agents.base_agent import BaseAgent
from agents.query_execution_agent import QueryExecutionAgent
from agents.data_processing_agent import DataProcessingAgent
from agents.graph_generation_agent import GraphGeneratingAgent
from dotenv import load_dotenv
import os
import pandas as pd
import json
import traceback

# Load environment variables
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY is not set in the environment or .env file.")

# Initialize FastAPI app and other agents
app = FastAPI()
data_processing_agent = DataProcessingAgent()
graph_generation_agent = GraphGeneratingAgent()
conversation_context = {}  
query_history = []         
feedback_data = []  

# Singleton for Persistent Query Execution Agent
query_execution_agent_instance = None
# BaseAgent will be initialized after the database connection is established.
base_agent = None  

def get_query_execution_agent():
    """Dependency Injection for Persistent Query Execution Agent"""
    global query_execution_agent_instance
    if query_execution_agent_instance is None:
        raise HTTPException(status_code=500, detail="Database connection not initialized. Please validate.")
    return query_execution_agent_instance

# Pydantic Models for Request Validation
class QueryRequest(BaseModel):
    query: str
    conversation_id: str
    show_analysis: bool = False

class GraphRequest(BaseModel):
    data: list
    requested_graph_type: str = None

class FeedbackRequest(BaseModel):
    query: str
    feedback: str
    conversation_id: str

class DBConfigRequest(BaseModel):
    db_type: str
    dbname: str
    user: str
    password: str
    host: str
    port: int
    timeout: int = 60

class ContextRequest(BaseModel):
    conversation_id: str
    context: dict

# Root Endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Enhanced Multi-Turn Data Query Assistant!"}

# Database Connection Validation
@app.post("/api/connection")
def validate_connection(config: DBConfigRequest):
    global query_execution_agent_instance, base_agent
    try:
        db_config = {
            "dbname": config.dbname,
            "user": config.user,
            "password": config.password,
            "host": config.host,
            "port": config.port
        }
        
        # Initialize the database connection and BaseAgent only after successful connection
        query_execution_agent_instance = QueryExecutionAgent(
            db_config=db_config, 
            timeout=config.timeout, 
            db_type=config.db_type.lower()
        )
        query_execution_agent_instance.validate_connection()
        
        # Initialize the BaseAgent after the QueryExecutionAgent is ready
        base_agent = BaseAgent(query_execution_agent_instance)
        
        return {"status": "success", "message": f"{config.db_type.capitalize()} connection is valid."}
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error in /api/connection: {error_details}")
        raise HTTPException(status_code=500, detail=f"{config.db_type.capitalize()} connection failed: {str(e)}")

# Process Query with Optional Query Optimization Insights
@app.post("/api/query")
def process_query(request: QueryRequest, query_execution_agent=Depends(get_query_execution_agent)):
    global conversation_context, query_history
    try:
        if not query_execution_agent.validate_connection():
            raise HTTPException(status_code=500, detail="Database connection expired. Please validate again.")

        # Generate SQL using LLM with the schema automatically included
        sql = base_agent.process_user_query(request.query, request.conversation_id)
        if not base_agent.validate_sql(sql):
            raise HTTPException(status_code=400, detail="Invalid SQL generated.")

        # Execute the query with or without optimization insights
        if request.show_analysis:
            query_result = query_execution_agent.execute_query_with_analysis(sql)
            results = data_processing_agent.format_results(query_result["results"])
            # Flatten the results for better readability
            performance_analysis = [str(item[0]) for item in query_result["performance_analysis"]]
        else:
            data = query_execution_agent.execute_query(sql)
            results = data_processing_agent.format_results(data)
            performance_analysis = None

        # Update conversation context and query history
        if request.conversation_id not in conversation_context:
            conversation_context[request.conversation_id] = {"queries": [], "results": []}
        
        # ✅ Store the query and results
        sql = base_agent.process_user_query(request.query, request.conversation_id)
        data = query_execution_agent.execute_query(sql)
        results = data_processing_agent.format_results(data)
        
        conversation_context[request.conversation_id]["queries"].append(request.query)
        conversation_context[request.conversation_id]["results"].append(results)
        query_history.append({"conversation_id": request.conversation_id, "query": request.query, "results": results})

        return {"sql": sql, "results": results, "performance_analysis": performance_analysis}

    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error during query execution: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")

# Generate Graph with Advanced Visualizations
@app.post("/api/generate_graph")
def generate_graph(request: GraphRequest):
    try:
        result = graph_generation_agent.generate_graph(request.data, request.requested_graph_type)
        return result
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error generating graph: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error generating graph: {str(e)}")

# Collect User Feedback for Query Refinement
@app.post("/api/feedback")
def collect_feedback(request: FeedbackRequest):
    try:
        feedback_entry = {
            "conversation_id": request.conversation_id,
            "query": request.query,
            "feedback": request.feedback
        }
        feedback_data.append(feedback_entry)

        # Persist feedback for long-term storage
        with open("feedback_data.json", "a") as f:
            json.dump(feedback_entry, f)
            f.write("\n")

        return {"status": "success", "message": "Feedback recorded successfully."}
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error storing feedback: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error storing feedback: {str(e)}")

# Fetch All Query Histories
@app.get("/api/query/history")
def get_query_history():
    return {"query_history": query_history}

# Fetch Context for a Specific Conversation
@app.get("/api/context/{conversation_id}")
def get_conversation_context(conversation_id: str):
    if conversation_id in conversation_context:
        return {"conversation_id": conversation_id, "context": conversation_context[conversation_id]}
    else:
        raise HTTPException(status_code=404, detail="Conversation context not found.")

# Clear Context for a Specific Conversation
@app.delete("/api/context/{conversation_id}")
def clear_conversation_context(conversation_id: str):
    if conversation_id in conversation_context:
        del conversation_context[conversation_id]
        return {"status": "success", "message": "Context cleared successfully."}
    else:
        raise HTTPException(status_code=404, detail="Conversation context not found.")
