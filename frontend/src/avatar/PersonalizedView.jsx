import InteractionHUD from '../components/InteractionHUD';

export default function PersonalizedView({ adUrl }) {
  return (
    <div className="absolute inset-0 w-full h-full z-10">
      {/* The Targeted Ad */}
      <video 
        className="w-full h-full object-cover" 
        src={`/ads/${adUrl}`} 
        autoPlay 
        loop 
        muted 
      />
      
      {/* Tailwind: Positioned absolute at the bottom, centered */}
      <div className="absolute bottom-12 w-full flex justify-center z-20">
        <div className="bg-black/60 backdrop-blur-md px-8 py-4 rounded-full border border-white/20 text-center shadow-2xl">
          <p className="text-gray-300 text-sm tracking-widest uppercase mb-1">To interact with Adorix</p>
          <h2 className="text-white text-3xl font-bold tracking-wide">Say "Hey Adorix"</h2>
        </div>
      </div>
    </div>
  );
}