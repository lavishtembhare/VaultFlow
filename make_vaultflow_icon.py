from PIL import Image, ImageDraw

def create_vaultflow_icon():
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Dark Rounded App Squircle Background
    draw.rounded_rectangle([12, 12, 244, 244], radius=56, fill="#0f172a", outline="#38bdf8", width=8)

    # 2. Outer Shield Silhouette (Vault / Protection)
    shield_pts = [
        (128, 44),
        (204, 76),
        (204, 150),
        (128, 214),
        (52, 150),
        (52, 76)
    ]
    draw.polygon(shield_pts, fill="#1e293b", outline="#38bdf8", width=8)

    # 3. Inner Finance Accent (Growth Diamond / Vault Core)
    core_pts = [
        (128, 86),
        (170, 134),
        (128, 182),
        (86, 134)
    ]
    draw.polygon(core_pts, fill="#10b981", outline="#34d399", width=4)

    # 4. Center Node Spark
    draw.ellipse([118, 124, 138, 144], fill="#ffffff")

    # Export multi-size Windows icon
    img.save(
        "vaultflow_icon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print("✔ 'vaultflow_icon.ico' generated successfully!")

if __name__ == "__main__":
    create_vaultflow_icon()