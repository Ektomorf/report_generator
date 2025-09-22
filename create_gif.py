#!/usr/bin/env python3
"""
GIF Creator from PNG Images

This script creates an animated GIF from PNG images in a specified folder.
The images are sorted alphabetically and combined into a single GIF file.

Usage:
    python create_gif.py [folder_path] [output_path] [duration] [loop]

Arguments:
    folder_path: Path to folder containing PNG images (default: current directory)
    output_path: Output GIF file path (default: output.gif)
    duration: Duration per frame in milliseconds (default: 500)
    loop: Number of loops (0 for infinite, default: 0)
"""

import os
import sys
import glob
import argparse
from PIL import Image
import re


def natural_sort_key(text):
    """
    Sort key function for natural sorting (handles numbers properly).
    For example: img1.png, img2.png, img10.png will be sorted correctly.
    """
    return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', text)]


def create_gif_from_pngs(folder_path, output_path, duration=500, loop=0):
    """
    Create a GIF from PNG images in a folder.
    
    Args:
        folder_path (str): Path to the folder containing PNG images
        output_path (str): Path for the output GIF file
        duration (int): Duration of each frame in milliseconds
        loop (int): Number of loops (0 for infinite loop)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Find all PNG files in the folder
        png_pattern = os.path.join(folder_path, "*.png")
        png_files = glob.glob(png_pattern)
        
        if not png_files:
            print(f"No PNG files found in {folder_path}")
            return False
        
        # Sort files naturally (handles numbers correctly)
        png_files.sort(key=natural_sort_key)
        
        print(f"Found {len(png_files)} PNG files:")
        for i, file in enumerate(png_files, 1):
            print(f"  {i:2d}. {os.path.basename(file)}")
        
        # Load images
        images = []
        for png_file in png_files:
            try:
                img = Image.open(png_file)
                # Convert to RGB if necessary (GIF doesn't support RGBA)
                if img.mode in ('RGBA', 'LA'):
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    else:
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                images.append(img)
                print(f"Loaded: {os.path.basename(png_file)} ({img.size[0]}x{img.size[1]})")
                
            except Exception as e:
                print(f"Error loading {png_file}: {e}")
                continue
        
        if not images:
            print("No valid images could be loaded")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
        # Save as GIF
        print(f"\nCreating GIF...")
        print(f"Output: {output_path}")
        print(f"Duration per frame: {duration}ms")
        print(f"Loop count: {'infinite' if loop == 0 else loop}")
        
        images[0].save(
            output_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=loop,
            optimize=True
        )
        
        # Get file size
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\nGIF created successfully!")
        print(f"File size: {file_size_mb:.2f} MB")
        print(f"Frames: {len(images)}")
        
        return True
        
    except Exception as e:
        print(f"Error creating GIF: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create an animated GIF from PNG images in a folder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python create_gif.py
  python create_gif.py ./images output.gif
  python create_gif.py ./images animated.gif 1000
  python create_gif.py ./images slow_animation.gif 2000 1
        """
    )
    
    parser.add_argument(
        'folder_path',
        nargs='?',
        default='.',
        help='Path to folder containing PNG images (default: current directory)'
    )
    
    parser.add_argument(
        'output_path',
        nargs='?',
        default='output.gif',
        help='Output GIF file path (default: output.gif)'
    )
    
    parser.add_argument(
        'duration',
        nargs='?',
        type=int,
        default=50,
        help='Duration per frame in milliseconds (default: 500)'
    )
    
    parser.add_argument(
        'loop',
        nargs='?',
        type=int,
        default=0,
        help='Number of loops, 0 for infinite (default: 0)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='GIF Creator 1.0'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.folder_path):
        print(f"Error: Folder '{args.folder_path}' does not exist")
        sys.exit(1)
    
    if not os.path.isdir(args.folder_path):
        print(f"Error: '{args.folder_path}' is not a directory")
        sys.exit(1)
    
    if args.duration < 1:
        print("Error: Duration must be at least 1 millisecond")
        sys.exit(1)
    
    if args.loop < 0:
        print("Error: Loop count cannot be negative")
        sys.exit(1)
    
    # Ensure output has .gif extension
    if not args.output_path.lower().endswith('.gif'):
        args.output_path += '.gif'
    
    print("=" * 60)
    print("GIF Creator from PNG Images")
    print("=" * 60)
    print(f"Source folder: {os.path.abspath(args.folder_path)}")
    print(f"Output file: {os.path.abspath(args.output_path)}")
    print("=" * 60)
    
    # Create the GIF
    success = create_gif_from_pngs(
        args.folder_path,
        args.output_path,
        args.duration,
        args.loop
    )
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: GIF created successfully!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("ERROR: Failed to create GIF")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()