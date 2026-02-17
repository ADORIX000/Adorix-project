import { useState, useEffect, useRef } from "react";

export function useSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    const connect = () => {
      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        console.log("✅ Connected to Adorix Backend");
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
        } catch (err) {
          console.error("WS Parse Error", err);
        }
      };

      ws.current.onclose = () => {
        console.log("🔌 Disconnected. Reconnecting in 3s...");
        setIsConnected(false);
        setTimeout(connect, 3000);
      };
    };

    connect();

    return () => ws.current?.close();
  }, [url]);

  return { isConnected, lastMessage };
}