import { AVATAR_STATES } from './avatarStates';

export default function AvatarOverlay({ state }) {
  const isVisible = state !== AVATAR_STATES.HIDDEN;
  const videoSrc = isVisible ? `/assets/avatar/${AVATAR_STATES[state]}` : '';

  return (
    <div 
      className={`absolute bottom-0 left-0 w-full flex justify-center z-30 transition-transform duration-700 ease-in-out ${
        isVisible ? 'translate-y-0 opacity-100' : 'translate-y-[100%] opacity-0'
      }`}
    >
      {/* Assuming the avatar video is optimized for the screen width */}
      <video 
        className="w-[120%] max-w-2xl h-auto drop-shadow-2xl object-cover pointer-events-none"
        src={videoSrc}
        autoPlay
        muted // Must be muted to autoplay; audio comes from Python backend
        loop={['IDLE', 'TALKING', 'THINKING'].includes(state)}
      />
    </div>
  );
}