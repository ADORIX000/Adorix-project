import React from "react";

export default function AdPlayer({ src, show = true, onEnded }) {
  if (!show || !src) return null;

  return (
    <video
      key={src}
      src={src}
      autoPlay
      muted
      // Removed 'loop' so it can actually finish and trigger the next ad
      playsInline
      onEnded={onEnded}
      style={styles.video}
    />
  );
}

const styles = {
  video: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover",
    zIndex: 0,
  },
};