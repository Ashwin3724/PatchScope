"""Small patch-nearest-neighbor anomaly demo with a purely synthetic reference."""
import base64, io
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import roc_auc_score

SIZE=128; PATCH=16; MAX_BYTES=2*1024*1024; MAX_PIXELS=4_000_000
class ImageError(ValueError):pass

def synthetic(seed,defect=False):
    rng=np.random.default_rng(seed)
    # A made-up textured gray surface. No real product images are included.
    y,x=np.mgrid[:SIZE,:SIZE]
    image=125+4*np.sin(y/7)+rng.normal(0,2,(SIZE,SIZE))+rng.normal(0,2)
    mask=np.zeros((SIZE,SIZE),dtype=bool)
    if defect:
        yy=int(rng.integers(24,96));xx=int(rng.integers(20,91))
        image[yy:yy+8,xx:xx+23]-=45;mask[yy:yy+8,xx:xx+23]=True
    return Image.fromarray(np.uint8(np.clip(image,0,255)),'L').convert('RGB'),mask

def load_image(data):
    if not data:raise ImageError('File is empty.')
    if len(data)>MAX_BYTES:raise ImageError('Image exceeds 2 MB.')
    try:
        with Image.open(io.BytesIO(data)) as im:
            if im.format not in ('PNG','JPEG'):raise ImageError('Only PNG and JPEG images are supported.')
            if im.width*im.height>MAX_PIXELS:raise ImageError('Image exceeds 4 million pixels.')
            if im.width<16 or im.height<16:raise ImageError('Image must be at least 16 by 16 pixels.')
            return ImageOps.exif_transpose(im).convert('RGB').resize((SIZE,SIZE),Image.Resampling.BILINEAR)
    except ImageError:raise
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError) as exc:raise ImageError('Unable to read this PNG or JPEG.') from exc

def features(im):
    a=np.asarray(im.convert('L').resize((SIZE,SIZE)),dtype=float)/255
    rows=[]
    for y in range(0,SIZE,PATCH):
        for x in range(0,SIZE,PATCH):
            p=a[y:y+PATCH,x:x+PATCH]
            rows.append([p.mean(),p.std(),np.mean(np.abs(np.diff(p,axis=0))),np.mean(np.abs(np.diff(p,axis=1)))])
    return np.asarray(rows)

def fit_reference():
    ref=np.vstack([features(synthetic(i)[0]) for i in range(32)])
    scaler=StandardScaler().fit(ref)
    nn=NearestNeighbors(n_neighbors=1,algorithm='brute').fit(scaler.transform(ref))
    model={'scaler':scaler,'nn':nn}
    val=[score(model,synthetic(i)[0])[0] for i in range(100,112)]
    model['threshold']=float(np.quantile(val,.95))
    test_normal=[score(model,synthetic(i)[0])[0] for i in range(200,208)]
    test_defect=[score(model,synthetic(i,True)[0])[0] for i in range(300,308)]
    labels=[0]*len(test_normal)+[1]*len(test_defect)
    scores=test_normal+test_defect
    model['evaluation']={'normal_count':len(test_normal),'defect_count':len(test_defect),
        'roc_auc':float(roc_auc_score(labels,scores)),
        'normal_flagged':sum(s>=model['threshold'] for s in test_normal),
        'defects_flagged':sum(s>=model['threshold'] for s in test_defect)}
    return model

def score(model,image):
    f=features(image); distances=model['nn'].kneighbors(model['scaler'].transform(f),return_distance=True)[0].ravel()
    return float(distances.max()),distances.reshape(SIZE//PATCH,SIZE//PATCH)

def as_data_url(img):
    b=io.BytesIO();img.save(b,format='PNG');return 'data:image/png;base64,'+base64.b64encode(b.getvalue()).decode('ascii')

def inspect(model,img,kind):
    score_value,patches=score(model,img);arr=np.asarray(img.convert('RGB'),dtype=float)
    # Map normalized within this image; color intensity is relative, not a probability.
    heat=patches / max(float(patches.max()),1e-10)
    overlay=arr.copy()
    for y in range(8):
        for x in range(8):
            alpha=.62*heat[y,x]
            block=arr[y*PATCH:(y+1)*PATCH,x*PATCH:(x+1)*PATCH]
            overlay[y*PATCH:(y+1)*PATCH,x*PATCH:(x+1)*PATCH]=block*(1-alpha)+np.array([245,55,35])*alpha
    return {'image':as_data_url(img),'heatmap':as_data_url(Image.fromarray(np.uint8(np.clip(overlay,0,255)))),
        'score':score_value,'threshold':model['threshold'],'flagged':bool(score_value>=model['threshold']),'kind':kind}
