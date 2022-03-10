
from ColorController import ColorController
from fastapi import FastAPI, HTTPException


app = FastAPI()


@app.get("/search/name/{name}")
def read_name(name: str):
    """Search for a color by name, and return a corresponding lists of color values in hex, RGB, and HSV format."""
    color = ColorController(name=name)
    return {"name": color.name, "hex_codes": color.hex_code, "rgb_values": color.rgb, "hsv_values": color.hsv}


@app.get("/search/hex/{hex_code}")
def read_hex(hex_code: str):
    color = ColorController(hex_code=hex_code)
    return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}


@app.get("/search/rgb/{rgb_value}")
def read_rgb(rgb_value: str):
    rgb = tuple([int(num) for num in rgb_value.split(',')])
    color = ColorController(rgb=rgb)
    return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}


@app.get("/search/hsv/{hsv_value}")
def read_hsv(hsv_value: str):
    hsv = tuple([int(num) for num in hsv_value.split(',')])
    if hsv[0] < 0 or hsv[1] < 0 or hsv[0] > 1 or hsv[1] > 1:
        raise HTTPException(status_code=404, detail="HSV values out of range.")
    color = ColorController(hsv=hsv)
    return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}
