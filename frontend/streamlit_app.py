import json
import streamlit as st
import requests
import pandas as pd
import plotly.io as pio
import uuid
from io import BytesIO

# Page Configuration
st.set_page_config(
    page_title="Data Query Assistant",
    page_icon="💬",
    layout="wide"
)

# Custom CSS for enhanced styling
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Card-like containers */
    .stButton>button, .stDownloadButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 12px 20px;
        border: none;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 5px 0;
    }
    
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Form styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    
    .stTextArea>div>textarea {
        border-radius: 8px;
    }
    
    /* Success/Error message styling */
    .stSuccess, .stError {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #1E1E1E;
        margin-bottom: 1.5rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        padding: 2rem 1rem;
    }
    
    /* DataFrame styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Code block styling */
    .stCodeBlock {
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Radio button styling */
    .stRadio>div {
        padding: 10px;
        background: #f8f9fa;
        border-radius: 8px;
        margin: 5px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session states
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())
if "connection_initialized" not in st.session_state:
    st.session_state["connection_initialized"] = False

# Backend API Base URL
API_BASE_URL = "http://127.0.0.1:8000"

# Initialize global variables
df = pd.DataFrame()
plotly_fig = None

# Sidebar Configuration
with st.sidebar:
    st.title("🛠️ Configuration")
    
    # New Conversation Section
    st.sidebar.markdown("### 🔄 Start Fresh")
    if st.button("Start New Conversation", key="new_conv"):
        st.session_state["conversation_id"] = str(uuid.uuid4())
        st.session_state["connection_initialized"] = False
        st.success("🎉 New conversation started!")
    
    # Database Configuration
    st.markdown("### 📦 Database Setup")
    db_type = st.selectbox("Database Type", ["PostgreSQL", "MySQL"], 
                          help="Select your database type")
    
    # Database Configuration Form
    with st.form("db_config_form"):
        st.markdown("#### Connection Details")
        cols = st.columns(2)
        with cols[0]:
            db_name = st.text_input("Database", "dvdrental")
            db_user = st.text_input("Username", "postgres")
            db_host = st.text_input("Host", "localhost")
        with cols[1]:
            db_password = st.text_input("Password", "", type="password")
            db_port = st.text_input("Port", 
                                  "5432" if db_type == "PostgreSQL" else "3306")
        
        if st.form_submit_button("🔄 Test Connection"):
            with st.spinner("Testing connection..."):
                try:
                    response = requests.post(
                        f"{API_BASE_URL}/api/connection",
                        json={
                            "db_type": db_type.lower(),
                            "dbname": db_name,
                            "user": db_user,
                            "password": db_password,
                            "host": db_host,
                            "port": int(db_port)
                        }
                    )
                    if response.status_code == 200:
                        st.success("✅ Connected successfully!")
                        st.session_state["connection_initialized"] = True
                    else:
                        st.error(response.json().get("detail", 
                                                   "Connection failed"))
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

    # Query Analysis Toggle
    show_query_analysis = st.checkbox("🔍 Show Query Optimization Insights",
                                    help="View detailed query performance analysis")

# Main Content
st.title("💬 Data Query Assistant")
st.markdown("Transform your natural language into powerful database queries!")

# Query Input
query_container = st.container()
with query_container:
    query = st.text_area(
        "What would you like to know about your data?",
        height=100,
        placeholder="e.g., Show me the top 5 customers by rental count",
        help="Enter your question in natural language"
    )

# Execute Query
if st.session_state["connection_initialized"]:
    if st.button("🚀 Execute Query", use_container_width=True):
        with st.spinner("Processing your query..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/query",
                    json={
                        "query": query,
                        "schema": "Provide the schema for the dvdrental database here.",
                        "conversation_id": st.session_state["conversation_id"],
                        "show_analysis": show_query_analysis
                    }
                )
                
                if response.status_code == 200:
                    st.success("Query executed successfully! 🎉")
                    
                    # Display results in tabs
                    tabs = st.tabs(["📊 Results", "🔍 SQL", "📈 Visualization"])
                    
                    with tabs[0]:
                        results = response.json().get("results", [])
                        if results:
                            df = pd.DataFrame(results)
                            st.dataframe(df, use_container_width=True)
                            
                            # Export options
                            col1, col2 = st.columns(2)
                            with col1:
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    "📥 Download CSV",
                                    csv,
                                    "results.csv",
                                    "text/csv",
                                    use_container_width=True
                                )
                    
                    with tabs[1]:
                        st.code(response.json().get("sql", ""), language="sql")
                        if show_query_analysis:
                            st.markdown("#### ⚡ Performance Analysis")
                            performance_analysis = response.json().get("performance_analysis", [])
                            formatted_analysis = "\n".join([
                                "  " * str(line).count("->") + str(line).replace("->", "").strip()
                                for line in performance_analysis
                            ])
                            st.code(formatted_analysis, language="sql")
                    
                    with tabs[2]:
                        if df.empty:
                            st.info("No data available for visualization")
                        else:
                            try:
                                graph_response = requests.post(
                                    f"{API_BASE_URL}/api/generate_graph",
                                    json={"data": df.to_dict(orient="records")}
                                )
                                
                                if graph_response.status_code == 200:
                                    graph_data = graph_response.json().get("graph", {})
                                    if graph_data:
                                        plotly_fig = pio.from_json(json.dumps(graph_data))
                                        st.plotly_chart(plotly_fig, use_container_width=True)
                                        
                                        # Export graph
                                        if plotly_fig:
                                            html_str = plotly_fig.to_html(
                                                full_html=True,
                                                include_plotlyjs="cdn"
                                            )
                                            st.download_button(
                                                "📥 Download Interactive Graph",
                                                html_str.encode('utf-8'),
                                                "visualization.html",
                                                "text/html",
                                                use_container_width=True
                                            )
                            except Exception as e:
                                st.error(f"Visualization error: {str(e)}")
                
                else:
                    st.error(response.json().get("detail", "Query failed"))
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
else:
    st.warning("⚠️ Please configure and test your database connection first")

