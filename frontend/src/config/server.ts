const STORAGE_KEY = 'cc_server_url';

export function isCapacitor(): boolean {
  return !!(window as unknown as Record<string, unknown>).Capacitor;
}

export function getServerUrl(): string {
  return localStorage.getItem(STORAGE_KEY) || '';
}

export function setServerUrl(url: string) {
  // Normalize: remove trailing slash
  const normalized = url.replace(/\/+$/, '');
  localStorage.setItem(STORAGE_KEY, normalized);
}

export function clearServerUrl() {
  localStorage.removeItem(STORAGE_KEY);
}

export function getApiBase(): string {
  if (!isCapacitor()) return '';
  return getServerUrl();
}

export function getWsUrl(): string {
  if (!isCapacitor()) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws`;
  }
  const server = getServerUrl();
  if (!server) return '';
  const wsProtocol = server.startsWith('https') ? 'wss:' : 'ws:';
  const host = server.replace(/^https?:\/\//, '');
  return `${wsProtocol}//${host}/ws`;
}
