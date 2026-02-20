import React from "react";
import AdPlayer from "../components/AdPlayer";
import LiveStatus from "../components/LiveStatus";

export default function PersonalizedView({ systemState, isConnected, sendJsonMessage }) {
  const [loopCount, setLoopCount] = React.useState(0);

  const handleAdEnd = () => {
    const nextCount = loopCount + 1;
    setLoopCount(nextCount);
    console.log(`[Personalized] Ad loop count: ${nextCount}`);
    
    if (nextCount >= 2) {
        console.log("[Personalized] Reached 2 loops, triggering timeout...");
        sendJsonMessage({ type: "AD_LOOP_TIMEOUT" });
    }
  };

  return (
    <div style={styles.wrap}>
      {/* CSS for the Task #9 Pulse Animation */}
      <style>
        {`
          @keyframes pulse-glow {
            0% { transform: translateX(-50%) scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); }
            70% { transform: translateX(-50%) scale(1.05); box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); }
            100% { transform: translateX(-50%) scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
          }
        `}
      </style>

      {/* Renders the ad and triggers the next one in the playlist when finished */}
      <AdPlayer
        src={systemState.ad ? `/ads/${systemState.ad}` : ""}
        show={true}
        onEnded={handleAdEnd}
      />

      <LiveStatus isConnected={isConnected} />

      {/* Existing Header Overlay */}
      <div style={styles.overlay}>
        <h2 style={{ margin: 0 }}>Personalized Experience</h2>
      </div>

      {/* Task #9: Bottom-Center Interaction Prompt */}
      <div style={styles.promptBadge}>
        <span style={styles.promptText}>"Hey Adorix to interact"</span>
      </div>
    </div>
  );
}

const styles = {
  wrap: {
    position: "relative",
    width: "100vw",
    height: "100vh",
    overflow: "hidden",
    background: "#070b12",
  },
  overlay: {
    position: "absolute",
    top: 40,
    right: 40,
    color: "white",
    zIndex: 10,
    textAlign: "right",
  },
  promptBadge: {
    position: "absolute",
    bottom: "10%",
    left: "50%",
    transform: "translateX(-50%)",
    background: "rgba(255, 255, 255, 0.15)",
    backdropFilter: "blur(12px)",
    padding: "14px 32px",
    borderRadius: "50px",
    border: "1px solid rgba(255, 255, 255, 0.25)",
    boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    animation: "pulse-glow 2s infinite ease-in-out",
    zIndex: 20,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  promptText: {
    color: "white",
    fontSize: "1.3rem",
    fontWeight: "600",
    letterSpacing: "0.5px",
    whiteSpace: "nowrap",
    textShadow: "0 2px 4px rgba(0,0,0,0.5)",
  },
};