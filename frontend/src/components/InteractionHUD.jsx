export default function InteractionHUD({ showMic }) {
  return (
    <div className="absolute bottom-16 w-full flex flex-col items-center justify-center z-40 transition-opacity duration-500">
      
      {showMic ? (
        // Active Microphone UI
        <div className="flex flex-col items-center">
          <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center animate-bounce shadow-[0_0_40px_rgba(37,99,235,0.8)] border-4 border-white/20">
            <span className="text-4xl">🎙️</span>
          </div>
          <p className="text-blue-100 font-semibold mt-4 tracking-widest uppercase text-sm animate-pulse">
            Listening...
          </p>
        </div>
      ) : (
        // Call to Action Prompt
        <div className="bg-black/60 backdrop-blur-xl px-10 py-5 rounded-3xl border border-white/20 text-center shadow-2xl">
          <p className="text-gray-400 text-xs tracking-[0.2em] uppercase mb-2">To interact with Adorix</p>
          <h2 className="text-white text-3xl font-bold tracking-wide">Say "Hey Adorix"</h2>
        </div>
      )}

    </div>
  );
}