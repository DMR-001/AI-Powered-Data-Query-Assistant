import pandas as pd

class DataProcessingAgent:
    def format_results(self, data: pd.DataFrame) -> dict:
        return data.to_dict(orient='records')

    def summarize_data(self, data: pd.DataFrame) -> dict:
        return {
            "row_count": len(data),
            "columns": list(data.columns),
            "sample": data.head().to_dict(orient='records'),
        }
