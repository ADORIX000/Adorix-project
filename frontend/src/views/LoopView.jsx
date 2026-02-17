import { useState } from 'react';

const adVideos = [
  '/ads/10-15_male.mp4',
  '/ads/10-15_female.mp4',
  '/ads/16-29_male.mp4',
  '/ads/16-29_female.mp4',
  '/ads/30-39_male.mp4',
  '/ads/30-39_female.mp4',
  '/ads/40-49_male.mp4',
  '/ads/40-49_female.mp4',
  '/ads/50-59_male.mp4',
  '/ads/50-59_female.mp4',
  '/ads/above-60_male.mp4',
  '/ads/above-60_female.mp4',

];

const LoopView = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [error, setError] = useState(null);

  const handleVideoEnd = () => {
    console.log("Video finished, moving to next...");
    setCurrentIndex((prevIndex) => (prevIndex + 1) % adVideos.length);
    setError(null); // Reset error on change
  };

  const handleVideoError = (e) => {
    console.error("Video failed to load:", adVideos[currentIndex]);
    setError(`Failed to load: ${adVideos[currentIndex]}`);
  };

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