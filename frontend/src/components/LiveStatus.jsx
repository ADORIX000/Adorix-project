export default function LiveStatus({ isConnected }) {
  return (
    <div className="absolute top-8 right-8 z-50 flex items-center gap-3 bg-black/50 backdrop-blur-md px-5 py-2.5 rounded-full border border-white/10 shadow-lg">
      <div className={`w-3.5 h-3.5 rounded-full ${isConnected ? 'bg-green-500 animate-slow-pulse shadow-[0_0_12px_#22c55e]' : 'bg-red-500'}`}></div>
      <span className="text-white text-xs font-bold tracking-[0.2em] uppercase opacity-90">
        {isConnected ? 'Live Sensing' : 'System Offline'}
      </span>
    </div>
  );
}