export default function LiveStatus({ isConnected }) {
  return (
    // Tailwind: Fixed top-right, flexbox layout, blur effect
    <div className="absolute top-6 right-6 z-50 flex items-center gap-3 bg-black/40 backdrop-blur-sm px-4 py-2 rounded-full border border-white/10">
      <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-slow-pulse shadow-[0_0_10px_#22c55e]' : 'bg-red-500'}`}></div>
      <span className="text-white text-xs font-bold tracking-widest">
        {isConnected ? 'LIVE SENSING' : 'OFFLINE'}
      </span>
    </div>
  );
}