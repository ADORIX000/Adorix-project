export default function LoopView() {
  return (
    <div className="absolute inset-0 w-full h-full z-0 bg-black flex items-center justify-center overflow-hidden">
      <video 
        className="w-full h-full object-cover opacity-80" 
        src="/ads/10-15_female.mp4" 
        autoPlay 
        loop 
        muted 
        onError={(e) => {
          console.error("Video failed to load", e);
          e.target.style.display = 'none';
        }}
      />
    </div>
  );
}