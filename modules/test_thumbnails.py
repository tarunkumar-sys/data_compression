"""
M1: Thumbnails & Profile Images - Multiple Techniques Test
Techniques: JPEG q85, JPEG q75, WebP q80, WebP q70
Output: results/M1_thumbnails_results.csv -> Best = WebP q80 expected
"""
from PIL import Image
import os, time, glob, csv, math, sys
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

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

TECHNIQUES=[
    ("JPEG_q85","JPEG",{"quality":85}),
    ("JPEG_q75","JPEG",{"quality":75}),
    ("WebP_q80","WEBP",{"quality":80}),
    ("WebP_q70","WEBP",{"quality":70}),
]

def test_module():
    os.makedirs("results", exist_ok=True)
    all_files=glob.glob("data/images/*.*")
    files=[f for f in all_files if f.lower().endswith(('.jpg','.jpeg','.png','.webp','.avif','.bmp','.tiff'))]
    if not files:
        print("❌ M1: data/images/ me 20 pics daal - Edumi2/media/profile_pictures se")
        return []
    results=[]
    for fp in files[:20]:
        try:
            img=Image.open(fp).convert('RGB')
        except Exception as ex:
            print(f"Skip {fp}: {ex}")
            continue
        orig=os.path.getsize(fp)
        base=os.path.splitext(os.path.basename(fp))[0]
        for name,fmt,par in TECHNIQUES:
            out=f"results/M1_{base}_{name}.tmp"
            s=time.time()
            try:
                img.save(out,fmt,**par)
                e=(time.time()-s)*1000
                comp=os.path.getsize(out)
                saving=(1-comp/orig)*100
                results.append({"module":"M1_thumbnails","file":base,"technique":name,"orig_kb":round(orig/1024,1),"comp_kb":round(comp/1024,1),"saving_%":round(saving,1),"psnr":round(psnr(fp,out),2),"time_ms":round(e,1)})
                os.remove(out)
            except Exception as ex:
                print(f"Skip {name}: {ex}")
    return results

if __name__=="__main__":
    res=test_module()
    if res:
        os.makedirs("results",exist_ok=True)
        with open("results/M1_thumbnails_results.csv","w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=res[0].keys()); w.writeheader(); w.writerows(res)
        print(f"✅ M1 Done: results/M1_thumbnails_results.csv - {len(res)} tests")
        
        # Summary of all 4 techniques
        print("\n📊 M1 All Techniques Comparison (Averages):")
        print(f"   {'Technique':<15} | {'Avg Saving %':<14} | {'Avg PSNR (dB)':<14} | {'Avg Time (ms)':<14}")
        print("   " + "-"*65)
        for name, _, _ in TECHNIQUES:
            tech_rows=[r for r in res if r['technique']==name]
            if tech_rows:
                avg_sav=sum(r['saving_%'] for r in tech_rows)/len(tech_rows)
                avg_psnr=sum(r['psnr'] for r in tech_rows)/len(tech_rows)
                avg_time=sum(r['time_ms'] for r in tech_rows)/len(tech_rows)
                print(f"   {name:<15} | {avg_sav:>12.1f}% | {avg_psnr:>12.1f} | {avg_time:>12.1f}")
        
        # Find best
        best=max(res,key=lambda x: x['saving_%'] if x['psnr']>35 else -1)
        print(f"\n🏆 M1 Best: {best['technique']} -> {best['saving_%']}% saving, PSNR {best['psnr']}dB - Use in cameras/models.py")
