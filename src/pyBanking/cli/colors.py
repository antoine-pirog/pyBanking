import random
import colorsys

def get_random_color():
    return f"rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})"

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(
        int(rgb[0] * 255),
        int(rgb[1] * 255),
        int(rgb[2] * 255),
    )


def randomize_hex_color(base_hex, variation_percent = 20):
    r, g, b = hex_to_rgb(base_hex)

    # Convert to HLS (Hue, Lightness, Saturation)
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    new_h = h * (1 + random.randint(-variation_percent, variation_percent)/100)
    new_l = l * (1 + random.randint(-variation_percent, variation_percent)/100)
    new_s = s * (1 + random.randint(-variation_percent, variation_percent)/100)

    new_h = max(0, min(new_h, 1))
    new_l = max(0, min(new_l, 1))
    new_s = max(0, min(new_s, 1))

    r2, g2, b2 = colorsys.hls_to_rgb(new_h, new_l, new_s)
    return rgb_to_hex((r2, g2, b2))