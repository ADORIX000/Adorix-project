import React from "react";

export default function AdPlayer({ src, show = true }) {
  if (!show || !src) return null;

  return (
    <video
      key={src}
      src={src}
      autoPlay
      muted
      loop
      playsInline
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