const API_BASE_URL = 'http://localhost:5000';

export interface ApiQueryResult {
  sql_query: string;
  result: any[][];
  columns: string[];
}

export interface ApiError {
  error: string;
}

export interface ApiSchemaResult {
  schema: string;
  schema_info: {
    table_name: string;
    row_count: number;
    columns: Array<{
      name: string;
      type: string;
      stats: string;
    }>;
  };
}

export interface ApiUploadResult {
  message: string;
  filename: string;
  schema: string;
  schema_info: {
    table_name: string;
    row_count: number;
    columns: Array<{
      name: string;
      type: string;
      stats: string;
    }>;
  };
}

export const api = {
  async generateSQL(question: string): Promise<ApiQueryResult> {
    const response = await fetch(`${API_BASE_URL}/generate_sql`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error || 'Failed to generate SQL');
    }

    return response.json();
  },

  async uploadCSV(file: File): Promise<ApiUploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload_csv`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error || 'Failed to upload CSV');
    }

    return response.json();
  },

  async getSchema(): Promise<ApiSchemaResult> {
    const response = await fetch(`${API_BASE_URL}/schema`);

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error || 'Failed to get schema');
    }

    return response.json();
  }
};