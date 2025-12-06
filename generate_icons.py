#!/usr/bin/env python3
"""
Generate icon files for the print server
Creates .ico (Windows) and .icns (macOS) from a base image
"""

from PIL import Image, ImageDraw
import os

def create_printer_icon(size=256):
    """Create a printer icon"""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    printer_color = (66, 126, 234)  # Blue
    paper_color = (255, 255, 255)   # White
    shadow_color = (50, 50, 50)     # Dark gray
    
    # Scale factors
    s = size / 256
    
    # Draw printer body (top part)
    draw.rounded_rectangle(
        [40*s, 60*s, 216*s, 120*s],
        radius=10*s,
        fill=printer_color
    )
    
    # Draw paper slot
    draw.rectangle(
        [70*s, 90*s, 186*s, 110*s],
        fill=paper_color
    )
    
    # Draw printer tray (bottom part)
    draw.rounded_rectangle(
        [60*s, 120*s, 196*s, 180*s],
        radius=8*s,
        fill=printer_color
    )
    
    # Draw paper coming out
    draw.rectangle(
        [80*s, 160*s, 176*s, 200*s],
        fill=paper_color,
        outline=shadow_color,
        width=int(2*s)
    )
    
    # Draw indicator lights
    for i, color in enumerate([(0, 255, 0), (255, 165, 0)]):
        draw.ellipse(
            [170*s + i*25*s, 75*s, 185*s + i*25*s, 90*s],
            fill=color
        )
    
    return img

def save_windows_icon(img, filepath):
    """Save as Windows .ico file"""
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    icons = []
    for size in sizes:
        icons.append(img.resize(size, Image.Resampling.LANCZOS))
    
    icons[0].save(filepath, format='ICO', sizes=[(s[0], s[1]) for s in sizes])
    print(f"Created Windows icon: {filepath}")

def save_macos_icon(img, iconset_path):
    """Save as macOS .icns file"""
    sizes = [
        (16, 'icon_16x16.png'),
        (32, 'icon_16x16@2x.png'),
        (32, 'icon_32x32.png'),
        (64, 'icon_32x32@2x.png'),
        (128, 'icon_128x128.png'),
        (256, 'icon_128x128@2x.png'),
        (256, 'icon_256x256.png'),
        (512, 'icon_256x256@2x.png'),
        (512, 'icon_512x512.png'),
        (1024, 'icon_512x512@2x.png'),
    ]
    
    # Create iconset directory
    os.makedirs(iconset_path, exist_ok=True)
    
    # Generate all required sizes
    for size, filename in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_path, filename))
    
    print(f"Created macOS iconset: {iconset_path}")
    print("To convert to .icns, run:")
    print(f"  iconutil -c icns {iconset_path}")

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Generate icon
    print("Generating print server icon...")
    icon = create_printer_icon(256)
    
    # Save Windows icon
    ico_path = os.path.join(static_dir, 'icon.ico')
    save_windows_icon(icon, ico_path)
    
    # Save macOS iconset
    iconset_path = os.path.join(static_dir, 'icon.iconset')
    save_macos_icon(icon, iconset_path)
    
    # Also save a PNG for reference
    png_path = os.path.join(static_dir, 'icon.png')
    icon.save(png_path)
    print(f"Created PNG icon: {png_path}")
    
    print("\nIcon generation complete!")
    print("\nFor macOS, run this command to create .icns:")
    print(f"  iconutil -c icns {iconset_path}")
