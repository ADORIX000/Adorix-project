import AvatarOverlay from '../avatar/AvatarOverlay';
import InteractionHUD from '../components/InteractionHUD';

export default function InteractionView({ adUrl, avatarState, isMicActive }) {
  return (
    <div className="absolute inset-0 w-full h-full z-20 bg-black">
      {/* Dim the background ad so the Avatar pops out more */}
      <video 
        className="w-full h-full object-cover brightness-40 transition-all duration-500" 
        src={`/ads/${adUrl}`} 
        autoPlay 
        loop 
        muted 
      />
      
      <AvatarOverlay state={avatarState} />
      
      {/* Show the mic HUD only if the system is actively recording user audio */}
      {isMicActive && <InteractionHUD showMic={true} />}
    </div>
  );
}