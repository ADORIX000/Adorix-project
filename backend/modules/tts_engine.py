import pyttsx3

engine = pyttsx3.init()

engine.setProperty('rate',150)#speed
engine.setProperty('volume',1.0)#volume
engine.setProperty('voice',engine.getProperty('voices')[1].id)



def speak(text):
    
    print(f"ADORIX:{text}")
    engine.say(text)
    engine.runAndWait() #wait until speaking is done

#Test the function
if __name__ == "__main__":
    speak("Hello , I am Adorix , How can i help you ?")
