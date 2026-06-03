export interface ApiResponse<T> {
  data: T;
}

export interface ApiListResponse<T> {
  data: T[];
  meta: {
    cursor: string | null;
    has_more: boolean;
    limit: number;
  };
}

export interface ApiError {
  status: number;
  code: string;
  message: string;
  detail: string;
  instance: string;
  trace_id: string;
}
