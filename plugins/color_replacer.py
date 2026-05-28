import numpy as np
from PIL import Image

def colorize_template_2(template_img, new_hex):
    # Convert image to numpy array
    arr = np.array(template_img)

    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]

    # Base turquoise: rgb(6, 225, 204)
    # Base purple: rgb(161, 0, 255)

    # We will identify non-grayscale, non-black pixels and tint them to the new_hex
    # To avoid changing everything, we will look for high saturation pixels (difference between max and min channel > threshold)

    target_hex = new_hex.lstrip('#')
    new_r, new_g, new_b = tuple(int(target_hex[i:i+2], 16) for i in (0, 2, 4))

    max_c = np.max(arr[:,:,:3], axis=2)
    min_c = np.min(arr[:,:,:3], axis=2)
    saturation = max_c - min_c

    # Mask for pixels that are colored (not pure gray/black/white)
    mask = saturation > 30

    arr[:,:,0][mask] = new_r
    arr[:,:,1][mask] = new_g
    arr[:,:,2][mask] = new_b

    return Image.fromarray(arr)
