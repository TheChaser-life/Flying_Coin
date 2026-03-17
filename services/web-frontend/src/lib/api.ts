import { auth } from "@/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://flying-coin.thinhopsops.win/api/v1";

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  // Try to get session if on server side
  let token = "";
  try {
    const session = await auth();
    if (session?.user?.id) {
        // Note: next-auth v5 beta session structure might vary, 
        // usually you'd want the access_token if you stored it in session.
        // For now we assume the gateway might check cookies or we need to pass a header.
    }
  } catch (e) {
    // Client-side execution or no session
  }

  const url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || `API error: ${response.status}`);
  }

  return response.json();
}

export const marketApi = {
  getLatestPrice: (ticker: string) => apiFetch(`/market/symbols/${ticker}/latest`),
  listSymbols: () => apiFetch("/market/symbols"),
  getHistory: (ticker: string) => apiFetch(`/market/symbols/${ticker}/history`),
};

export const sentimentApi = {
  getSentiment: (symbol: string) => apiFetch(`/sentiment/${symbol}`),
};
