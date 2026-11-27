from urllib.parse import urlsplit
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
ROOT=Path(__file__).resolve().parent.parent

def create_base(name,lifespan=None):
    app=FastAPI(title=name,lifespan=lifespan)
    app.mount('/static',StaticFiles(directory=ROOT/'app'/'static'),name='static')
    @app.middleware('http')
    async def guard(request:Request,call_next):
        if request.url.hostname not in ('127.0.0.1','localhost','::1'):
            return JSONResponse({'detail':'Local use only.'},status_code=403)
        origin=request.headers.get('origin')
        if origin:
            try:
                p=urlsplit(origin); oport=p.port or (443 if p.scheme=='https' else 80); port=request.url.port or (443 if request.url.scheme=='https' else 80)
                if p.scheme!=request.url.scheme or p.hostname!=request.url.hostname or oport!=port:return JSONResponse({'detail':'Cross-origin request rejected.'},status_code=403)
            except ValueError:return JSONResponse({'detail':'Invalid origin.'},status_code=403)
        r=await call_next(request);r.headers['X-Content-Type-Options']='nosniff';r.headers['Referrer-Policy']='no-referrer'
        if request.url.path not in ('/docs','/openapi.json'):
            r.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        return r
    @app.get('/',include_in_schema=False)
    def home():return FileResponse(ROOT/'app'/'static'/'index.html')
    return app
