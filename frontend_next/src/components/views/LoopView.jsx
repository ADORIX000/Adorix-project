"use client";
import { useState, useEffect } from 'react';

const LoopView = () => {
  const [adVideos, setAdVideos] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Fetch the list of ads from the backend
    const fetchAds = async () => {
      try {
        const response = await fetch('/api/ads');
        const data = await response.json();
        
        // Add /ads/ prefix to each filename
        const fullPaths = data.map(name => `/ads/${name}`);
        setAdVideos(fullPaths);
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch ads:", err);
        setError("Could not connect to backend server.");
        setLoading(false);
      }
    };

    fetchAds();
  }, []);

  const handleVideoEnd = () => {
    if (adVideos.length === 0) return;
    setCurrentIndex((prevIndex) => (prevIndex + 1) % adVideos.length);
    setError(null);
  };

  const handleVideoError = (e) => {
    console.error("Video failed to load:", adVideos[currentIndex]);
    setError(`Failed to load: ${adVideos[currentIndex]}`);
  };

  if (loading) {
    return (
      <div className="w-screen h-screen bg-black flex items-center justify-center text-white font-mono">
        <div className="p-8 border border-white/20 rounded-xl bg-white/5 backdrop-blur-md">
            ⌛ Loading Ad Inventory...
        </div>
      </div>
    );
  }

  if (adVideos.length === 0 && !loading) {
     return (
        <div className="w-screen h-screen bg-black flex items-center justify-center text-white font-mono text-center">
             <div className="p-8 border border-red-500/50 rounded-xl bg-red-500/5">
                ❌ No active ads found in /ads folder.<br/>
                <span className="text-gray-400 text-sm">Please run synchronization first.</span>
             </div>
        </div>
     );
  }

  return (
    <div style={{ position: 'relative', width: '100vw', height: '100vh', background: '#000' }}>
      {/* 1. THE VIDEO PLAYER */}
      <video
        key={adVideos[currentIndex]} 
        src={adVideos[currentIndex]}
        autoPlay
        muted
        onEnded={handleVideoEnd}
        onError={handleVideoError}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />

      {/* 2. DEBUG OVERLAY (Only for testing) */}
      <div style={{
        position: 'absolute',
        top: 20,
        left: 20,
        padding: '15px',
        background: 'rgba(0,0,0,0.7)',
        color: 'white',
        fontFamily: 'monospace',
        borderRadius: '8px',
        border: error ? '2px solid red' : '1px solid green'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>Video Loop Tester</h3>
        <p><strong>Current Path:</strong> {adVideos[currentIndex]}</p>
        <p><strong>Status:</strong> {error ? "❌ ERROR" : "✅ Playing"}</p>
        {error && <p style={{ color: '#ff4444' }}>{error}</p>}
        
        <button onClick={handleVideoEnd} style={{ marginTop: '10px', cursor: 'pointer' }}>
          Skip to Next Video
        </button>
      </div>
    </div>
  );
};

export default LoopView;