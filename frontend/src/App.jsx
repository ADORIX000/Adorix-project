import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Import Components
import LoopMode from './components/LoopMode';
import DeliveryMode from './components/DeliveryMode';
import AvatarMode from './components/AvatarMode';

function App() {
  const [systemState, setSystemState] = useState({
    mode: "LOOP",
    video: "default_loop.mp4",
    avatar_speaking: false,
    avatar_message: ""
  });

  // Poll Backend every 500ms
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await axios.get('http://localhost:5000/status');
        setSystemState(res.data);
      } catch (err) {
        console.error("Backend Disconnected");
      }
    }, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-screen h-screen bg-black overflow-hidden">
      {/* 1. LOOP MODE */}
      {systemState.mode === "LOOP" && (
        <LoopMode />
      )}

      {/* 2. DELIVERY MODE (Personalized Ad) */}
      {systemState.mode === "DELIVERY" && (
        <DeliveryMode videoFile={systemState.video} />
      )}

      {/* 3. INTERACTION MODE (Avatar) */}
      {systemState.mode === "INTERACTION" && (
        <AvatarMode 
          isSpeaking={systemState.avatar_speaking} 
          message={systemState.avatar_message} 
        />
      )}
    </div>
  );
}

export default App;