# 🎬 ADORIX Kiosk - Quick Start Guide

## **Easiest Way: One-Click Start**

### **Option 1: Windows Batch (Automatic)**
```bash
START_SIMPLE.bat
```
This opens everything automatically!

### **Option 2: PowerShell**
```powershell
.\START_ADORIX.ps1
```

---

## **Manual Start (3 Steps)**

### **Step 1: Install Frontend Dependencies** (first time only)
```bash
cd frontend
npm install
```

### **Step 2: Start Kiosk (Terminal 1)**
```bash
python adorix_kiosk.py
```
✅ Camera window opens  
✅ Detects faces and shows age/gender  
✅ Plays ads when idle  
✅ WebSocket server starts on port 8000

### **Step 3: Start Frontend (Terminal 2)**
```bash
cd frontend
npm run dev
```
✅ Opens `http://localhost:5173`  
✅ Shows avatar + detected users  
✅ Displays current ad state

---

## **What You Should See**

### **Kiosk Window (Camera + Ads)**
- 📷 **Detecting Users?** → Shows camera with faces detected
- 🎬 **Idle?** → Shows ad video loop
- Press `q` to close camera window

### **Browser (Frontend)**
- 🙂 **Idle State** → Avatar smiling
- 👂 **Detecting Users** → Avatar listening, shows user info
- 📺 **Playing Ad** → Avatar shows TV emoji

### **Console Output**
```
✅ Vision detector started
▶️  Playing ad: furniture_ad.mp4
Detected: Female - Age 28
```

---

## **Troubleshooting**

### **Camera Not Showing?**
1. Check Windows Camera app works
2. Ensure webcam permission granted
3. Try `python adorix_kiosk.py` directly

### **Ads Not Playing?**
1. Ensure you have mp4 files in `services/ad_engine/ads/`
2. Check console for "Playing ad:" messages
3. Ads only play when no faces detected (IDLE state)

### **Frontend Not Connecting?**
1. Check kiosk window is open (shows WebSocket ready)
2. Refresh browser (F5)
3. Check browser console (F12) for errors

### **Stop Everything**
Press `Ctrl+C` in each terminal

---

## **Project Structure**

```
adorix_kiosk.py          ← Main kiosk (integrated everything)
START_SIMPLE.bat         ← One-click start (Windows)
START_ADORIX.ps1         ← PowerShell start

services/
  ├─ vision/
  │  └─ detector.py      ← Face detection
  └─ ad_engine/
     ├─ selector.py      ← Ad selection logic
     └─ ads/             ← Video files (.mp4)

frontend/
  └─ src/
     └─ components/
        └─ avatar/       ← Avatar display
```

---

## **Configuration**

### **Enable/Disable Camera Window**
Edit `services/vision/detector.py`:
```python
self.DRAW_DEBUG_WINDOW = True   # Change to False to hide
```

### **Change WebSocket Port**
Edit `adorix_kiosk.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8000)  # Change port here
```

### **Adjust Detection Sensitivity**
Edit `services/vision/detector.py`:
```python
self.DWELL_SECONDS = 3.0        # Seconds before face is "committed"
self.MATCH_DISTANCE = 90        # Face matching threshold
```

---

## **Features**

✅ Real-time face detection with age/gender  
✅ WebSocket communication with frontend  
✅ Ad video playback on idle  
✅ Avatar state management  
✅ User detection counter  
✅ Automatic reconnection  

---

**Need help?** Check console output for error messages! 🚀
