import json
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.responses import FileResponse
import httpx
from lxml import html
import jdatetime 

CACHE_FILE_PATH = "/tmp/cache.json"
CACHE_EXPIRY_MINUTES = 60

app = FastAPI()


async def fetch_price_from_source():
    url = "https://www.tgju.org/profile/price_dollar_rl"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        tree = html.fromstring(response.content)
        xpath_expr = '/html/body/main/div[1]/div[1]/div[1]/div/div[1]/div[3]/div[1]/span[2]'
        result = tree.xpath(xpath_expr)
        price = result[0].text.strip() if result and result[0].text else None

        return {
            "success": True,
            "price": price,
            "currency": "IRR",
            "last_updated": jdatetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": "tgju.org"
        }

def load_cache():
    try:
        if os.path.exists(CACHE_FILE_PATH):
            with open(CACHE_FILE_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        print("Cache load failed:", e)
    return None

def save_cache(data):
    try:
        with open(CACHE_FILE_PATH, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("Cache save failed:", e)

@app.get("/api/dollar")
async def get_price(request: Request):
    pretty = request.query_params.get("pretty") == "true"
    cache = load_cache()
    now = datetime.utcnow()

    def make_response(data):
        if pretty:
            return Response(
                content=json.dumps(data, indent=4, ensure_ascii=False),
                media_type="application/json"
            )
        return JSONResponse(content=data)

    if cache:
        try:
            timestamp = datetime.fromisoformat(cache["last_updated"])
            if now - timestamp < timedelta(minutes=CACHE_EXPIRY_MINUTES):
                return make_response(cache)
        except Exception:
            pass

    try:
        new_data = await fetch_price_from_source()
        if new_data["success"]:
            save_cache(new_data)
        return make_response(new_data)
    except Exception as e:
        if cache:
            cache["warning"] = "Source failed, showing cached data"
            return make_response(cache)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

@app.get("/api")
async def root():
    return JSONResponse(
        content={
            "success": True,
            "message": "Welcome to free currency API",
            "endpoint": ["/api/dollar"],
            "description": "Fetch the latest currency price in Iran",
            "author": "digitallyboy@gmail.com",
            "version": "1.0",
        },
        media_type="application/json"
    )


 
@app.get("/")
async def read_index():
    return FileResponse('templates/index.html')
     
