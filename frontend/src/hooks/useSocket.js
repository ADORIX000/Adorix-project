import { useEffect, useRef, useState } from "react";

export default function useSocket(url = "ws://127.0.0.1:8000/ws") {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        setLastMessage(JSON.parse(event.data));
      } catch {
        setLastMessage({ raw: event.data });
      }
    };

    return () => ws.close();
  }, [url]);

  return { isConnected, lastMessage, wsRef };
}