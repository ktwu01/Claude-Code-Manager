import { useEffect, useRef, useState } from 'react';
import { WsClient } from '../api/ws';
import { getWsUrl } from '../config/server';

/**
 * useWebSocket hook with callback support.
 *
 * IMPORTANT: Use the `onMessage` callback for high-frequency streams (e.g. chat).
 * The old `lastMessage` state pattern loses messages when React batches rapid
 * state updates — the useEffect depending on lastMessage only fires for the
 * last value in a batch, silently dropping intermediate messages.
 */
export function useWebSocket(
  channels: string[],
  onMessage?: (msg: Record<string, unknown>) => void,
) {
  const clientRef = useRef<WsClient | null>(null);
  const callbackRef = useRef(onMessage);
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Keep callback ref in sync without triggering reconnect
  callbackRef.current = onMessage;

  useEffect(() => {
    const wsUrl = getWsUrl();
    if (!wsUrl) return;
    const client = new WsClient(wsUrl);
    clientRef.current = client;

    client.onMessage((msg) => {
      const parsed = msg as unknown as Record<string, unknown>;
      callbackRef.current?.(parsed);
      setLastMessage(parsed);
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
