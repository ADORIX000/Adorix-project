import React from "react";
import AdPlayer from "../components/AdPlayer";
import LiveStatus from "../components/LiveStatus";

export default function PersonalizedView({ systemState, isConnected }) {
  return (
    <div style={styles.wrap}>
      {systemState.ad && <AdPlayer src={systemState.ad} show />}

      <LiveStatus isConnected={isConnected} />

      <div style={styles.overlay}>
        <h2>Personalized Experience</h2>
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
  },
};