export default function LoopView() {
  return (
    <div className="absolute inset-0 w-full h-full z-0">
      <video 
        className="w-full h-full object-cover opacity-80" 
        src="/ads/generic_loop.mp4" 
        autoPlay 
        loop 
        muted 
      />
    </div>
  );
}