from fastapi import FastAPI,Request
from fastapi.templating import Jinja2Templates

app=FastAPI()

templates= Jinja2Templates(directory='templates')

@app.get('/')
async def name(request: Request):
    return templates.TemplateResponse('index.html',{'request':request})

@app.get('/login')
def name(request: Request):
    return templates.TemplateResponse('login.html',{'request':request})

@app.get('/register')
def name(request: Request):
    return templates.TemplateResponse('register.html',{'request':request})