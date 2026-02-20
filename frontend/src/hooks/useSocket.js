import useWebSocket from 'react-use-websocket';

export const useSocket = (url) => {
  const { lastJsonMessage, readyState, sendJsonMessage } = useWebSocket(url, {
    shouldReconnect: () => true,
    reconnectInterval: 3000,
  });
  return { 
    lastMessage: lastJsonMessage, 
    isConnected: readyState === 1,
    sendJsonMessage 
  };
};