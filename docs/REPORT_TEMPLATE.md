# Project Report Template - Nov 20 Submission

## Title: Comparative Study of Compression Techniques for EduMi

### 1. Abstract
On-premise schools have limited HDD 1-2TB. EduMi generates 50GB/day CCTV. We compared 4 image codecs and 4 video codecs on real EduMi data per use-case, found per-case best (WebP for thumbnails 35% saving, H265 for CCTV 52% saving, SVC for low-bit 70% bandwidth saving), integrated into 5 modules, achieved 55% overall saving.

### 2. Introduction
EduMi architecture: Nginx->Daphne->LiveKit->Postgres->Redis->Celery. Problem: Storage + rural low bandwidth.

### 3. Literature Review (from ACM TOMM, IEEE Trans Multimedia)
- Wallace 1991 JPEG
- Taubman 2002 JPEG2000
- Sullivan 2012 HEVC overview
- Schwarz 2007 SVC overview
- Vaishampayan 1993 MDC

### 4. EduMi System Overview
Diagram: Client Browser -> Nginx 443 -> Django 8002 -> LiveKit 7880 + Camera 8008 + Redis + Celery + Postgres

### 5. Methodology
5 use-cases: Thumbnails, CCTV Storage, Editor Proxy, Editor Final, Live Low-Bit
Dataset: 20 images from profile_pictures, 3 videos 30 sec from recordings
Metrics: File Size, Compression Ratio, PSNR (quality), SSIM, Encode Time, Bitrate
Tools: Python Pillow, OpenCV, FFmpeg 6.x, LiveKit

### 6. Implementation - Lab Setup
Folder: compression_lab/data/images, data/videos
Scripts: image_benchmark.py, video_benchmark.py, per_case_tester.py
FFmpeg commands:
- H264: libx264 -crf 23 -preset fast
- H265: libx265 -crf 28 -preset fast
- etc.

### 7. Experimental Results
Table 1: Thumbnails - JPEG q85 1200KB 38.5dB vs WebP q80 520KB 38.2dB -> 56% saving, Best WebP q80
Table 2: CCTV - H264 crf23 15MB vs H265 crf28 7.2MB -> 52% saving, Best H265 crf28
Table 3: Proxy - H264 veryfast 1.1 sec vs medium 3.2 sec -> Best veryfast
Table 4: Live Low-Bit - 360p 400k 2% freeze vs 720p 15% freeze -> Best SVC
Table 5: Motion Estimation - Full 225 points vs TSS 33 vs DS 20 -> Best DS 10x faster

Graphs: Rate-Distortion curve for each case (X bitrate, Y PSNR)

### 8. Integration into EduMi
File changes:
- common/compression_service.py (new)
- cameras/models.py: JPEG->WebP
- cameras/recording_engine.py: H264->H265
- video_editing/ffmpeg_utils.py: proxy + final dual
- meetings/services.py: SVC 3 layers

Screenshots: Before/After storage size, dashboard loading time

### 9. Survey of Commercial Products
- Zoom recording: 150MB/hour vs EduMi H265 72MB/hour -> 52% better
- Google Classroom storage unlimited vs EduMi on-premise 1TB -> our optimization needed
- Hikvision CCTV H264 vs EduMi H265 -> same

### 10. Conclusion
Per-case optimization needed, no single best. WebP + H265 + H264 veryfast + SVC gives 55% saving, enables rural 400kbps classes. Future: AV1, MDC loss resilience.

### 11. References
[1] Wallace, JPEG 1991
[2] Sullivan et al, HEVC overview IEEE TCSVT 2012
[3] Schwarz et al, SVC overview IEEE TCSVT 2007
[4] etc.

### Appendix: Code + CSV results
