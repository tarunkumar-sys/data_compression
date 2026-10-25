"""
Motion Estimation - Full Search vs TSS vs Diamond Search
"""
import glob
print("=== Motion Estimation Comparison ===")
print("Full Search (ES): 225 points/MB, Slowest, PSNR Best")
print("Three Step Search (TSS): 33 points/MB, 7x Faster, PSNR -0.5dB")
print("Diamond Search (DS): ~20 points/MB, 10x Faster, PSNR -0.2dB -> BEST (H.264 uses DS)")
print("\nEduMi me Diamond Search best hai - fast + good quality")
print("Reference: Implement block matching 16x16 macroblock")
try:
    import os
    vids=glob.glob("data/videos/*.mp4") or glob.glob("../data/videos/*.mp4")
    if vids:
        print(f"\nFound video {vids[0]}, would test 2 frames for motion vectors")
    else:
        print("\nAdd video to data/videos/ to test practical")
except:
    pass
