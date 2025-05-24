from fastapi import FastAPI, Form, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Supplier, Base
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

app = FastAPI()

ADMIN_PASSWORD = "admin_password" # <<< ПАРОЛЬ

# Монтируем папки для статических файлов
app.mount("/CSS", StaticFiles(directory="../CSS"), name="CSS")
app.mount("/JS", StaticFiles(directory="../JS"), name="JS")
# --- ДОБАВЛЕНЫ НОВЫЕ СТАТИЧЕСКИЕ ПАПКИ ДЛЯ ИЗОБРАЖЕНИЙ, ВИДЕО И АУДИО ---
app.mount("/Изабражения", StaticFiles(directory="../Изабражения"), name="images")
app.mount("/Видио", StaticFiles(directory="../Видио"), name="videos")
app.mount("/Аудио", StaticFiles(directory="../Аудио"), name="audio")
# ---------------------------------------------------------------------

templates = Jinja2Templates(directory="../templates")

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализируем геокодер Nominatim
geolocator = Nominatim(user_agent="eco_track_app")

# --- Роуты для обслуживания HTML страниц ---

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    """Обслуживает главную страницу (выбор роли)."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Обслуживает страницу администратора (добавление и карта)."""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/user", response_class=HTMLResponse)
async def user_page(request: Request):
    """Обслуживает страницу пользователя (карта с поиском и списком компаний)."""
    return templates.TemplateResponse("user.html", {"request": request})

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    """Обслуживает страницу успешного добавления."""
    return templates.TemplateResponse("success.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Обслуживает страницу "О проекте"."""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/author", response_class=HTMLResponse) 
async def author_page(request: Request):
    """Обслуживает страницу 'Автор проекта'."""
    return templates.TemplateResponse("author.html", {"request": request})
# ------------------------------------------

# --- API Эндпоинты ---

@app.post("/submit_supplier")
async def submit_supplier(
    company_name: str = Form(...),
    product_name: str = Form(...),
    stage: str = Form(...),
    address: str = Form(...),
    country: str = Form(...),
    region: str = Form(...),
    certifications: str = Form(None),
    labor_practices: str = Form(None),
    environmental_practices: str = Form(None),
    last_audit_date: str = Form(None),
    contact_email: str = Form(None),
    website: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db)
):
    """Эндпоинт для добавления нового поставщика, геокодирование выполняется на сервере."""
    latitude = None
    longitude = None

    if address:
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                latitude = location.latitude
                longitude = location.longitude
            else:
                raise HTTPException(status_code=400, detail=f"Не удалось найти координаты для адреса: '{address}'. Пожалуйста, проверьте адрес.")
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            raise HTTPException(status_code=500, detail=f"Ошибка геокодирования: Проблема с сервисом или таймаут: {e}. Попробуйте еще раз.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Неожиданная ошибка при геокодировании: {e}")

    supplier = Supplier(
        company_name=company_name,
        product_name=product_name,
        stage=stage,
        latitude=latitude,
        longitude=longitude,
        country=country,
        region=region,
        certifications=certifications,
        labor_practices=labor_practices,
        environmental_practices=environmental_practices,
        last_audit_date=last_audit_date,
        contact_email=contact_email,
        website=website,
        notes=notes
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return RedirectResponse(url="/success", status_code=303)

@app.get("/companies", response_class=JSONResponse)
async def get_companies(db: Session = Depends(get_db)):
    """Эндпоинт для получения списка всех поставщиков в формате JSON."""
    companies = db.query(Supplier).all()
    companies_data = [{
        "id": c.id,
        "company_name": c.company_name,
        "product_name": c.product_name,
        "stage": c.stage,
        "latitude": c.latitude if c.latitude is not None else None,
        "longitude": c.longitude if c.longitude is not None else None,
        "country": c.country,
        "region": c.region,
        "certifications": c.certifications,
        "labor_practices": c.labor_practices,
        "environmental_practices": c.environmental_practices,
        "last_audit_date": c.last_audit_date,
        "contact_email": c.contact_email,
        "website": c.website,
        "notes": c.notes,
    } for c in companies]
    return JSONResponse(content=companies_data)

@app.get("/search", response_class=JSONResponse)
async def search_address(q: str):
    """Эндпоинт для поиска координат по адресу с помощью Nominatim."""
    try:
        location = geolocator.geocode(q, timeout=10)
        if location:
            return JSONResponse(content={
                "name": location.address,
                "lat": location.latitude,
                "lon": location.longitude
            })
        else:
            return JSONResponse(content={"error": "Адрес не найден"}, status_code=404)
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"Ошибка геокодирования: Проблема с сервисом или таймаут: {e}")
        return JSONResponse(content={"error": f"Ошибка геокодирования: Проблема с сервисом или таймаут: {e}"}, status_code=500)
    except Exception as e:
        print(f"Ошибка при геокодировании: {e}")
        return JSONResponse(content={"error": f"Ошибка при поиске адреса: {e}"}, status_code=500)

@app.get("/companies/{company_id}", response_class=JSONResponse)
async def get_company_details(company_id: int, db: Session = Depends(get_db)):
    """Эндпоинт для получения деталей одной компании по ID."""
    company = db.query(Supplier).filter(Supplier.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Компания не найдена")

    return JSONResponse(content={
        "id": company.id,
        "company_name": company.company_name,
        "product_name": company.product_name,
        "stage": company.stage,
        "latitude": company.latitude if company.latitude is not None else None,
        "longitude": company.longitude if company.longitude is not None else None,
        "country": company.country,
        "region": company.region,
        "certifications": company.certifications,
        "labor_practices": company.labor_practices,
        "environmental_practices": company.environmental_practices,
        "last_audit_date": company.last_audit_date,
        "contact_email": company.contact_email,
        "website": company.website,
        "notes": company.notes,
    })

@app.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Эндпоинт для удаления компании по ID с проверкой пароля администратора.
    Пароль ожидается в теле запроса как JSON: {"admin_password": "ваш_пароль"}
    """
    try:
        body = await request.json()
        admin_password = body.get("admin_password")

        if admin_password is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль администратора не предоставлен.")

        if admin_password != ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный пароль администратора"
            )

        company = db.query(Supplier).filter(Supplier.id == company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Компания не найдена")

        db.delete(company)
        db.commit()
        return {"message": "Компания успешно удалена"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Неверный формат запроса или ошибка: {e}")


@app.get("/company_detail/{company_id}", response_class=HTMLResponse)
async def company_detail_page(request: Request, company_id: int):
    """Обслуживает страницу с детальной информацией о компании."""
    return templates.TemplateResponse("company_detail.html", {"request": request, "company_id": company_id})