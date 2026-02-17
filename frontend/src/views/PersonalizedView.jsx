import InteractionHUD from '../components/InteractionHUD';

export default function PersonalizedView({ adUrl }) {
  return (
    <div className="absolute inset-0 w-full h-full z-10 bg-black">
      <video 
        className="w-full h-full object-cover" 
        src={`/ads/${adUrl}`} 
        autoPlay 
        loop 
        muted 
      />
      <InteractionHUD showMic={false} />
    </div>
  );
}