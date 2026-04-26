def render_skin_cross_section(needle_depth, ink_deposition, trauma_zones):
    """
    Creates a medical-illustration style view of skin layers
    """
    # Create blank canvas
    h, w = 400, 600
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Draw skin layers (simplified)
    # Epidermis
    cv2.rectangle(img, (0, 100), (w, 150), (255, 240, 220), -1)
    cv2.putText(img, "Epidermis", (10, 130), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    # Dermis
    cv2.rectangle(img, (0, 150), (w, 300), (255, 220, 200), -1)
    cv2.putText(img, "Dermis", (10, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    # Subcutaneous
    cv2.rectangle(img, (0, 300), (w, h), (255, 200, 180), -1)
    cv2.putText(img, "Subcutaneous", (10, 350),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    
    # Draw needle
    needle_x = w // 2
    cv2.line(img, (needle_x, 50), (needle_x, 100 + needle_depth), 
             (100, 100, 100), 3)
    
    # Draw ink deposition as particles
    ink_y = 100 + needle_depth
    cv2.circle(img, (needle_x, ink_y), 8, (0, 0, 0), -1)
    
    # Trauma zone (heat map)
    if trauma_zones:
        for zone in trauma_zones:
            center = (zone['x'], zone['y'])
            radius = zone['radius']
            # Red intensity based on trauma level
            intensity = min(255, zone['trauma'] * 50)
            cv2.circle(img, center, radius, (0, 0, intensity), -1)
    
    return img