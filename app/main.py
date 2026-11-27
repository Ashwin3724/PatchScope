from contextlib import asynccontextmanager
from fastapi import File, UploadFile, HTTPException
from app.base import create_base
from app.vision import fit_reference,synthetic,load_image,inspect,ImageError,MAX_BYTES

def create_app(model=None):
    @asynccontextmanager
    async def lifespan(app):
        if app.state.model is None:app.state.model=fit_reference()
        yield
    app=create_base('PatchScope',lifespan);app.state.model=model
    @app.get('/api/status')
    def status():
        m=app.state.model
        return {'ready':m is not None,'threshold':m['threshold'],'evaluation':m['evaluation']} if m else {'ready':False}
    @app.get('/api/sample')
    def sample(defect:bool=False):return inspect(app.state.model,synthetic(1001,defect)[0],'synthetic defect' if defect else 'synthetic normal')
    @app.post('/api/inspect')
    async def upload(file:UploadFile=File(...)):
        content=await file.read(MAX_BYTES+1);await file.close()
        try:img=load_image(content)
        except ImageError as e:raise HTTPException(400,str(e)) from e
        return inspect(app.state.model,img,'uploaded image')
    return app
app=create_app()
