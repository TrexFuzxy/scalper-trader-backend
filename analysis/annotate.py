from PIL import Image, ImageDraw
import os

def annotate_chart(image_path, signal):
    # Dummy: Draw simple lines for entry, SL, TP
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    # Draw lines (dummy positions)
    draw.line([(0, h//2), (w, h//2)], fill="green", width=3)  # Entry
    draw.line([(0, h//2-30), (w, h//2-30)], fill="red", width=3)  # SL
    draw.line([(0, h//2+30), (w, h//2+30)], fill="blue", width=3)  # TP
    annotated_path = image_path.replace(".png", "_annotated.png").replace(".jpg", "_annotated.jpg")
    img.save(annotated_path)
    return annotated_path 