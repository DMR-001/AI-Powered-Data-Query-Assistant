import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
import json
import numpy as np

class GraphGeneratingAgent:
    def generate_graph(self, data: list[dict], requested_graph_type: str = None):
        """
        Generate a graph based on the provided data and requested graph type.
        """
        try:
            # Convert data to a DataFrame and validate it
            if not data:
                raise ValueError("No data provided for graph generation.")
            df = pd.DataFrame(data)
            if df.empty:
                raise ValueError("Dataframe is empty. Cannot generate graph.")

            # Identify numeric and categorical columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

            # Automatic Graph Type Detection Based on Data
            if not requested_graph_type:
                if len(df.columns) == 1:
                    requested_graph_type = "pie"
                elif len(df.columns) == 2:
                    if len(numeric_cols) == 1 and len(categorical_cols) == 1:
                        requested_graph_type = "bar"
                    elif len(numeric_cols) == 2:
                        requested_graph_type = "scatter"
                    else:
                        requested_graph_type = "table"  # Defaulting to table if no numeric data is available
                else:
                    requested_graph_type = "correlation" if len(numeric_cols) >= 2 else "table"

            # Correlation Matrix (Heatmap)
            if requested_graph_type == "correlation":
                numeric_df = df.select_dtypes(include=[np.number])
                if numeric_df.shape[1] < 2:
                    raise ValueError("At least two numerical columns are required for correlation matrix.")
                correlation_matrix = numeric_df.corr()
                fig = px.imshow(correlation_matrix, title="Correlation Matrix (Heatmap)")

            # Heatmap
            elif requested_graph_type == "heatmap":
                numeric_df = df.select_dtypes(include=[np.number])
                fig = px.imshow(numeric_df.corr(), title="Heatmap")

            # Box Plot
            elif requested_graph_type == "box":
                if not numeric_cols:
                    raise ValueError("Box plot requires at least one numeric column.")
                fig = px.box(df, y=numeric_cols[0], title="Box Plot")

            # Histogram
            elif requested_graph_type == "histogram":
                if not numeric_cols:
                    raise ValueError("Histogram requires at least one numeric column.")
                fig = px.histogram(df, x=numeric_cols[0], title="Histogram")

            # Time Series Chart
            elif requested_graph_type == "time_series":
                if 'date' not in df.columns[0].lower():
                    raise ValueError("Time series requires a date column.")
                fig = px.line(df, x=df.columns[0], y=df.columns[1], title="Time Series Chart")

            # Bar Chart
            elif requested_graph_type == "bar":
                if len(numeric_cols) == 1 and len(categorical_cols) >= 1:
                    fig = px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title="Bar Chart")
                else:
                    raise ValueError("Bar chart requires one numeric and one categorical column.")

            # Line Chart
            elif requested_graph_type == "line":
                if len(df.columns) != 2:
                    raise ValueError("Line chart requires exactly two columns.")
                fig = px.line(df, x=df.columns[0], y=df.columns[1], title="Line Chart")

            # Scatter Plot
            elif requested_graph_type == "scatter":
                if len(df.columns) != 2:
                    raise ValueError("Scatter plot requires exactly two columns.")
                fig = px.scatter(df, x=df.columns[0], y=df.columns[1], title="Scatter Plot")

            # Pie Chart with Conflict Handling
            elif requested_graph_type == "pie":
                if df.shape[1] != 1:
                    raise ValueError("Pie chart requires exactly one column.")
                
                # Column Conflict
                pie_data = df[df.columns[0]].value_counts().reset_index()
                if 'count' in pie_data.columns:
                    pie_data.columns = ['category', 'value']
                else:
                    pie_data.columns = ['category', 'count']

                # Prevent further conflicts if the original df already has a 'count' column
                if 'count' in df.columns:
                    pie_data = pie_data.rename(columns={"count": "value"})

                # Generate Pie Chart
                fig = px.pie(pie_data, names='category', values='value', title="Pie Chart")

            # Network Graph
            elif requested_graph_type == "network":
                if df.shape[1] != 2:
                    raise ValueError("Network graph requires exactly two columns.")
                G = nx.from_pandas_edgelist(df, source=df.columns[0], target=df.columns[1])
                pos = nx.spring_layout(G)
                edge_x, edge_y = [], []

                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='#888'))
                node_trace = go.Scatter(x=[pos[node][0] for node in G.nodes()],
                                        y=[pos[node][1] for node in G.nodes()],
                                        mode='markers+text',
                                        marker=dict(size=15),
                                        text=[str(node) for node in G.nodes()])

                fig = go.Figure(data=[edge_trace, node_trace])

            # Table Display
            elif requested_graph_type == "table":
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(df.columns), fill_color='lightgrey'),
                    cells=dict(values=[df[col].tolist() for col in df.columns])
                )])
                fig.update_layout(title="Table Display")

            else:
                raise ValueError(f"Unsupported graph type: {requested_graph_type}")

            # Return the generated graph as JSON
            return {"graph": json.loads(fig.to_json()), "graph_type": requested_graph_type}

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error in GraphGeneratingAgent: {error_details}")
            raise ValueError(f"Graph generation failed: {str(e)}")

