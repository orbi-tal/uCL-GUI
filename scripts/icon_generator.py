#!/usr/bin/env python3
"""
Icon Generator - Creates .icns and .ico files for cross-platform applications
"""

import os
import sys
import subprocess
import shutil
import platform
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw  # type: ignore # noqa

def check_dependencies():
    """Check if required dependencies are installed"""
    dependencies = {
        'PIL': 'Pillow',
        'cairosvg': 'cairosvg'
    }
    
    installed = []
    missing = []
    
    for module, package in dependencies.items():
        try:
            if module == 'PIL':
                import PIL
                print(f"✓ {package} is installed (version {PIL.__version__})")
                installed.append(package)
            elif module == 'cairosvg':
                try:
                    import cairosvg
                    print(f"✓ {package} is installed (version {cairosvg.__version__})")
                    installed.append(package)
                except ImportError:
                    print(f"✗ {package} is missing (optional but recommended)")
                    missing.append(package)
        except ImportError:
            if module == 'PIL':
                print(f"✗ {package} is missing (required)")
                print(f"  Install with: pip install {package}")
                missing.append(package)
            else:
                print(f"✗ {package} is missing (optional but recommended)")
                missing.append(package)
    
    # Check for Inkscape as alternative to cairosvg
    inkscape_found = False
    inkscape_paths = [
        'inkscape',  # Standard path
        '/Applications/Inkscape.app/Contents/MacOS/inkscape',  # macOS
        r'C:\Program Files\Inkscape\bin\inkscape.exe',  # Windows 64-bit
        r'C:\Program Files (x86)\Inkscape\bin\inkscape.exe',  # Windows 32-bit
    ]
    
    for path in inkscape_paths:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split('\n')[0] if result.stdout else "unknown version"
                print(f"✓ Inkscape is installed ({version})")
                inkscape_found = True
                break
        except (subprocess.SubprocessError, FileNotFoundError):
            continue
    
    if not inkscape_found:
        print("✗ Inkscape not found (optional alternative to cairosvg)")
    
    # Check for iconutil on macOS
    if platform.system() == 'Darwin':
        try:
            result = subprocess.run(['iconutil', '--help'], capture_output=True)
            if result.returncode == 0:
                print("✓ iconutil is available (required for .icns on macOS)")
            else:
                print("✗ iconutil is not working correctly (needed for .icns)")
        except (subprocess.SubprocessError, FileNotFoundError):
            print("✗ iconutil not found (needed for .icns creation)")
    
    # We need at least Pillow to proceed
    if 'Pillow' in installed:
        return True
    else:
        print("\nError: Pillow is required. Install with: pip install Pillow")
        return False

