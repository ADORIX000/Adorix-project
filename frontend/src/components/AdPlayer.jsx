import React from "react";

export default function AdPlayer({ src, show = true, onEnded }) {
  if (!show || !src) return null;

  return (
    <video
      key={src}
      src={src}
      autoPlay
      muted
      playsInline
      onEnded={onEnded}
      onError={() => {
        console.error(`AdPlayer: Failed to load ad ${src}. Skipping.`);
        if (onEnded) onEnded();
      }}
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
    zIndex: 5,
  },
};