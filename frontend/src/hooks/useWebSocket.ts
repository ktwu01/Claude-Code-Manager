import { useEffect, useRef, useState } from 'react';
import { WsClient } from '../api/ws';

export function useWebSocket(channels: string[]) {
  const clientRef = useRef<WsClient | null>(null);
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const client = new WsClient(`${protocol}//${window.location.host}/ws`);
    clientRef.current = client;

    client.onMessage((msg) => {
      setLastMessage(msg as unknown as Record<string, unknown>);
      setIsConnected(true);
    });

    client.connect();
    client.subscribe(channels);

    return () => client.close();
  }, []);

  useEffect(() => {
    clientRef.current?.subscribe(channels);
  }, [channels]);

  return { lastMessage, isConnected };
}
