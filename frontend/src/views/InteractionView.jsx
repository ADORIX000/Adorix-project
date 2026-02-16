import React from "react";
import AvatarOverlay from "../avatar/AvatarOverlay";
import InteractionHUD from "../components/InteractionHUD";
import LiveStatus from "../components/LiveStatus";

export default function InteractionView({ systemState, isConnected }) {
  return (
    <div style={styles.wrap}>
      <AvatarOverlay state={systemState.avatar_state} />

      <LiveStatus isConnected={isConnected} />

      <InteractionHUD
        state={systemState.avatar_state}
        subtitle={systemState.subtitle}
      />
    </div>
  );
}

const styles = {
  wrap: {
    position: "relative",
    width: "100vw",
    height: "100vh",
    background: "#070b12",
    overflow: "hidden",
  },
};