import { ApiError } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const REQUEST_TIMEOUT_MS = 30000; // 30 seconds

type RequestMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestOptions {
  method?: RequestMethod;
  body?: unknown;
  headers?: Record<string, string>;
  timeout?: number;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  /**
   * SECURITY WARNING: Tokens are stored in localStorage which is vulnerable to XSS attacks.
   * TODO: Migrate to httpOnly cookies for production deployment.
   * See: https://owasp.org/www-community/attacks/xss/
   */
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  setToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
    }
  }

  setRefreshToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", token);
    }
  }

  clearTokens(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }

  private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, headers = {}, timeout = REQUEST_TIMEOUT_MS } = options;
    const token = this.getToken();

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...headers,
    };

    if (token) {
      requestHeaders["Authorization"] = `Bearer ${token}`;
    }

    // Create AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    const config: RequestInit = {
      method,
      headers: requestHeaders,
      signal: controller.signal,
    };

    if (body && method !== "GET") {
      config.body = JSON.stringify(body);
    }

    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}${endpoint}`, config);
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("요청 시간이 초과되었습니다. 다시 시도해주세요.");
      }
      throw new Error("네트워크 오류가 발생했습니다. 연결을 확인해주세요.");
    } finally {
      clearTimeout(timeoutId);
    }

    if (!response.ok) {
      // Handle specific status codes
      if (response.status === 401) {
        this.clearTokens();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        throw new Error("로그인이 필요합니다.");
      }

      // Parse error response
      const error: ApiError = await response.json().catch(() => ({ detail: "" }));

      // Return user-friendly error messages based on status code
      const errorMessages: Record<number, string> = {
        400: error.detail || "잘못된 요청입니다. 입력 내용을 확인해주세요.",
        403: error.detail || "이 작업을 수행할 권한이 없습니다.",
        404: error.detail || "요청한 리소스를 찾을 수 없습니다.",
        409: error.detail || "이미 존재하는 데이터와 충돌합니다.",
        422: error.detail || "입력 값이 올바르지 않습니다.",
        429: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
        500: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        502: "서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
        503: "서비스가 일시적으로 중단되었습니다. 잠시 후 다시 시도해주세요.",
      };

      throw new Error(
        errorMessages[response.status] ||
        error.detail ||
        `요청 처리 중 오류가 발생했습니다. (${response.status})`
      );
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "GET" });
  }

  post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "POST", body });
  }

  put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "PUT", body });
  }

  patch<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "PATCH", body });
  }

  delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

export const api = new ApiClient(API_URL);
