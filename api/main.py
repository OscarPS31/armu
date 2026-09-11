from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import recipes

app = FastAPI(title= 'Armu API')

app.add_middleware(
    CORSMiddleware,
    allow_origins= ['*'],
    allow_methods= ['*'],
    allow_headers= ['*']
)

@app.get('/health')
def health():
    return {'status':'ok'}




app.include_router(recipes.router)
