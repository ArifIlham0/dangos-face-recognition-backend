from PIL import Image
from io import BytesIO

def crop_center_square(image_file):
    img = Image.open(image_file)
    width, height = img.size

    if width > height:
        img = img.rotate(-90, expand=True)
        width, height = img.size

    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img_cropped = img.crop((left, top, right, bottom))
    
    if img_cropped.mode in ("RGBA", "LA"):
        img_cropped = img_cropped.convert("RGB")

    cropped_io = BytesIO()
    img_cropped.save(cropped_io, format='JPEG')
    cropped_io.seek(0)
    return cropped_io.getvalue()