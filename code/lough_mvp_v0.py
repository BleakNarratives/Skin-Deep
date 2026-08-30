# [DNA_TAG]
# ORIGIN: Crostini-Chromebook (auto-detected)
# PILLAR: rootbase-engine-room
# DEPS: cv2, mediapipe, numpy, pandas
# ROLE: Component of UNPACKED
# AUTHOR: Auto-tagged by Buffy (DNA Sweeper)
# SESSION: 2026-08-22 ShipWreckD OS Builder
# TIER: Recruit (5)
# AKA: lough_mvp_v0, code-module
# [/DNA_TAG]

# File: lough_mvp_v0.py
"""
LOUGH MVP v0.0.1
- Webcam hand tracking via MediaPipe
- Simulated EMG from hand velocity
- Visual feedback overlay
- Data logging to CSV
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from datetime import datetime

class LoughMVP:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7)
        self.cap = cv2.VideoCapture(0)
        self.data_log = []
        
    def simulate_emg(self, hand_landmarks):
        """Generate pseudo-EMG from hand movement variance"""
        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark])
        velocity = np.std(landmarks, axis=0).mean() * 100  # Fake metric
        emg_signal = np.clip(velocity + np.random.normal(0, 0.1), 0, 1)
        return emg_signal
    
    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
                
            # Process with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Get simulated EMG
                    emg_val = self.simulate_emg(hand_landmarks)
                    
                    # Log data
                    self.data_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'emg_simulated': emg_val,
                        'wrist_x': hand_landmarks.landmark[0].x,
                        'wrist_y': hand_landmarks.landmark[0].y
                    })
                    
                    # Visual feedback
                    cv2.putText(frame, f"EMG: {emg_val:.2f}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Target comparison (hardcoded target position)
                    target_x, target_y = 0.5, 0.5
                    current_x = hand_landmarks.landmark[0].x
                    current_y = hand_landmarks.landmark[0].y
                    error = np.sqrt((current_x - target_x)**2 + (current_y - target_y)**2)
                    
                    if error > 0.1:
                        cv2.putText(frame, "DEVIATION!", (10, 70),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow('LOUGH MVP v0.0.1', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        cv2.destroyAllWindows()
        
        # Save data
        df = pd.DataFrame(self.data_log)
        df.to_csv('lough_mvp_log.csv', index=False)
        print(f"Logged {len(df)} data points.")

if __name__ == "__main__":
    mvp = LoughMVP()
    mvp.run()