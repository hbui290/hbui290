import os
import re
import base64
import requests
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance

def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(os.path.dirname(script_dir))
    bg_image_path = os.path.join(repo_dir, ".github", "assets", "focus.png")
    output_svg_path = os.path.join(repo_dir, "profile-activity.svg")

    # 1. Fetch the dynamic graph SVG from Vercel (transparent background)
    url = "https://github-readme-activity-graph.vercel.app/graph?username=hbui290&bg_color=00000000&color=a0a0a0&title_color=007aff&line=007aff&point=ffffff&area_color=053a75&hide_border=true"
    print(f"Fetching SVG from: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to fetch SVG")
        return
    svg_content = response.text

    # 2. Parse SVG dimensions (default to 1200x430 if not found)
    width = 1200
    height = 430
    width_match = re.search(r'width=["\'](\d+)["\']', svg_content)
    height_match = re.search(r'height=["\'](\d+)["\']', svg_content)
    if width_match:
        width = int(width_match.group(1))
    if height_match:
        height = int(height_match.group(1))
    print(f"SVG Dimensions: {width}x{height}")

    # 3. Process the background image
    if not os.path.exists(bg_image_path):
        print(f"Background image not found at {bg_image_path}")
        return

    img = Image.open(bg_image_path)
    # Convert palette/RGBA to RGB for JPEG conversion
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Crop and resize to cover the SVG aspect ratio (center crop)
    img_w, img_h = img.size
    target_aspect = width / height
    current_aspect = img_w / img_h

    if current_aspect > target_aspect:
        # Image is wider than needed
        new_width = int(target_aspect * img_h)
        offset = (img_w - new_width) // 2
        img = img.crop((offset, 0, offset + new_width, img_h))
    else:
        # Image is taller than needed
        new_height = int(img_w / target_aspect)
        offset = (img_h - new_height) // 2
        img = img.crop((0, offset, img_w, offset + new_height))

    img = img.resize((width, height), Image.Resampling.LANCZOS)

    # Apply digital blur and dark overlay
    img = img.filter(ImageFilter.GaussianBlur(radius=5))
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.38) # 38% brightness


    # 4. Save processed image as low-size JPEG in memory and base64-encode
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=75)
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # 5. Embed image into SVG
    # We insert the <image> tag right after the opening <svg> tag
    svg_tag_end = svg_content.find(">") + 1
    if svg_tag_end <= 0:
        print("Invalid SVG format")
        return

    # Image tag that fills the SVG background
    image_tag = (
        f'\n  <image href="data:image/jpeg;base64,{img_str}" '
        f'width="{width}" height="{height}" x="0" y="0" '
        f'preserveAspectRatio="xMidYMid slice" opacity="0.8"/>'
    )

    modified_svg = svg_content[:svg_tag_end] + image_tag + svg_content[svg_tag_end:]

    # Write the modified SVG
    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(modified_svg)
    print(f"Successfully generated custom SVG at {output_svg_path}")

if __name__ == "__main__":
    main()
