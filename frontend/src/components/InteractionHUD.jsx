import React from 'react';

const InteractionHUD = ({ isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="hud-overlay" style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)' }}>
      <div className="avatar-circle">
        {/* You can put an animated GIF or SVG of your avatar here */}
        <img src="assets/avatar_idle.gif" alt="Adorix Avatar" style={{ width: '150px' }} />
      </div>
      <h2 style={{ color: 'white', textShadow: '2px 2px 4px black' }}>
        "Say 'Hey Adorix' to ask a question!"
      </h2>
    </div>
  );
};

export default InteractionHUD;