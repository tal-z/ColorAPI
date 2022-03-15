from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from tortoise.contrib.fastapi import register_tortoise
from passlib.hash import bcrypt
import jwt

from ColorController import ColorController

from models import User, User_Pydantic, UserIn_Pydantic, Color
from kmeans import extract_colors

JWT_SECRET = 'mysecret'

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

register_tortoise(
    app,
    db_url='sqlite://db.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True,
)


async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)
    if not user:
        return False
    if not user.verify_password(password):
        return False
    return user


@app.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        return {'error': 'invalid credentials'}
    user_obj = await User_Pydantic.from_tortoise_orm(user)
    token = jwt.encode({'id': user_obj.id}, JWT_SECRET)
    return {'access_token': token, 'token_type': 'bearer'}


@app.post('/users', response_model=User_Pydantic)
async def create_user(user: UserIn_Pydantic):
    user_obj = User(username=user.username, password_hash=bcrypt.hash(user.password_hash))
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    return await User_Pydantic.from_tortoise_orm(user)

@app.get('/users/me', response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    return user


@app.get('/')
async def index(token: str = Depends(oauth2_scheme)):
    return {'the_token': token}


@app.get("/search/name/{name}")
async def read_name(name: str):
    """Search for a color by name, and return a corresponding lists of color values in hex, RGB, and HSV format."""
    color = ColorController(name=name)
    return {"name": color.name, "hex_codes": color.hex_code, "rgb_values": color.rgb, "hsv_values": color.hsv}


@app.get("/search/hex/{hex_code}")
async def read_hex(hex_code: str):
    try:
        color = ColorController(hex_code=hex_code)
        return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}
        return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}
    except ValueError:
        raise HTTPException(status_code=404, detail="Value Error")


@app.get("/search/rgb/{rgb_value}")
async def read_rgb(rgb_value: str):
    rgb = tuple([int(num) for num in rgb_value.split(',')])
    if not all(0 <= num <= 255 for num in rgb):
        raise HTTPException(status_code=404, detail="RGB values out of range.")
    color = ColorController(rgb=rgb)
    return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}


@app.get("/search/hsv/{hsv_value}")
async def read_hsv(hsv_value: str):
    hsv = tuple([int(num) for num in hsv_value.split(',')])
    if 0 <= hsv[0] <= 1 or 0 <= hsv[1] <= 1 or 0 <= hsv[2] <= 255:
        raise HTTPException(status_code=404, detail="HSV values out of range.")
    color = ColorController(hsv=hsv)
    return {"hex_code": color.hex_code, "rgb_value": color.rgb, "hsv_value": color.hsv, "names": color.name}


async def write_image_dominant_colors(name: str, url: str, num_colors: int):
    avg_inertia, dominant_colors = await run_in_threadpool(lambda: extract_colors(image_path=url, k=num_colors))
    await run_in_threadpool(lambda:
        Color.create(name=name, url=url, num_colors=num_colors, dominant_colors=dominant_colors, avg_inertia=avg_inertia)
    )

@app.post("/extract/{num_colors}/")
async def extract_from_image(name: str, url: str, num_colors: int, background_tasks: BackgroundTasks, token: str = Depends(oauth2_scheme)):
    background_tasks.add_task(write_image_dominant_colors, name=name, url=url, num_colors=num_colors)
    return {"message": "colors have been extracted"}



@app.get("/retrieve/{name}/")
async def retrieve_image_data_by_name(name: str, token: str = Depends(oauth2_scheme)):
    return {"num_colors": "number of colors goes here..."}
