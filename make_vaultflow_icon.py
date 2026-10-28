import os
from PIL import Image, ImageDraw

def generate_icon_image(size=(256, 256)) -> Image.Image:
    """Generates a clean, minimal geometric vault icon as a PIL Image."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([12, 12, 244, 244], radius=56, fill="#0f172a", outline="#38bdf8", width=6)

    shield_pts = [(128, 44), (204, 76), (204, 150), (128, 214), (52, 150), (52, 76)]
    draw.polygon(shield_pts, fill="#1e293b", outline="#38bdf8", width=6)

    core_pts = [(128, 86), (170, 134), (128, 182), (86, 134)]
    draw.polygon(core_pts, fill="#10b981", outline="#34d399", width=4)

    draw.ellipse([118, 124, 138, 144], fill="#ffffff")
    return img

def ensure_vaultflow_icon(ico_path="vaultflow_icon.ico") -> Image.Image:
    """Loads existing .ico immediately in O(1) if present; only generates if missing."""
    if os.path.exists(ico_path):
        try:
            return Image.open(ico_path)
        except Exception:
            pass

    img = generate_icon_image()
    try:
        img.save(
            ico_path,
            format="ICO",
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )
    except Exception:
        pass
    return img

if __name__ == "__main__":
    ensure_vaultflow_icon("vaultflow_icon.ico")
    print("✔ 'vaultflow_icon.ico' generated successfully!")