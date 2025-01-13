Here’s a README file for the Data Query Assistant (DQA) project:

---

# Data Query Assistant (DQA) - Intelligent Database Querying System

## Project Overview
The Data Query Assistant (DQA) project aims to build an intelligent querying system that enables business users to interact with databases using natural language. The system leverages AI agents to interpret queries, generate SQL, execute them, and present results in a user-friendly format, democratizing access to data while ensuring security and accuracy.

---

## Features
- **Natural Language Processing**: Interpret and process user queries in natural language.
- **SQL Generation**: Automatically generate SQL queries based on the input query.
- **Graph Generation**: Visualize query results with interactive graphs (bar, line, pie, scatter, etc.).
- **Multi-Database Support**: PostgreSQL (primary) and MySQL (secondary).
- **Error Handling**: Provide user-friendly error messages and manage connection issues.
- **Streamlit Interface**: Intuitive user interface for interacting with the system, displaying query results, and exporting data.

---

## Sample Database
This project uses the [DVD Rental Database](https://www.postgresqltutorial.com/postgresql-getting-started/postgresql-sample-database/) as a test database. It contains 15 tables and realistic relationships including:
- Customer data
- Inventory information
- Payments and rental information

---

## Technical Requirements

### 1. Core Components

#### A. Agent Architecture

##### Base Agent (Text-to-SQL)
- Uses OpenAI's GPT-3.5-turbo or Mixtral (open-source alternative).
- Context management for multi-turn conversations.
- Capable of understanding the database schema.

##### Sub-Agents
- **Query Execution Agent**: Handles database connections, executes SQL queries safely, manages timeouts.
- **Data Processing Agent**: Formats query results, generates basic visualizations, provides summary statistics.
- **Graph Generation Agent**: Analyzes query results for suitable visualizations and generates interactive plots using Plotly.
- **Error Handling Agent**: Manages database connection errors and query syntax issues, providing user-friendly messages.

#### B. Database Integration
- Primary support for PostgreSQL.
- Secondary support for MySQL.
- Features like connection pooling, credential security, and timeout management.

#### C. User Interface
- Built with Streamlit, includes:
  - Chat interface for query input.
  - Results display area (table and graph views).
  - Export options (CSV, Excel, PNG for graphs).
  - Query history section.
  - Database connection configuration options.

### 2. Detailed Requirements

#### A. Database Connection Screen
- Select database type (PostgreSQL/MySQL).
- Input connection string.
- Test connection button and connection status indicator.
- Option to save the configuration.

#### B. Main Query Interface
- Chat-style input box for queries.
- Query history panel (collapsible).
- Display area for results:
  - Table view.
  - Graph view with type selector.
  - Export functionality (CSV, Excel, PNG for graphs).

#### C. Agent Implementation

- **Base Agent (Text-to-SQL)**:
  - `process_user_query(query: str) -> Dict[str, Any]`
  - `validate_sql(sql: str) -> bool`
  - `maintain_conversation_context(context: List[Dict]) -> None`

- **Query Execution Agent**:
  - `execute_query(sql: str) -> pd.DataFrame`
  - `validate_connection() -> bool`
  - `handle_timeouts() -> None`

- **Graph Generation Agent**:
  - `analyze_data_for_visualization(data: pd.DataFrame) -> List[str]`
  - `generate_graph(data: pd.DataFrame, graph_type: str) -> plotly.Figure`
  - `create_time_series(data: pd.DataFrame) -> plotly.Figure`
  - `generate_correlation_matrix(data: pd.DataFrame) -> plotly.Figure`
  - `create_network_graph(data: pd.DataFrame) -> plotly.Figure`

- **Data Processing Agent**:
  - `format_results(data: pd.DataFrame) -> Dict[str, Any]`
  - `generate_visualization(data: pd.DataFrame) -> Any`
  - `summarize_data(data: pd.DataFrame) -> Dict[str, str]`

### 3. API Endpoints

- **/api/query**
  - POST: Accepts natural language query.
  - Response: Query results + metadata.

- **/api/connection**
  - POST: Create or update connection.
  - GET: Test connection.
  - DELETE: Remove connection.

- **/api/history**
  - GET: Retrieve query history.
  - DELETE: Clear query history.

- **/api/graph**
  - POST: Generate specific graph type.
  - GET: Retrieve available graph types.

---

## Setup and Installation

### Prerequisites
- Python 3.x
- PostgreSQL/MySQL Database Server

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/DMR-001/AI-Powered-Data-Query-Assistant.git
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database and configure the connection.

### Running the Application

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. Configure the database connection in the app UI and start querying.

---

## API Documentation

### /api/query (POST)
#### Request Body
```json
{
  "query": "What are the most rented movies?"
}
```

#### Response
```json
{
  "data": [
    {"movie_title": "The Godfather", "rent_count": 120},
    {"movie_title": "The Dark Knight", "rent_count": 110}
  ],
  "metadata": {
    "query_time": "2025-01-13T15:00:00",
    "execution_time": 2.5
  }
}
```

### /api/connection (POST)
#### Request Body
```json
{
  "db_type": "postgresql",
  "connection_string": "host=localhost dbname=dvd_rental user=admin password=secret"
}
```

#### Response
```json
{
  "status": "success",
  "message": "Connection established successfully."
}
```

---

## Architecture

### Agent Interaction Diagrams
- The agents interact in a flow to process the user input, execute SQL queries, process results, and generate visualizations.

### Database Schema
- Includes tables like `customers`, `inventory`, `rentals`, `payments`, and more.

---

## Success Criteria

- **90% accuracy** in converting natural language queries to SQL.
- **Appropriate visualizations** generated based on query results.
- **Response time** under 5 seconds for simple queries.
- **Error handling** with user-friendly feedback.
- **Complete documentation** and test coverage.

---

## License

This project is licensed under the MIT License.

---

Feel free to expand on this based on your development process!