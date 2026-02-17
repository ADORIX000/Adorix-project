import React from "react";
import AdPlayer from "../components/AdPlayer";

export default function LoopView({ systemState }) {
  return (
    <div style={styles.wrap}>
      <AdPlayer src="/ads/default.mp4" show />

      <div style={styles.overlay}>
        <h1>ADORIX</h1>
        <p>Smart AI Advertising Experience</p>
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
    bottom: 40,
    left: 40,
    color: "white",
    zIndex: 10,
  },
};