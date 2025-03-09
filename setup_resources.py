import os
import urllib.request
import shutil
import ssl

def setup_resources():
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # Ensure static directory exists
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        
    # Create subdirectory for icons if it doesn't exist
    icons_dir = os.path.join(static_dir, 'icons')
    if not os.path.exists(icons_dir):
        os.makedirs(icons_dir)
    
    # Default favicon.ico
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon_path):
        # Generate basic favicon using a placeholder service
        context = ssl._create_unverified_context()
        with urllib.request.urlopen("https://placehold.co/32x32/2196F3/FFF.png", context=context) as response:
            with open(os.path.join(icons_dir, "temp.png"), 'wb') as out_file:
                shutil.copyfileobj(response, out_file)
        # Convert to ico format (requires PIL)
        try:
            from PIL import Image
            img = Image.open(os.path.join(icons_dir, "temp.png"))
            img.save(favicon_path)
            os.remove(os.path.join(icons_dir, "temp.png"))
        except ImportError:
            print("PIL not available, copying PNG instead of creating ICO")
            shutil.copy(os.path.join(icons_dir, "temp.png"), favicon_path)
    
    # Apple touch icons
    sizes = [57, 72, 114, 144, 152, 180]
    for size in sizes:
        icon_name = f"apple-touch-icon{'-' + str(size) + 'x' + str(size) if size != 57 else ''}.png"
        icon_path = os.path.join(static_dir, icon_name)
        if not os.path.exists(icon_path):
            with urllib.request.urlopen(f"https://placehold.co/{size}x{size}/2196F3/FFF.png", context=context) as response:
                with open(icon_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
    
    print("Resource setup complete")

if __name__ == "__main__":
    setup_resources()
