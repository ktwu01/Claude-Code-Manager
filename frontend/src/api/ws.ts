type WsHandler = (data: { channel: string; data: Record<string, unknown> }) => void;

export class WsClient {
  private ws: WebSocket | null = null;
  private channels: string[] = [];
  private handlers: WsHandler[] = [];
  private retryDelay = 1000;
  private maxDelay = 30000;
  private url: string;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onopen = () => {
      this.retryDelay = 1000;
      if (this.channels.length > 0) {
        this.ws?.send(JSON.stringify({ action: 'subscribe', channels: this.channels }));
      }
    };
    this.ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.channel) {
          this.handlers.forEach((h) => h(msg));
        }
      } catch { /* ignore */ }
    };
    this.ws.onclose = () => {
      setTimeout(() => this.connect(), this.retryDelay);
      this.retryDelay = Math.min(this.retryDelay * 2, this.maxDelay);
    };
  }

  subscribe(channels: string[]) {
    this.channels = [...new Set([...this.channels, ...channels])];
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'subscribe', channels }));
    }
  }

  onMessage(handler: WsHandler) {
    this.handlers.push(handler);
    return () => {
      this.handlers = this.handlers.filter((h) => h !== handler);
    };
  }

  close() {
    this.ws?.close();
    this.ws = null;
  }
}
