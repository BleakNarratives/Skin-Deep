# Mockup: Artist POV compositor
def composite_artist_pov(hand_cam, scene_cam, hud_data):
    """
    hand_cam: Close-up of working area (webcam on machine)
    scene_cam: Wider view (head-mounted camera)
    hud_data: Telemetry overlay (EMG, depth, etc.)
    """
    # Picture-in-picture: hand view in corner
    h, w = scene_cam.shape[:2]
    hand_resized = cv2.resize(hand_cam, (w//4, h//4))
    
    # Overlay
    composite = scene_cam.copy()
    composite[10:10+h//4, w-w//4-10:w-10] = hand_resized
    
    # Add telemetry HUD
    cv2.putText(composite, f"EMG: {hud_data['emg']:.2f}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(composite, f"Depth: {hud_data['depth']}mm", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 200), 2)
    
    return composite