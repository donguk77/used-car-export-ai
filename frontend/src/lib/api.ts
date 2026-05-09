import axios, { type AxiosInstance } from "axios";

/**
 * 백엔드 API 베이스.
 * - dev: vite proxy 가 /api·/health 를 :8000 으로 보냄 (baseURL 빈값 = same-origin)
 * - prod: VITE_API_BASE_URL 환경변수로 백엔드 호스트 지정 (예: https://api.example.com)
 */
const baseURL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export const api: AxiosInstance = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 응답 받은 에러 (4xx/5xx)
    if (error.response) {
      console.error(
        "API error",
        error.config?.method?.toUpperCase(),
        error.config?.url,
        "→",
        error.response.status,
        error.response.data,
      );
    } else {
      // 네트워크 에러 / 타임아웃 / CORS — error.response 가 undefined
      console.error(
        "API network error",
        error.config?.method?.toUpperCase(),
        error.config?.url,
        "→",
        error.message,
      );
    }
    return Promise.reject(error);
  },
);
