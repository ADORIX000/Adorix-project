import { useEffect, useRef } from "react";

export default function useSocket(onMessage) {
  const ws = useRef(null);

  useEffect(() => {
    const WS_URL = "ws://localhost:8000/ws";

    const connect = () => {
      ws.current = new WebSocket(WS_URL);

      ws.current.onopen = () =>
        console.log("✅ Connected to Adorix Backend");

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (err) {
          console.error("WS Parse Error", err);
        }
      };

      ws.current.onclose = () => {
        console.log("🔌 Disconnected. Reconnecting in 3s...");
        setTimeout(connect, 3000);
      };
    };

    connect();

    return () => ws.current?.close();
  }, [onMessage]);
}