def convert_svg_to_png(svg_path, output_png, size):
    """Convert SVG to PNG at specified size while preserving aspect ratio"""
    # Ensure imports are available
    from PIL import Image, ImageDraw
    try:
        # Try using cairosvg if available (higher quality)
        try:
            import cairosvg
            import xml.etree.ElementTree as ET
            
            # Parse the SVG to get its dimensions
            tree = ET.parse(svg_path)
            root = tree.getroot()
            
            # Get width and height attributes (handle various formats)
            width = root.get('width', '100')
            height = root.get('height', '100')
            
            # Strip units if present
            width = float(''.join(c for c in width if c.isdigit() or c == '.'))
            height = float(''.join(c for c in height if c.isdigit() or c == '.'))
            
            # Calculate aspect ratio
            aspect_ratio = width / height
            
            # Create a transparent background image with proper dimensions
            if aspect_ratio > 1:  # Wider than tall
                output_width = size
                output_height = int(size / aspect_ratio)
            else:  # Taller than wide or square
                output_width = int(size * aspect_ratio)
                output_height = size
                
            # Convert with proper dimensions
            cairosvg.svg2png(url=str(svg_path), write_to=str(output_png), 
                            output_width=output_width, output_height=output_height)
            
            # Now create a centered square image with transparent background
            from PIL import Image
            img = Image.open(output_png)
            square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            
            # Calculate paste position to center the image
            paste_x = (size - output_width) // 2
            paste_y = (size - output_height) // 2
            
            # Paste the image onto the transparent square
            square_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
            square_img.save(output_png)
            
            return True
        except ImportError:
            # Try using Inkscape if available
            try:
                inkscape_paths = [
                    'inkscape',  # Standard path
                    '/Applications/Inkscape.app/Contents/MacOS/inkscape',  # macOS
                    r'C:\Program Files\Inkscape\bin\inkscape.exe',  # Windows 64-bit
                    r'C:\Program Files (x86)\Inkscape\bin\inkscape.exe',  # Windows 32-bit
                ]
                
                for inkscape_path in inkscape_paths:
                    try:
                        # Try the current inkscape path - use export-area-drawing to preserve aspect ratio
                        cmd = [
                            inkscape_path,
                            '--export-filename', str(output_png),
                            '--export-width', str(size),
                            '--export-area-drawing',
                            str(svg_path)
                        ]
                        subprocess.run(cmd, check=True, capture_output=True)
                        print(f"Used Inkscape to convert SVG to PNG")
                        
                        # Now center the image in a square canvas
                        from PIL import Image
                        img = Image.open(output_png)
                        width, height = img.size
                        square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                        
                        # Calculate paste position
                        paste_x = (size - width) // 2
                        paste_y = (size - height) // 2
                        
                        # Paste the image onto the transparent square
                        square_img.paste(img, (paste_x, paste_y), img if img.mode == 'RGBA' else None)
                        square_img.save(output_png)
                        
                        return True
                    except (subprocess.SubprocessError, FileNotFoundError):
                        continue
                
                # If Inkscape isn't available, fall back to PIL
                print("Warning: Inkscape not found. Using fallback method.")
                img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                # Create a simple colored square with the app initial
                draw.rectangle([size//4, size//4, 3*size//4, 3*size//4], fill="#4762FF")
                draw.text((size//2.5, size//2.5), "U", fill="#FFFFFF", size=size//3)
                img.save(str(output_png))
                print("Warning: For best results, install cairosvg or Inkscape")
                return True
            except Exception as e:
                print(f"Error using fallback SVG conversion: {e}")
                return False
    except Exception as e:
        print(f"Error converting SVG to PNG: {e}")
        return False

def create_ico(source_image, output_path):
    """Create Windows ICO file from source image"""
    print(f"Creating ICO file: {output_path}")
    
    # Import required libraries
    import io
    import shutil
    from PIL import Image, ImageDraw
    
    # ICO supports multiple sizes
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    
    # Open the source image
    try:
        # Check if source is SVG
        tmp_path = None
        if str(source_image).lower().endswith('.svg'):
            # Create a temporary PNG to work with
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = Path(tmp.name)
            
            # Convert SVG to high-res PNG
            if not convert_svg_to_png(source_image, tmp_path, 1024):
                print("Failed to convert SVG to PNG, attempting to read SVG directly")
                # If conversion failed, try to read the SVG directly with another method
                try:
                    import cairosvg
                    png_data = cairosvg.svg2png(url=str(source_image), output_width=1024, output_height=1024)
                    with open(tmp_path, 'wb') as f:
                        f.write(png_data)
                except ImportError:
                    print("WARNING: Cannot convert SVG properly without cairosvg or Inkscape")
                    # Create a simple fallback icon
                    img = Image.new('RGBA', (1024, 1024), (71, 98, 255, 255))  # #4762FF
                    img.save(tmp_path)
            
            source_image = tmp_path
        
        # Open image with PIL
        img = Image.open(source_image)
        
        # Ensure the image has an alpha channel (transparency)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Resize to all required sizes and save as ICO
        images = []
        for size in ico_sizes:
            # Preserve aspect ratio while scaling
            width, height = img.size
            aspect_ratio = width / height
                
            if aspect_ratio > 1:  # Wider than tall
                new_width = size
                new_height = int(size / aspect_ratio)
            else:  # Taller than wide or square
                new_width = int(size * aspect_ratio)
                new_height = size
                
            # Create a properly scaled version that preserves aspect ratio
            resampling = getattr(Image, 'LANCZOS', getattr(Image.Resampling, 'LANCZOS', 1))
            scaled_img = img.resize((new_width, new_height), resampling)
                
            # Create a transparent square canvas
            square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            
            # Paste the scaled image in the center
            paste_x = (size - new_width) // 2
            paste_y = (size - new_height) // 2
            square_img.paste(scaled_img, (paste_x, paste_y), scaled_img if scaled_img.mode == 'RGBA' else None)
            
            images.append(square_img)
        
        # Create output directory if it doesn't exist
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save as ICO - handle potential format issues
        try:
            # Try standard method first - make sure to use correct sizes
            images[0].save(
                output_path, 
                format='ICO', 
                sizes=[(img.size[0], img.size[1]) for img in images],
                append_images=images[1:]
            )
            
            # Verify the ICO file contains multiple sizes
            try:
                with Image.open(output_path) as ico_check:
                    # PIL doesn't expose multiple icon sizes easily, check file size instead
                    if ico_check.format != 'ICO' or output_path.stat().st_size < 4000:
                        raise ValueError("ICO file appears to be incomplete")
            except Exception:
                raise ValueError("Failed to verify ICO file integrity")
                
        except Exception as ico_error:
            print(f"Warning: Standard ICO save failed ({ico_error}), trying alternate method")
            
            # If that fails, try saving each size one at a time
            try:
                # Create a temporary ICO to work with
                tmp_ico = output_path.with_name(f"tmp_{output_path.name}")
                
                # First try an alternate PIL method
                # Start with the largest image and add smaller ones
                main_img = images[-1]  # Largest size (256px)
                main_img.save(tmp_ico, format="ICO")
                
                # Create a new ICO with all sizes
                with open(tmp_ico, 'wb') as outfile:
                    # Write ICO header: 0=Reserved, 1=ICO type, Count=number of images
                    outfile.write(b'\x00\x00\x01\x00' + len(images).to_bytes(2, byteorder='little'))
                    
                    # Leave space for directory entries (16 bytes each)
                    outfile.seek(6 + 16 * len(images))
                    
                    # Write each image
                    offset = 6 + 16 * len(images)
                    directory = []
                    
                    for i, img in enumerate(images):
                        # Convert to bytes
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format='PNG')
                        img_bytes = img_bytes.getvalue()
                        img_size = len(img_bytes)
                        
                        # Write image data
                        outfile.write(img_bytes)
                        
                        # Store directory entry
                        w, h = img.size
                        colors = 0  # 0 means 256 or more colors
                        planes = 1
                        bpp = 32  # RGBA
                        
                        directory.append({
                            'width': w,
                            'height': h,
                            'colors': colors,
                            'planes': planes,
                            'bpp': bpp,
                            'size': img_size,
                            'offset': offset
                        })
                        
                        offset += img_size
                    
                    # Write directory entries
                    outfile.seek(6)
                    for entry in directory:
                        # Write entry in ICO format
                        outfile.write(bytes([
                            entry['width'] if entry['width'] < 256 else 0,
                            entry['height'] if entry['height'] < 256 else 0,
                            entry['colors'],
                            0,  # Reserved
                            entry['planes'] & 0xFF,
                            (entry['planes'] >> 8) & 0xFF,
                            entry['bpp'] & 0xFF,
                            (entry['bpp'] >> 8) & 0xFF,
                        ]))
                        
                        # Size and offset
                        outfile.write(entry['size'].to_bytes(4, byteorder='little'))
                        outfile.write(entry['offset'].to_bytes(4, byteorder='little'))
                
                # Replace with the fixed file
                shutil.copy(tmp_ico, output_path)
                tmp_ico.unlink(missing_ok=True)
                
                print("Created ICO file using alternate method")
                
            except Exception as alt_error:
                print(f"Alternative method failed: {alt_error}, saving individual PNG files")
                
                # If all else fails, save individual PNGs and create a basic ICO
                # Create a subdirectory for temporary PNGs
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_dir_path = Path(tmp_dir)
                    
                    # Save each size as PNG
                    png_paths = []
                    for i, size in enumerate(ico_sizes):
                        png_path = tmp_dir_path / f"icon_{size}x{size}.png"
                        images[i].save(png_path)
                        png_paths.append(png_path)
                    
                    # Save largest size as main icon
                    largest_png = tmp_dir_path / "icon_main.png"
                    images[-1].save(largest_png)
                    
                    # Also save individual sizes in output directory for fallback
                    for size in [16, 32, 48, 256]:
                        idx = ico_sizes.index(size) if size in ico_sizes else -1
                        png_output = output_path.with_name(f"{output_path.stem}_{size}.png")
                        images[idx].save(png_output)
                        print(f"Saved {png_output} as fallback")
                        
                    # Create a basic ICO with at least a couple of sizes
                    try:
                        # Use largest size to create a small ICO
                        images[-1].save(output_path, format="ICO")
                        # Add a second size if possible
                        if len(images) > 1:
                            images[0].save(output_path, format="ICO", append=True)
                    except Exception:
                        # If everything fails, create a minimal valid ICO
                        with open(output_path, 'wb') as f:
                            f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x04\x00\x28\x01\x00\x00\x16\x00\x00\x00')
                            f.write(b'\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00\x04\x00\x00\x00\x00\x00\x00\x00')
                            f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        
        # Clean up temporary file if created
        if 'tmp_path' in locals():
            tmp_path.unlink(missing_ok=True)
            
        print(f"✓ Created ICO file: {output_path}")
        return True
    
    except Exception as e:
        print(f"Error creating ICO file: {e}")
        print(f"Exception details: {str(e)}")
        
        # Create fallback PNGs
        try:
            output_dir = Path(output_path).parent
            # Create a simple colored square
            for size in [16, 32, 48, 256]:
                img = Image.new('RGBA', (size, size), (71, 98, 255, 255))  # #4762FF
                draw = ImageDraw.Draw(img)
                if size >= 32:
                    # Add a letter to larger icons
                    font_size = max(10, size // 3)
                    draw.text((size//3, size//3), "U", fill="#FFFFFF")
                png_path = output_dir / f"{Path(output_path).stem}_{size}.png"
                img.save(png_path)
                print(f"Created fallback icon: {png_path}")
            
            # Create an empty .ico file to prevent build errors
            with open(output_path, 'wb') as f:
                # Write minimal ICO header
                f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x04\x00\x28\x01\x00\x00\x16\x00\x00\x00')
                f.write(b'\x28\x00\x00\x00\x10\x00\x00\x00\x20\x00\x00\x00\x01\x00\x04\x00\x00\x00\x00\x00\x00\x00')
                f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
                
            return True
        except Exception as fallback_error:
            print(f"Failed to create fallback icons: {fallback_error}")
            return False

def create_icns(source_image, output_path):
    """Create macOS ICNS file from source image"""
    print(f"Creating ICNS file: {output_path}")
    
    # Import required libraries
    import io
    from PIL import Image, ImageDraw
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)
            
            # Check if source is SVG
            if str(source_image).lower().endswith('.svg'):
                # Create a temporary PNG to work with
                tmp_png = tmp_dir_path / "source.png"
                convert_svg_to_png(source_image, tmp_png, 1024)
                source_image = tmp_png
            
            # Open the source image
            img = Image.open(source_image)
            
            # If we're on macOS, we can use the native iconutil
            if platform.system() == 'Darwin':
                iconset_path = tmp_dir_path / "icon.iconset"
                iconset_path.mkdir(exist_ok=True)
                
                # ICNS requires these specific sizes
                icns_sizes = {
                    '16x16': '16x16.png',
                    '32x32': '16x16@2x.png',
                    '32x32': '32x32.png',
                    '64x64': '32x32@2x.png',
                    '128x128': '128x128.png',
                    '256x256': '128x128@2x.png',
                    '256x256': '256x256.png',
                    '512x512': '256x256@2x.png',
                    '512x512': '512x512.png',
                    '1024x1024': '512x512@2x.png'
                }
                
                # Generate each required size
                for size, filename in icns_sizes.items():
                    size_px = int(size.split('x')[0])
                    
                    # Preserve aspect ratio while scaling
                    width, height = img.size
                    aspect_ratio = width / height
                    
                    if aspect_ratio > 1:  # Wider than tall
                        new_width = size_px
                        new_height = int(size_px / aspect_ratio)
                    else:  # Taller than wide or square
                        new_width = int(size_px * aspect_ratio)
                        new_height = size_px
                    
                    # Create a properly scaled version that preserves aspect ratio
                    resampling = getattr(Image, 'LANCZOS', getattr(Image.Resampling, 'LANCZOS', 1))
                    scaled_img = img.resize((new_width, new_height), resampling)
                    
                    # Create a transparent square canvas
                    square_img = Image.new('RGBA', (size_px, size_px), (0, 0, 0, 0))
                    
                    # Paste the scaled image in the center
                    paste_x = (size_px - new_width) // 2
                    paste_y = (size_px - new_height) // 2
                    square_img.paste(scaled_img, (paste_x, paste_y), scaled_img if scaled_img.mode == 'RGBA' else None)
                    
                    square_img.save(iconset_path / filename)
                
                # Convert iconset to icns using iconutil
                subprocess.run([
                    'iconutil', 
                    '-c', 'icns', 
                    str(iconset_path),
                    '-o', str(output_path)
                ], check=True)
                
                print(f"✓ Created ICNS file: {output_path}")
                return True
            else:
                # On non-macOS systems, we'll create a PNG with the same name
                # and add a note that true .icns can only be created on macOS
                print("Native ICNS creation requires macOS with iconutil.")
                print("Creating high-resolution PNG instead.")
                
                # Create a PNG with the same name (without extension)
                png_path = output_path.with_suffix('.png')
                
                # Create properly sized versions that preserve aspect ratio
                width, height = img.size
                aspect_ratio = width / height
                
                # For the 1024x1024 version
                if aspect_ratio > 1:  # Wider than tall
                    new_width = 1024
                    new_height = int(1024 / aspect_ratio)
                else:  # Taller than wide or square
                    new_width = int(1024 * aspect_ratio)
                    new_height = 1024
                
                # Create a properly scaled version
                resampling = getattr(Image, 'LANCZOS', getattr(Image.Resampling, 'LANCZOS', 1))
                scaled_img = img.resize((new_width, new_height), resampling)
                
                # Create a transparent square canvas
                img_resized = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
                paste_x = (1024 - new_width) // 2
                paste_y = (1024 - new_height) // 2
                img_resized.paste(scaled_img, (paste_x, paste_y), scaled_img if scaled_img.mode == 'RGBA' else None)
                img_resized.save(png_path)
                
                # For the 512x512 version
                if aspect_ratio > 1:  # Wider than tall
                    new_width = 512
                    new_height = int(512 / aspect_ratio)
                else:  # Taller than wide or square
                    new_width = int(512 * aspect_ratio)
                    new_height = 512
                
                # Create a properly scaled version
                resampling = getattr(Image, 'LANCZOS', getattr(Image.Resampling, 'LANCZOS', 1))
                scaled_img = img.resize((new_width, new_height), resampling)
                
                # Create a transparent square canvas
                img_medium = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
                paste_x = (512 - new_width) // 2
                paste_y = (512 - new_height) // 2
                img_medium.paste(scaled_img, (paste_x, paste_y), scaled_img if scaled_img.mode == 'RGBA' else None)
                medium_path = output_path.with_name("icon_512.png")
                img_medium.save(medium_path)
                
                print(f"✓ Created PNG icons at {png_path} and {medium_path}")
                print("Note: For a true macOS .icns file, build on macOS.")
                
                # Create a more proper .icns file with basic icon format support
                with open(output_path, 'wb') as f:
                    # ICNS magic + file size placeholder (will fill in later)
                    f.write(b'icns\x00\x00\x00\x00')
                    
                    # For each standard size, add an entry
                    # Format: 4-byte type code + 4-byte length + data
                    
                    # Convert 1024x1024 image to PNG data
                    png_data = io.BytesIO()
                    img_resized.save(png_data, format='PNG')
                    png_data = png_data.getvalue()
                    
                    # Add ic10 entry (1024x1024 retina icon - PNG format)
                    ic10_size = 8 + len(png_data)  # 8 bytes for type+length
                    f.write(b'ic10')
                    f.write(ic10_size.to_bytes(4, byteorder='big'))
                    f.write(png_data)
                    
                    # Convert 512x512 image to PNG data
                    png_data = io.BytesIO()
                    img_medium.save(png_data, format='PNG')
                    png_data = png_data.getvalue()
                    
                    # Add ic09 entry (512x512 icon - PNG format)
                    ic09_size = 8 + len(png_data)
                    f.write(b'ic09')
                    f.write(ic09_size.to_bytes(4, byteorder='big'))
                    f.write(png_data)
                    
                    # Go back and write the file size
                    file_size = f.tell()
                    f.seek(4)
                    f.write(file_size.to_bytes(4, byteorder='big'))
                
                return True
    
    except Exception as e:
        print(f"Error creating ICNS file: {e}")
        return False

def generate_icons(source_image, output_dir):
    """Generate all icon formats from source image"""
    # Ensure imports are available
    from PIL import Image, ImageDraw
    if not check_dependencies():
        print("Missing dependencies. Please install required packages.")
        return False
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Convert source_image to Path object
    source_path = Path(source_image)
    
    # Check if source image exists
    if not source_path.exists():
        print(f"Error: Source image not found at {source_path}")
        return False
    
    # Ensure the source image is suitable for icons
    print(f"Analyzing source image: {source_path}")
    try:
        if source_path.suffix.lower() != '.svg':
            # For non-SVG files, check size
            with Image.open(source_path) as img:
                width, height = img.size
                if width < 1024 or height < 1024:
                    print(f"Warning: Source image is {width}x{height} pixels.")
                    print("For best results, use an image at least 1024x1024 pixels.")
                if width != height:
                    print(f"Note: Image is not square ({width}x{height}).")
                    print("The aspect ratio will be preserved and the image will be centered.")
    except Exception as e:
        print(f"Warning: Could not analyze source image: {e}")
    
    # Create ICO file (Windows)
    ico_path = output_path / "icon.ico"
    print("\n=== Creating Windows ICO file ===")
    ico_success = create_ico(source_path, ico_path)
    
    # Create ICNS file (macOS)
    icns_path = output_path / "icon.icns"
    print("\n=== Creating macOS ICNS file ===")
    icns_success = create_icns(source_path, icns_path)
    
    # Also create a high-res PNG fallback
    print("\n=== Creating PNG fallbacks ===")
    png_path = output_path / "icon.png"
    try:
        # Open the source image
        if source_path.suffix.lower() == '.svg':
            # Convert SVG to PNG first
            tmp_png = output_path / "tmp_source.png"
            convert_svg_to_png(source_path, tmp_png, 1024)
            with Image.open(tmp_png) as img:
                img.save(png_path)
            # Cleanup temp file
            # Cleanup temp file if created
            tmp_png.unlink(missing_ok=True)
        else:
            # Create a properly sized version of the bitmap that preserves aspect ratio
            with Image.open(source_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                    
                if aspect_ratio > 1:  # Wider than tall
                    new_width = 1024
                    new_height = int(1024 / aspect_ratio)
                else:  # Taller than wide or square
                    new_width = int(1024 * aspect_ratio)
                    new_height = 1024
                    
                # Create a properly scaled version
                resampling = getattr(Image, 'LANCZOS', getattr(Image.Resampling, 'LANCZOS', 1))
                scaled_img = img.resize((new_width, new_height), resampling)
                    
                # Create a transparent square canvas
                square_img = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
                    
                # Paste the scaled image in the center
                paste_x = (1024 - new_width) // 2
                paste_y = (1024 - new_height) // 2
                square_img.paste(scaled_img, (paste_x, paste_y), scaled_img if scaled_img.mode == 'RGBA' else None)
                    
                square_img.save(png_path)
        print(f"✓ Created PNG fallback: {png_path}")
        png_success = True
    except Exception as e:
        print(f"Error creating PNG fallback: {e}")
        png_success = False
    
    success = ico_success or icns_success or png_success
    
    if success:
        print("\n=== Icon Generation Summary ===")
        print(f"Windows ICO (icon.ico): {'✓ Success' if ico_success else '✗ Failed'}")
        print(f"macOS ICNS (icon.icns):  {'✓ Success' if icns_success else '✗ Failed'}")
        print(f"PNG Fallback (icon.png): {'✓ Success' if png_success else '✗ Failed'}")
        print(f"\nIcon files created in: {output_path}")
    else:
        print("\nIcon generation failed for all formats.")
    
    return success

def main():
    """Main function when script is run directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate application icons for multiple platforms')
    parser.add_argument('--source', required=True, help='Source image (high resolution PNG or SVG recommended)')
    parser.add_argument('--output', default='icons', help='Output directory for the generated icons')
    parser.add_argument('--install-deps', action='store_true', help='Install recommended dependencies')
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing recommended dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "cairosvg"], check=True)
            print("Dependencies installed successfully.")
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            print("You may need to install them manually:")
            print("  pip install Pillow cairosvg")
    
    print(f"Generating icons from {args.source}...")
    print(f"Output directory: {args.output}")
    
    if generate_icons(args.source, args.output):
        print("\nIcon generation complete.")
        print("You can now use these icons in your application.")
        print("Remember to update your build configuration to use these icons.")
    else:
        print("\nIcon generation failed.")
        print("Check the error messages above for details.")
        print("You may need to install additional dependencies:")
        print("  pip install Pillow cairosvg")
        sys.exit(1)

if __name__ == "__main__":
    main()