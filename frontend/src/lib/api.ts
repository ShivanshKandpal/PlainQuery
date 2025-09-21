const API_BASE_URL = (import.meta as any)?.env?.VITE_API_URL || 'http://localhost:5000';

export interface ApiQueryResult {
  request_id: string;
  sql_query: string;
  result: any[][];
  columns: string[];
  latency: number;
  cost: number;
  total_cost: number;
  feedback_applied?: boolean;
  original_request_id?: string;
}

export interface ApiMonitoringResult {
  total_requests: number;
  total_feedback_sessions: number;
  total_cost: number;
  cost_cap: number;
  remaining_budget: number;
  recent_requests: Array<{
    request_id: string;
    timestamp: string;
    question: string;
    latency: number;
    cost: number;
    total_cost: number;
  }>;
  recent_feedback_sessions: Array<{
    feedback_request_id: string;
    original_request_id: string;
    timestamp: string;
    original_question: string;
    feedback: string;
    latency: number;
    cost: number;
  }>;
  average_latency: number;
  feedback_improvement_rate: number;
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
  },

  async getMonitoring(): Promise<ApiMonitoringResult> {
    const response = await fetch(`${API_BASE_URL}/monitoring`);

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error || 'Failed to get monitoring data');
    }

    return response.json();
  },

  async resetMonitoring(): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/reset_monitoring`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error || 'Failed to reset monitoring');
    }

    return response.json();
  },

  async submitFeedback(requestId: string, originalQuestion: string, feedback: string): Promise<ApiQueryResult> {
    const response = await fetch(`${API_BASE_URL}/submit_feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        request_id: requestId,
        original_question: originalQuestion,
        feedback: feedback,
      }),
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw new Error(error.error || 'Failed to submit feedback');
    }

    return response.json();
  }
};