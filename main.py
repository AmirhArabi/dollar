from fastapi import FastAPI
from fastapi.responses import JSONResponse
import httpx
from bs4 import BeautifulSoup
import os
from datetime import datetime

app = FastAPI()

async def fetch_tgju_dollar_price():
    url = "https://www.tgju.org/profile/price_dollar_rl"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # روش ۱: جستجوی کلاس info-value (ممکن است نیاز به به‌روزرسانی داشته باشد)
            price_element = soup.select_one('.info-value > span')
            
            # روش ۲: جستجوی itemprop (اگر موجود باشد)
            if not price_element:
                price_element = soup.select_one('[itemprop="price"]')
            
            if price_element:
                price = price_element.get_text(strip=True)
                return {
                    "success": True,
                    "price": price,
                    "currency": "IRR",
                    "last_updated": datetime.utcnow().isoformat(),
                    "source": "tgju.org"
                }
            else:
                return {"success": False, "error": "Element not found"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/dollar")
async def get_dollar_price():
    result = await fetch_tgju_dollar_price()
    if result["success"]:
        return JSONResponse(result)
    else:
        return JSONResponse(result, status_code=500)

# برای تست محلی
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)