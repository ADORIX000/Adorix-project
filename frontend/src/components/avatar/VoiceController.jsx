import { useEffect, useRef, useState } from "react";

export default function VoiceController({
  onWake,
  onListening,
  onSpeaking,
  onIdle,
  setSubtitle,
}) {
  const recognitionRef = useRef(null);
  const listeningRef = useRef(false);

  const [micStatus, setMicStatus] = useState("OFF"); // OFF | LISTENING | SPEAKING
  const [supported, setSupported] = useState(true);

  // --- INIT SPEECH RECOGNITION ---
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recog = new SpeechRecognition();
    recog.lang = "en-US";
    recog.continuous = true;
    recog.interimResults = false;

    recog.onresult = (event) => {
      const text = event.results[event.results.length - 1][0].transcript
        .toLowerCase()
        .trim();

      console.log("🎤 Heard:", text);

      // WAKE WORD
      if (text.includes("hey adorix") && !listeningRef.current) {
        listeningRef.current = true;
        setMicStatus("LISTENING");

        onWake();
        setSubtitle("👂 I'm listening...");
        setTimeout(onListening, 700);
        return;
      }

      // QUESTION
      if (listeningRef.current) {
        recog.stop();
        setMicStatus("SPEAKING");

        onSpeaking();
        setSubtitle(`You asked: "${text}"`);

        speakAnswer(
          "Here is a demo response from Adorix. This will be replaced by the real backend.",
          () => {
            listeningRef.current = false;
            setMicStatus("OFF");
            setSubtitle("");
            onIdle();
            startRecognition();
          }
        );
      }
    };

    recog.onerror = (e) => {
      console.error("Speech error:", e);
      setMicStatus("OFF");
    };

    recognitionRef.current = recog;
    startRecognition();

    return () => recog.stop();
  }, []);

  // --- START LISTENING ---
  const startRecognition = () => {
    try {
      recognitionRef.current?.start();
      setMicStatus("OFF");
    } catch {}
  };

  // --- TTS ---
  const speakAnswer = (text, onEnd) => {
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1;
    utter.pitch = 1;
    utter.onend = onEnd;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
  };

  if (!supported) {
    return (
      <div className="voice-warning">
        ❌ Speech Recognition not supported on this browser
      </div>
    );
  }

  return (
    <div className={`mic-indicator ${micStatus.toLowerCase()}`}>
      🎤 Mic: {micStatus}
    </div>
  );
}
