const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export async function getJSON<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return response.json();
}
