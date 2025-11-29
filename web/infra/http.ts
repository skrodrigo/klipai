const BACKEND_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BACKEND_BASE_URL}${path}`;

  const response = await fetch(url, {
    credentials: "include",
    ...options,
    headers: {
      ...(options.headers ?? {}),
      ...(!(options.body instanceof FormData) && { "Content-Type": "application/json" }),
    },
  });

  if (!response.ok) {
    throw new Error(`Request to ${url} failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

function requestSSE(path: string): EventSource {
  const url = `${BACKEND_BASE_URL}${path}`;
  return new EventSource(url, { withCredentials: true });
}

export { BACKEND_BASE_URL, request, requestSSE };
