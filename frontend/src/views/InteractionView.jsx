import React from "react";
import AvatarOverlay from "../avatar/AvatarOverlay";
import InteractionHUD from "../components/InteractionHUD";

export default function InteractionView({ state }) {
  return (
    <div style={styles.wrap}>
      <AvatarOverlay state={state} />
      <InteractionHUD state={state} />
    </div>
  );
}

const styles = {
  wrap: {
    position: "relative",
    width: "100vw",
    height: "100vh",
  },
};