# Feedback Section
with st.expander("✨ Provide Feedback"):
    feedback = st.radio(
        "Was this query helpful?",
        ["Yes", "No"],
        horizontal=True
    )
    
    if st.button("Submit Feedback", use_container_width=True):
        try:
            response = requests.post(
                f"{API_BASE_URL}/api/feedback",
                json={
                    "query": query,
                    "feedback": feedback,
                    "conversation_id": st.session_state["conversation_id"]
                }
            )
            if response.status_code == 200:
                st.success("Thank you for your feedback! 🙏")
            else:
                st.error("Failed to submit feedback")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# History Section
with st.sidebar.expander("📜 Query History"):
    if st.button("View All Queries"):
        response = requests.get(f"{API_BASE_URL}/api/query/history")
        if response.status_code == 200:
            history = response.json().get("query_history", [])
            for i, entry in enumerate(history, 1):
                st.markdown(f"**Query {i}:** {entry['query']}")
                st.markdown("---")
    
    if st.button("View Current Conversation"):
        response = requests.get(
            f"{API_BASE_URL}/api/context/{st.session_state['conversation_id']}"
        )
        if response.status_code == 200:
            context = response.json().get("context", {})
            if context and context.get("queries"):
                for i, query in enumerate(context["queries"], 1):
                    st.markdown(f"**Query {i}:** {query}")
                    st.markdown("---")
    
    if st.button("Clear History"):
        if st.session_state["conversation_id"]:
            response = requests.delete(
                f"{API_BASE_URL}/api/context/{st.session_state['conversation_id']}"
            )
            if response.status_code == 200:
                st.success("History cleared!")
            else:
                st.error("Failed to clear history")