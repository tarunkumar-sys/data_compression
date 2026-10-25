"""
Image Compression Benchmark - Per Case: Thumbnails
Tests: JPEG vs WebP - Best for EduMi thumbnails
"""
from PIL import Image
import os, time, glob, csv, math, sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

DATA_DIR = "data" if os.path.exists("data") else "../data"
RESULTS_DIR = "results" if os.path.exists("results") and not os.path.exists("../results") else ("../results" if os.path.exists("../results") else "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def psnr(p1,p2):
    try:
        import numpy as np
        i1 = np.array(Image.open(p1).convert('RGB'))
        i2 = np.array(Image.open(p2).convert('RGB'))
        if i1.shape != i2.shape:
            i2 = np.array(Image.fromarray(i2).resize((i1.shape[1], i1.shape[0])))
        mse = np.mean((i1.astype(float) - i2.astype(float)) ** 2)
        return 100 if mse == 0 else 20 * math.log10(255.0 / math.sqrt(mse))
    except Exception:
        return 0

def test_image(path):
    try:
        img=Image.open(path).convert('RGB')
    except Exception as ex:
        print(f"Skip {path}: {ex}")
        return []
    base=os.path.splitext(os.path.basename(path))[0]
    orig=os.path.getsize(path)
    tests=[("JPEG_q95","JPEG",{"quality":95}),("JPEG_q85","JPEG",{"quality":85}),("JPEG_q75","JPEG",{"quality":75}),("WebP_q90","WEBP",{"quality":90}),("WebP_q80","WEBP",{"quality":80}),("WebP_q70","WEBP",{"quality":70})]
    res=[]
    for name,fmt,par in tests:
        out=os.path.join(RESULTS_DIR, f"{base}_{name}.tmp")
        s=time.time()
        try:
            img.save(out,fmt,**par)
            e=(time.time()-s)*1000
            comp=os.path.getsize(out)
            saving=(1-comp/orig)*100
            res.append({"case":"thumbnails","image":base,"codec":name,"orig_kb":round(orig/1024,1),"comp_kb":round(comp/1024,1),"saving_%":round(saving,1),"time_ms":round(e,1),"psnr":round(psnr(path,out),2)})
            os.remove(out)
        except Exception as ex:
            print(f"Skip {name}: {ex}")
    return res

if __name__=="__main__":
    all_imgs=glob.glob(os.path.join(DATA_DIR, "images/*.*"))
    imgs=[p for p in all_imgs if p.lower().endswith(('.jpg','.jpeg','.png','.webp','.avif','.bmp','.tiff'))]
    if not imgs:
        print(f"❌ {DATA_DIR}/images/ me pics nahi mili")
    else:
        allr=[]
        for p in imgs[:20]:
            print(f"Testing {p}")
            allr.extend(test_image(p))
        if allr:
            out_csv = os.path.join(RESULTS_DIR, "image_comparison.csv")
            with open(out_csv,"w",newline="", encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=allr[0].keys()); w.writeheader(); w.writerows(allr)
            print(f"✅ results/image_comparison.csv - {len(allr)} tests")
            # Summary of all tested techniques
            unique_codecs=list(dict.fromkeys([r['codec'] for r in allr]))
            print("\n📊 All Tested Techniques Comparison (Averages):")
            print(f"   {'Codec':<12} | {'Avg Saving %':<14} | {'Avg Time (ms)':<14} | {'Avg PSNR (dB)':<14}")
            print("   " + "-"*60)
            for codec in unique_codecs:
                vals=[r for r in allr if r['codec']==codec]
                if vals:
                    avg_sav=sum(v['saving_%'] for v in vals)/len(vals)
                    avg_time=sum(v['time_ms'] for v in vals)/len(vals)
                    avg_psnr=sum(v['psnr'] for v in vals)/len(vals)
                    print(f"   {codec:<12} | {avg_sav:>12.1f}% | {avg_time:>12.1f} | {avg_psnr:>12.1f}")
