export const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function readApiResponse(response, fallbackMessage) {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : fallbackMessage;
    throw new Error(detail);
  }
  if (!data || typeof data !== "object") {
    throw new Error("The server returned an unreadable response. Please try again.");
  }
  return data;
}
