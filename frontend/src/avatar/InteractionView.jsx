import AvatarOverlay from '../avatar/AvatarOverlay';

export default function InteractionView({ adUrl }) {
  return (
    <div className="absolute inset-0 w-full h-full z-30">
      {/* The Ad continues playing darkly in the background */}
      <video 
        className="w-full h-full object-cover brightness-50" 
        src={`/ads/${adUrl}`} 
        autoPlay 
        loop 
      />
      
      {/* The Avatar appears at the bottom */}
      <AvatarOverlay />

      {/* Dynamic Mic Icon */}
      <div className="absolute bottom-8 w-full flex flex-col items-center justify-center z-40">
        <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center animate-bounce shadow-[0_0_30px_rgba(37,99,235,0.8)]">
          <span className="text-3xl">🎙️</span>
        </div>
        <p className="text-white font-semibold mt-3 tracking-wider">Listening...</p>
      </div>
    </div>
  );
}