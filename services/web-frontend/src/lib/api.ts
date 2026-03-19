
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://flying-coin.thinhopsops.win/api/v1";

export async function apiFetch(endpoint: string, options: RequestInit = {}, token?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    console.log(`[API] Sending request with token: ${token.substring(0, 10)}...`);
    headers["Authorization"] = `Bearer ${token}`;
  } else {
    console.warn(`[API] Sending request WITHOUT token to: ${endpoint}`);
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `API error: ${response.status}`);
  }

  return response.json();
}

export const marketApi = {
  getLatestPrice: (ticker: string, token?: string) => apiFetch(`/market-data/symbols/${ticker}/latest`, {}, token),
  listSymbols: (token?: string) => apiFetch("/market-data/symbols", {}, token),
  getHistory: (ticker: string, token?: string) => apiFetch(`/market-data/symbols/${ticker}/history`, {}, token),
};

export const sentimentApi = {
  getSentiment: (symbol: string, token?: string) => apiFetch(`/sentiment/${symbol}`, {}, token),
  getHistory: (symbol: string, token?: string) => apiFetch(`/sentiment/${symbol}/history`, {}, token),
};

export const forecastApi = {
  getForecast: (ticker: string, token?: string) => apiFetch(`/forecast/${ticker}`, {}, token),
};
