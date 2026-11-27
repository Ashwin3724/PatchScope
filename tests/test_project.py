import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from app.vision import synthetic, features, fit_reference, score, load_image, ImageError, inspect, MAX_BYTES
from app.main import create_app

@pytest.fixture(scope='module')
def model():return fit_reference()
@pytest.fixture(scope='module')
def client(model):
    with TestClient(create_app(model),base_url='http://127.0.0.1:8020') as c:yield c

def png():
    b=io.BytesIO();Image.new('RGB',(64,64),'gray').save(b,format='PNG');return b.getvalue()
def test_synthetic_reproducibility():
    assert synthetic(12,True)[0].tobytes()==synthetic(12,True)[0].tobytes()
    assert synthetic(12,True)[1].sum()>0 and synthetic(12,False)[1].sum()==0
def test_features_shape():assert features(synthetic(0)[0]).shape==(64,4)
def test_reference_threshold(model):assert model['threshold']>0 and model['evaluation']['normal_count']==8
def test_score_finite(model):
    s,patches=score(model,synthetic(42)[0]);assert s>=0 and patches.shape==(8,8)
def test_inspect_returns_png(model):
    d=inspect(model,synthetic(20,True)[0],'sample');assert d['image'].startswith('data:image/png;base64,') and isinstance(d['flagged'],bool)
def test_image_validation():
    assert load_image(png()).size==(128,128)
    with pytest.raises(ImageError):load_image(b'bad')
    with pytest.raises(ImageError):load_image(b'x'*(MAX_BYTES+1))
def test_tiny_image_rejected():
    b=io.BytesIO();Image.new('RGB',(2,2)).save(b,format='PNG')
    with pytest.raises(ImageError,match='at least'):load_image(b.getvalue())
def test_endpoints(client):
    assert client.get('/').status_code==200
    assert client.get('/api/status').json()['ready']
    assert client.get('/api/sample?defect=true').json()['kind']=='synthetic defect'
    r=client.post('/api/inspect',files={'file':('x.png',png(),'image/png')});assert r.status_code==200 and 'heatmap' in r.json()
def test_bad_upload(client):assert client.post('/api/inspect',files={'file':('x.png',b'bad','image/png')}).status_code==400
def test_origin_guard(client):assert client.get('/api/status',headers={'Origin':'https://bad.example'}).status_code==403
