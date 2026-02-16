import React from "react";
import AdPlayer from "../components/AdPlayer";

export default function PersonalizedView({ adVideo }) {
  return (
    <div style={styles.wrap}>
      <AdPlayer src={adVideo} show />
      <div style={styles.overlay}>
        <h2>Personalized Ad</h2>
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
  },
  overlay: {
    position: "absolute",
    top: 40,
    right: 40,
    color: "white",
    zIndex: 10,
  },
};