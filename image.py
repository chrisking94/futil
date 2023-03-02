# -*- coding: utf-8 -*-
# @Time         : 17:34 2022/8/20
# @Author       : Chris
# @Description  : Computer vision tools.
# Copied from https://towardsdatascience.com/removing-duplicate-or-similar-images-in-python-93d447c1c3eb
import io
from typing import Union
import imagehash
from PIL import Image
import numpy as np
from io import BytesIO
import base64


def to_rgb(image: Image.Image) -> Image.Image:
    """To RGB(3-channel) image."""
    if image.mode == "RGB":
        return image
    canvas = Image.new("RGB", image.size, (0, 0, 0))
    canvas.paste(image, mask=image if image.mode=="RGBA" else None)
    return canvas


def remove_alpha(image: Image.Image) -> Image.Image:
    if image.mode != 'RGBA':
        return image
    canvas = Image.new('RGBA', image.size, (255, 255, 255, 255))
    canvas.paste(image, mask=image)
    return canvas.convert('RGB')


def z_transform(img: Image, hash_size: int) -> Image:
    image = remove_alpha(img)
    image = image.convert("L").resize((hash_size, hash_size), Image.ANTIALIAS)
    data = image.getdata()
    quantiles = np.arange(100)
    quantiles_values = np.percentile(data, quantiles)
    zdata = (np.interp(data, quantiles_values, quantiles) / 100 * 255).astype(np.uint8)
    image.putdata(zdata)
    return image


def to_pil_image(img: Union[str, bytes, Image.Image]) -> Image.Image:
    """Convert input to PIL Image."""
    if isinstance(img, str):
        return Image.open(img)
    elif isinstance(img, bytes):
        return Image.open(io.BytesIO(img))
    elif isinstance(img, dict):
        if "b64" in img:
            return base642image(img["b64"])
    elif isinstance(img, Image.Image):
        return img  # No need to convert.
    raise NotImplemented(f"Unsupported input type '{type(img)}'!")


def get_hash(img) -> str:
    """Get hash string of an image."""
    img = to_pil_image(img)
    img = z_transform(img, 8)
    return str(imagehash.dhash(img))


def image2base64(image: Image.Image):
    buffer = BytesIO()
    if image.mode == "RGBA":
        image.save(buffer, format="PNG")
    else:
        image.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue())


def base642image(data: str):
    buffer = BytesIO(base64.b64decode(data))
    return Image.open(buffer)
