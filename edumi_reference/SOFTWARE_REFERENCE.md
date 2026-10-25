# 🎓 EduMi — Comprehensive Software Reference Report

> **Document Purpose:** Full technical and functional reference for EduMi (Edumi2).
> Intended as the authoritative source document for developers, administrators, and integration engineers.
>
> **Generated:** October 2026 | **Version:** Edumi2 | **License:** Commercial Enterprise

---

## 📑 Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Core Design Principles](#2-core-design-principles)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Python Dependencies](#5-python-dependencies)
6. [Module Reference](#6-module-reference)
   - [6.1 Accounts & Authentication](#61-accounts--authentication)
   - [6.2 Meetings & Virtual Classrooms](#62-meetings--virtual-classrooms)
   - [6.3 Attendance & Biometric Recognition](#63-attendance--biometric-recognition)
   - [6.4 Assignments & Quizzes](#64-assignments--quizzes)
   - [6.5 Cameras & CCTV](#65-cameras--cctv)
   - [6.6 Video Editing Studio](#66-video-editing-studio)
   - [6.7 RAG Workspace (AI Knowledge Base)](#67-rag-workspace-ai-knowledge-base)
   - [6.8 Common Utilities](#68-common-utilities)
7. [Database Schema Summary](#7-database-schema-summary)
8. [User Roles & Permissions](#8-user-roles--permissions)
9. [Environment Variables Reference](#9-environment-variables-reference)
10. [Microservices & Port Matrix](#10-microservices--port-matrix)
11. [Deployment Guide](#11-deployment-guide)
12. [Security & Privacy Architecture](#12-security--privacy-architecture)
13. [Repository Structure](#13-repository-structure)
14. [Authors & License](#14-authors--license)

---

## 1. Executive Summary

**EduMi** is a **self-hosted, on-premise, enterprise-grade academic operating system** engineered for educational institutions. It replaces fragmented subscription-heavy tools (Zoom, Teams, separate LMS portals, standalone video editors, paper roll-calls) with a **single unified platform** that runs entirely within an institution's LAN or private cloud.

### What EduMi Does

| Module | Features & Capabilities |
|---|---|
| **Live Virtual Classrooms** | Sub-second WebRTC audio/video via dedicated LiveKit SFU. Host controls: mute-all, remove user, camera lock, screen-share permissions. Live chat, hand-raising, quiz launches, automated attendance. |
| **AI Biometric Attendance** | Pre-join face verification via OpenCV YuNet + SFace (128-D). Client-side guidance via `face-api.js`. Anti-spoofing via MiniFASNetV2. Encrypted at rest via Fernet AES. |
| **Hardware & Mobile CCTV** | RTSP IP camera ingestion. Mobile IP camera integration (iOS/Android). Real-time crowd head-counting with bounding boxes & occupancy tracking. |
| **Academic LMS & Quizzes** | File-based homework submissions with magic-byte validation. Timed MCQ quizzes with auto-scoring. Study material library with RAG indexing. |
| **Video Editing Studio** | Browser-based non-destructive timeline editor. Multi-track audio, trim, split, rotate, resize, text captions. FFmpeg filtergraph rendering via Celery. |
| **Enterprise Authentication** | 6-digit email OTP with signed cryptographic fallback tokens. Sliding-window rate limiters. Strict role-based access control. |
| **Messaging & Notifications** | 1-to-1 direct messaging and campus-wide WebSocket announcements. Persistent in-app notifications. |
| **AI Knowledge Base (RAG)** | Semantic search over study materials. PDF/Word extraction, embedding, vector search, LLM Q&A. |

### Why On-Premise?

- **Zero Internet Dependency** — all video & CCTV traffic stays inside the school LAN; classes continue even if external internet drops
- **Absolute Data Sovereignty** — biometrics, grades, and recordings never leave school premises
- **Compliance Ready** — aligns with DPDP (India), FERPA (US), and GDPR standards
- **Zero Per-User SaaS Fees** — deploy for 500 or 5,000 students with no per-seat licensing cost

---

## 2. Core Design Principles

| Principle | Implementation |
|---|---|
| **100% Data Sovereignty** | Self-hosted on institution LAN/server; zero external telemetry, zero cloud lock-in |
| **Biometric Privacy First** | Raw face images are discarded immediately after registration; only encrypted 128-D float vectors are persisted |
| **Encryption at Rest** | Fernet (AES-128-CBC + HMAC-SHA256) for biometric vectors; `EncryptedTextField` for meeting chat messages |
| **Ultra-Low Latency Media** | LiveKit WebRTC SFU on-premise; Django Channels (ASGI/Daphne) for WebSocket real-time state |
| **Dual Database Resilience** | PostgreSQL (production) with automatic SQLite fallback for offline/dev environments |
| **Security Hardening** | Sliding-window rate limiters, magic-byte MIME validation, process isolation for heavy CPU tasks |

---

## 3. System Architecture

```
                 ┌──────────────────────────────────────────────┐
                 │    Institute Local Server (Server Room/Lab)   │
                 │   (Ubuntu 22.04 LTS / Windows — 16-32 GB RAM)│
                 │                                              │
                 │   • PostgreSQL Database                      │
                 │   • LiveKit WebRTC SFU (LAN Streaming)       │
                 │   • Daphne ASGI + Nginx (HTTPS: 443 / 8002)  │
                 │   • Redis (Task Queue & Channel Layers)      │
                 └──────────────────────┬───────────────────────┘
                                        │
            ┌───────────────────────────┼──────────────────────────┐
            │       Campus Gigabit LAN / Wi-Fi (192.168.x.x)       │
   ┌─────────▼────────┐          ┌──────▼──────────┐    ┌──────────▼──────────┐
   │  Student Devices │          │ Teacher Laptops │    │ Campus RTSP /       │
   │  (Phones / PCs)  │          │ (Live Classes)  │    │ Mobile Cameras      │
   └──────────────────┘          └─────────────────┘    └─────────────────────┘
```

```
                         Client Browser (HTTPS / WSS)
                                    │
                 ┌──────────────────▼──────────────────┐
                 │    Nginx Reverse Proxy / SSL         │  Port 443 / 8002
                 └─────────┬──────────────────┬─────────┘
                           │                  │
          ┌────────────────▼────────┐  ┌──────▼────────────────────┐
          │  Django Monolith ASGI   │  │  Camera Microservice      │
          │  (Auth, LMS, Channels)  │  │  (OpenCV, RTSP, Headcount)│
          │  Port 8002              │  │  Port 8008 (Waitress)     │
          └────────────┬────────────┘  └───────────────────────────┘
                       │
       ┌───────────────┼──────────────────┐
       │               │                  │
┌──────▼──────┐  ┌─────▼──────┐  ┌───────▼──────────┐
│ PostgreSQL  │  │   Redis    │  │  Celery Worker   │
│ Port 5432   │  │ Port 6379  │  │ (FFmpeg / AI BG) │
└─────────────┘  └────────────┘  └──────────────────┘
                                         │
                               ┌─────────▼──────────┐
                               │ LiveKit WebRTC SFU  │
                               │ Ports 7880 / 7881   │
                               └─────────────────────┘
```

**Request Flow:**
1. All user traffic hits **Nginx** which terminates SSL and forwards to Daphne
2. HTTP requests → Django views (LMS, Auth, Admin, API)
3. WebSocket upgrades → Django Channels consumers (live chat, face tracking, meeting events)
4. CCTV / camera requests → Camera Microservice (Waitress, port 8008)
5. Heavy processing (FFmpeg video rendering, AI batch tasks) → Celery workers via Redis
6. WebRTC media sessions → LiveKit SFU (ports 7880–7882)

---

## 4. Technology Stack

| Layer | Technology | Version / Notes |
|---|---|---|
| **Backend Framework** | Django | 4.2 LTS |
| **Async / WebSocket** | Django Channels + Daphne (ASGI) | ≥ 4.0 |
| **Camera Microservice** | Waitress | Lightweight WSGI for OpenCV service |
| **Reverse Proxy / SSL** | Nginx | SSL termination, static files, WebSocket proxy |
| **WebRTC SFU** | LiveKit | Self-hosted; on-premise media server |
| **Task Queue** | Celery 5.3 | Async FFmpeg jobs, email, AI tasks |
| **Cache / Broker** | Redis 7 | Channel layers + Celery broker |
| **Primary Database** | PostgreSQL 15+ | Encrypted biometrics storage |
| **Dev/Fallback Database** | SQLite 3 | Automatic fallback |
| **Face Detection** | OpenCV + YuNet ONNX | Apache 2.0 model |
| **Face Recognition** | SFace ONNX (128-D embeddings) | Apache 2.0 model |
| **Liveness Detection** | MiniFASNetV2 | Anti-spoofing |
| **Client-Side Face** | face-api.js | Positioning guidance in browser |
| **Video Processing** | FFmpeg 6.x + FFprobe | Filtergraph rendering pipeline |
| **Cryptography** | Fernet (cryptography lib) | AES-128-CBC + HMAC-SHA256 |

---

## 5. Python Dependencies

> Full list: [`requirements.txt`](./requirements.txt)

| Package | Purpose |
|---|---|
| `Django>=4.2,<5.0` | Web framework |
| `daphne>=4.0.0` | ASGI server for HTTP + WebSocket |
| `channels>=4.0.0` | Django WebSocket / real-time layer |
| `channels-redis>=4.1.0` | Redis channel layer backend |
| `celery>=5.3.0` | Distributed task queue |
| `redis` | Redis client |
| `livekit-api>=0.4.0` | LiveKit Python SDK for token generation |
| `opencv-python` | Computer vision (YuNet, SFace, head counting) |
| `cryptography>=42.0.0` | Fernet encryption for biometrics |
| `psycopg2-binary>=2.9` | PostgreSQL adapter |
| `dj-database-url` | Database URL parser |
| `python-dotenv` | Environment variable loading |
| `pillow` | Image processing |
| `numpy` | Numerical arrays (face embedding math) |
| `waitress` | Camera microservice WSGI server |
| `openpyxl` | Excel report export |
| `pypdf>=3.17.0` | PDF text extraction for RAG indexing |
| `python-docx>=1.1.0` | Word document parsing for RAG |
| `pyOpenSSL` | SSL certificate handling |
| `whitenoise` | Static file serving |
| `psutil>=5.9.0` | System resource monitoring |
| `qrcode` | QR code generation |
| `websockets` | WebSocket protocol support |
| `django-cors-headers` | Cross-Origin Resource Sharing headers |
| `django-redis` | Django Redis cache backend |
| `Twisted` + `autobahn` | ASGI underlying async framework |

---

## 6. Module Reference

---

### 6.1 Accounts & Authentication

**Location:** `accounts/`

**Purpose:** User management, authentication, OTP email verification, rate limiting, direct messaging, and notifications.

#### Key Files

| File | Responsibility |
|---|---|
| `models.py` | `UserProfile`, `EmailVerificationOTP`, `StudentPhoto`, `UserAchievement` |
| `messaging_models.py` | `Conversation`, `Message` (1-to-1 & group DMs) |
| `notification_models.py` | `Notification` model + delivery utilities |
| `email_tokens.py` | Cryptographic OTP generation, signed fallback tokens |
| `ratelimit.py` | Sliding-window rate limiter (Redis-backed) |
| `identity.py` | Cross-module identity resolution helpers |
| `admin_services.py` | Admin-level user management business logic |
| `services.py` | Registration, login, profile update service layer |
| `signals.py` | Django signals for `UserProfile` auto-creation |
| `consumers.py` | WebSocket consumer for real-time notifications |
| `tasks.py` | Celery tasks (email delivery, OTP cleanup) |
| `serializers.py` | DRF-compatible serializers for user data |

#### Data Models

##### `UserProfile`

Extends Django's built-in `User` with role-specific academic fields.

| Field | Type | Notes |
|---|---|---|
| `user` | `OneToOneField → User` | Core Django user |
| `user_type` | `CharField` | `student`, `teacher`, `admin` |
| `bio` | `TextField` | Optional biography |
| `phone` | `CharField` | Aliased as `contact_number` (SSOT) |
| `date_of_birth` | `DateField` | |
| `address` | `TextField` | |
| `profile_picture` | `ImageField` | Upload to `profile_pictures/` |
| `display_name` | `CharField` | Overrides first+last name display |
| `headline` | `CharField` | Short tagline |
| `cgpa` | `CharField` | Academic score |
| `subjects` | `TextField` | Comma-separated subjects |
| `github` / `linkedin` / `twitter` / `website` | `URLField` | Social links |
| `student_id` | `CharField` (unique) | Roll number; aliased as `roll_number` (SSOT) |
| `branch` | `CharField` | Department/branch (student) |
| `grade` | `CharField` | Year/grade (student) |
| `enrollment_date` | `DateField` | |
| `employee_id` | `CharField` (unique) | Teacher employee ID |
| `department` | `CharField` | Teacher department |
| `specialization` | `CharField` | Teacher specialization |
| `join_date` | `DateField` | Teacher joining date |
| `is_verified` | `BooleanField` | Email OTP verified |
| `email_verified_at` | `DateTimeField` | Verification timestamp |
| `last_seen` | `DateTimeField` | Last platform activity |
| `created_at` / `updated_at` | `DateTimeField` | Timestamps |

**Key methods:**
- `get_display_name()` — resolves display name from `display_name` → full name → username
- `get_profile_picture_url()` — returns picture URL or auto-generated UI avatar
- `get_identity_dict()` — standardized serializable identity for cross-module use
- `get_dashboard_url()` — returns role-appropriate landing URL
- `verify_email()` — marks email as verified with timestamp

##### `EmailVerificationOTP`

Enterprise-grade OTP persistence.

| Field | Notes |
|---|---|
| `otp_hash` | SHA-256 hashed 6-digit code |
| `expires_at` | TTL-based expiry |
| `is_used` | Single-use enforcement |
| `attempts` | Brute-force throttle counter |

##### `UserAchievement`

Achievement badges linked to `UserProfile`. Fields: `title`, `description`, `date_str`, `icon_type`.

#### Authentication Flow

```
Registration
    │
    ▼
6-digit OTP emailed (SHA-256 hashed, stored in DB)
    │
    ▼
User enters OTP → verified → is_verified = True
    │
    ▼
Redirect to role-specific dashboard
(/admin/, /teacher-dashboard/, /student-dashboard/)
```

- Sliding-window Redis rate limiters protect `/login/`, `/verify-otp/`, `/register/`
- Signed cryptographic fallback tokens for OTP recovery

---

### 6.2 Meetings & Virtual Classrooms

**Location:** `meetings/`

**Purpose:** LiveKit WebRTC virtual classrooms, classroom/student management, live chat, meeting controls, study materials, and RAG indexing pipeline.

#### Key Files

| File | Responsibility |
|---|---|
| `models.py` | All meeting/classroom data models |
| `consumers.py` | WebSocket event broker for live meeting state |
| `services.py` | LiveKit token generation, room management |
| `tasks.py` | Celery tasks for meeting cleanup |
| `livekit_http_proxy.py` | HTTP proxy to LiveKit REST API |
| `livekit_proxy.py` | WebSocket proxy to LiveKit signal server |

#### Data Models

##### `Classroom`

Persistent virtual classroom that survives across multiple meeting sessions.

| Field | Notes |
|---|---|
| `class_code` | Unique join code shared with students |
| `password` | Hashed classroom password |
| `teacher` | ForeignKey → User (classroom owner) |
| `auto_approve` | Skip manual approval for valid join requests |
| `is_active` | Soft-disable the classroom |

**Key methods:** `get_approved_students()`, `has_active_meeting()`, `get_active_meeting()`, `get_or_create_conversation()`

##### `ClassroomMembership`

Student enrollment lifecycle per classroom.

| Status | Meaning |
|---|---|
| `pending` | Awaiting teacher approval |
| `approved` | Full classroom access |
| `denied` | Join request rejected |
| `removed` | Removed by teacher |
| `left` | Student left voluntarily |

##### `Meeting`

A live WebRTC session (linked to a classroom or standalone).

| Field | Notes |
|---|---|
| `status` | `scheduled`, `live`, `ended`, `cancelled` |
| `sleep_status` | `active`, `sleeping` (teacher pauses session) |
| `meeting_type` | `classroom` or `temporary` |
| `global_mute` / `global_camera_off` / `global_screenshare_off` | Classroom-wide teacher controls |
| `student_can_view_camera` / `student_can_view_screenshare` | Per-meeting visibility |
| `duration_minutes` | Auto-expiry after this duration |
| `allow_chat` / `allow_screen_share` | Feature toggles |
| `record_meeting` | Enable recording |

**Key methods:** `is_expired()`, `is_sleeping()`, `can_join()`, `is_teacher_present()`, `put_to_sleep()`, `unfreeze()`

##### `MeetingParticipant`

Per-user session tracking inside a meeting.

| Field | Notes |
|---|---|
| `joined_at` / `left_at` | Attendance timestamps |
| `total_duration_seconds` | Cumulative time in meeting |
| `audio_permitted` / `video_permitted` / `screenshare_permitted` | Teacher-managed per-participant controls |

##### `MeetingChat`

Encrypted in-meeting chat messages.

- Uses `EncryptedTextField` — all messages are **AES-256 encrypted at rest**

##### `StudyMaterial`

Classroom resource library item.

| Field | Notes |
|---|---|
| `material_type` | `document`, `slides`, `notes`, `video`, `link`, `book` |
| `extracted_text` | Parsed plaintext for RAG/LLM indexing |
| `summary_ai` | AI-generated conceptual summary |
| `key_topics` | JSON list of extracted keywords |
| `rag_indexed` | Whether document is in the vector store |
| `rag_metadata` | Vector IDs, model version, chunking metadata |
| `download_count` / `view_count` | Usage analytics |

##### `MaterialChunk`

Segmented text chunk for RAG embedding retrieval.

| Field | Notes |
|---|---|
| `chunk_index` | Sequential chunk number |
| `chunk_text` | Raw text content |
| `token_count` | Token size estimate |
| `page_number` | Source page reference |
| `embedding_id` | Vector DB reference |
| `embedding_vector` | Float array for semantic search |

**Additional Models:** `MeetingAttendanceLog`, `MeetingSummary`, `KickedParticipant`, `MaterialUnit`, `MaterialBookmark`

---

### 6.3 Attendance & Biometric Recognition

**Location:** `attendance/`

**Purpose:** YuNet + SFace facial recognition pipeline, attendance record management, engagement scoring, and face reset requests.

#### Key Files

| File | Responsibility |
|---|---|
| `models.py` | All biometric and attendance data models |
| `face_service.py` | Core face detection + recognition pipeline |
| `encryption_service.py` | Fernet encrypt/decrypt of face vectors |
| `engagement_service.py` | Per-student emotion/engagement scoring |
| `consumers.py` | WebSocket consumer for real-time face verification |
| `face_tracking_consumer.py` | Continuous face tracking during live meetings |

#### Data Models

##### `StudentFaceProfile`

Secure biometric storage — the only biometric data model in the system.

| Field | Notes |
|---|---|
| `face_embedding_encrypted` | `BinaryField` — Fernet-encrypted 128-D float vector |
| `embedding_checksum` | SHA-256 hash for tamper detection |
| `face_photo` | Admin-only registration photo (not retained in production) |
| `face_quality_score` | 0.0–1.0 quality rating from YuNet |
| `registration_ip` | IP address at time of enrollment |
| `consent_version` / `consent_at` | GDPR/DPDP consent tracking |
| `needs_reenroll` | Force re-registration flag |
| `last_verified_at` | Timestamp of last successful recognition |

##### `AttendanceRecord`

One record per student per meeting — auto-created by the face recognition pipeline.

| Field | Notes |
|---|---|
| `status` | `present`, `absent`, `late`, `partial` |
| `verification_method` | `face_recognition` or `manual` |
| `face_match_confidence` | Float 0.0–1.0 |
| `face_verified_at` | Timestamp of successful match |
| `overridden_by` / `override_reason` | Teacher manual override |

##### `AttendanceSettings`

Per-classroom configuration controlled by the teacher.

| Field | Default | Notes |
|---|---|---|
| `face_recognition_enabled` | `True` | Toggle biometric verification |
| `match_similarity` | `0.363` | Min Cosine Similarity (SFace) |
| `confidence_threshold` | `0.55` | Legacy Euclidean distance threshold |
| `presence_duration_seconds` | `30` | Cumulative verified seconds for "Present" |
| `late_threshold_minutes` | `10` | Minutes past session start → "Late" |
| `recognition_interval_seconds` | `15` | How often client sends a frame |
| `enforce_schedule` | `False` | Only record on scheduled class days |

##### `ClassSchedule`

Per-classroom weekly timetable (Monday = 0, Sunday = 6). Fields: `day_of_week`, `start_time`, `end_time`, `is_active`.

##### `FaceRecognitionLog`

Full audit trail — **no images are ever stored**.

| Event Type | Meaning |
|---|---|
| `match_success` | Face recognized and matched |
| `match_failed` | Face detected but no match |
| `no_face` | No face detected in frame |
| `multiple_faces` | More than one face in frame |
| `low_quality` | Image quality too low |
| `no_profile` | No face profile registered for student |
| `error` | Processing error |

##### `EngagementReport`

Auto-generated after each meeting ends.

| Field | Notes |
|---|---|
| `student_data` | JSON list of per-student engagement summaries |
| `class_engagement_score` | 0–100 overall class score |

##### `StudentEngagementSnapshot`

Raw per-frame emotion snapshots collected during the meeting.

| Emotion | Meaning |
|---|---|
| `focused` | Attentive |
| `happy` | Engaged positively |
| `surprised` | Alert/surprised |
| `tired` | Sleeping/drowsy |
| `confused` | Uncertain/lost |
| `distracted` | Looking away |
| `absent` | Not visible |
| `unknown` | Unclassified |

##### `FaceResetRequest`

Student-initiated admin-approval workflow for face re-enrollment.
States: `pending` → `approved` / `denied`

#### Face Recognition Pipeline

```
Student joins meeting
       │
       ▼
face-api.js (client) — positioning guidance overlay
       │
       ▼ (frame sent via WebSocket every N seconds)
FaceTrackingConsumer (Django Channels)
       │
       ▼
YuNet ONNX → detect face bounding box
       │
       ▼
MiniFASNetV2 → liveness anti-spoofing check
       │
       ▼
SFace ONNX → extract 128-D embedding vector
       │
       ▼
Fernet decrypt stored embedding → Cosine similarity
       │
   match ≥ threshold?
   YES → mark Present / update confidence
   NO  → log FaceRecognitionLog(match_failed)
```

---

### 6.4 Assignments & Quizzes

**Location:** `assignments/`

**Purpose:** File-based homework assignments, timed MCQ/text quizzes, auto-grading, and anti-cheating tab-switch tracking.

#### Data Models

##### `Assignment`

Teacher-created homework task for a classroom.

| Field | Notes |
|---|---|
| `status` | `draft`, `published`, `archived` |
| `due_date` | Hard deadline; auto-detects late submissions |
| `total_marks` | Maximum score |
| `instructions` | Detailed task instructions |

##### `AssignmentQuestionFile`

Files attached to an assignment (PDF, image, link). Validated with magic-byte MIME checks.

##### `AssignmentSubmission`

Student homework submission.

| Field | Notes |
|---|---|
| `status` | `submitted`, `late`, `returned` |
| `marks_obtained` | Graded score |
| `feedback` | Teacher's written feedback |
| `evaluated_by` | Which teacher graded it |

Auto-sets `status = 'late'` on `save()` if submitted after `due_date`.

##### `Quiz`

Timed online test for a classroom.

| Field | Notes |
|---|---|
| `time_limit` | Minutes; null = unlimited |
| `status` | `draft`, `published`, `archived` |
| Can be launched live inside a meeting | |

##### `Question`

Individual quiz question.
- Types: `mcq` (Multiple Choice), `text` (Free text answer)
- Supports image attachment

##### `Choice`

MCQ answer option with `is_correct` flag for auto-grading.

##### `QuizSubmission`

Student quiz attempt record.

| Field | Notes |
|---|---|
| `tab_switch_count` | Anti-cheating: number of browser tab violations |
| `time_taken_seconds` | Duration tracker |
| `is_live_meeting_quiz` | Launched during WebRTC class |
| `marks_obtained` | Auto-graded for MCQs |
| `started_at` | When student opened the quiz |

##### `StudentAnswer`

Individual answer per question per quiz submission.

---

### 6.5 Cameras & CCTV

**Location:** `cameras/`, `camera_service/`, `mobile_cameras/`

**Purpose:** Campus RTSP camera ingestion, mobile IP webcam integration, CCTV recording, crowd head-counting, and classroom streaming.

#### Camera Types

| Type | Protocol | Description |
|---|---|---|
| `rtsp` | `rtsp://` | Standard RTSP IP cameras, campus CCTVs, network DVRs |
| `ip_webcam` | `http://IP:PORT/video` | Android IP Webcam app |
| `droidcam` | `http://IP:PORT/mjpegfeed` | iPhone DroidCam app |

#### Data Models

##### `Camera`

Camera registration and connection details.

| Field | Notes |
|---|---|
| `camera_type` | `rtsp`, `ip_webcam`, `droidcam` |
| `ip_address` / `port` / `stream_path` | Connection details |
| `username` / `password` | RTSP authentication credentials |
| `livekit_room` | Linked LiveKit room for streaming |
| `is_live` | Current streaming status |
| `live_teacher` | Which teacher activated the stream |

##### `CameraPermission`

Teacher access control per camera.
- `show_to_students` — whether students can view this camera feed during meetings

##### `CameraRecording`

Stored camera footage.

| Field | Notes |
|---|---|
| `recording_status` | `recording`, `processing`, `completed`, `failed` |
| `is_chunked` | Chunked binary storage mode |
| `edit_start_time` / `edit_end_time` | Non-destructive trim markers |
| `viewed_by` | M2M — unique student view tracking |
| `classrooms` | M2M — share one recording to multiple classrooms |

**Key methods:** `generate_thumbnail()`, `apply_trim()`, `generate_chunked_thumbnail()`

##### `RecordingChunk`

Binary video chunk for large chunked recordings. Fields: `sequence`, `data` (BinaryField), `duration`.

##### `HeadCountLog`

Occupancy data per camera snapshot.

| Field | Notes |
|---|---|
| `head_count` | Number of people detected |
| `confidence_score` | Average detection confidence |
| `date` / `hour` | For day/time-wise filtering |
| `snapshot` | Optional annotated frame with bounding boxes |

##### `HeadCountSession`

Active head counting session per camera.

| Field | Notes |
|---|---|
| `status` | `active`, `stopped` |
| `capture_interval` | Seconds between captures |
| `total_captures` | Total snapshots taken |
| `average_head_count` / `max_head_count` / `min_head_count` | Session statistics |

#### Camera Microservice (Port 8008)

The camera service is a **separate Waitress process** that:
- Ingests RTSP / mobile camera feeds using OpenCV
- Runs the head-counting algorithm (`head_count_service.py`)
- Emits live MJPEG/HLS streams for in-browser viewing
- Communicates with Django via internal HTTP + shared `CAMERA_SERVICE_SECRET`
- Nginx proxies `/camera-service/` → `http://127.0.0.1:8008`

---

### 6.6 Video Editing Studio

**Location:** `video_editing/`

**Purpose:** Browser-based non-destructive video editor — multi-track audio, trim, split, rotate, resize, text captions, speed change, fade, and grayscale — all rendered asynchronously via FFmpeg.

#### Key Files

| File | Responsibility |
|---|---|
| `models.py` | `VideoProject`, `ProjectAsset`, `EditOperation` |
| `ffmpeg_utils.py` | FFmpeg command builders and wrappers |
| `timeline_compiler.py` | Timeline JSON → FFmpeg filtergraph compiler |
| `tasks.py` | Celery tasks for async render jobs |
| `views.py` | Editor UI + AJAX operation endpoints |

#### Data Models

##### `VideoProject`

One video editing workspace per teacher/user.

| Field | Notes |
|---|---|
| `original_file` | Original upload — **never modified**, kept for reset |
| `current_file` | Working copy that gets replaced each operation |
| `timeline_state` | JSON: clips, tracks, splits, overlays |
| `status` | `ready`, `processing`, `error` |
| `proxy_status` | Low-res proxy render status for browser preview |
| `duration_seconds` / `width` / `height` | Video metadata |
| `trim_start` / `trim_end` | Active trim range |
| `has_audio` | Whether video has audio track |

**Key properties:** `display_title`, `display_duration`, `working_file`, `working_file_url`, `clips_json`

##### `ProjectAsset`

Additional audio, video, or image files for multi-track editing.
Types: `video`, `audio`, `image`.

##### `EditOperation`

Full edit history log with undo/redo support.

| Operation | Description |
|---|---|
| `upload` | Initial file upload |
| `trim` | Cut in/out points |
| `mute` / `unmute` | Audio toggle |
| `volume` | Audio level adjustment |
| `merge` | Combine video clips |
| `text_overlay` | Burn-in caption / subtitle |
| `speed` | Playback rate change |
| `rotate` | Video rotation (90°, 180°, 270°) |
| `resize` | Output resolution change |
| `grayscale` | Color to black & white |
| `fade` | Fade in / fade out effect |
| `reset` | Revert to original upload |

Each operation stores:
- `parameters` — JSON bag of operation settings
- `video_file` — snapshot of the result for history display
- `active` — `False` = undone operation

---

### 6.7 RAG Workspace (AI Knowledge Base)

**Location:** `rag_workspace/`

**Purpose:** Retrieval-Augmented Generation (RAG) pipeline — extracts text from study materials (PDF, Word, notes), embeds them into a vector store, and enables semantic Q&A over classroom documents.

#### Key Files

| File | Responsibility |
|---|---|
| `services.py` | Embedding generation, vector search, LLM querying |
| `views.py` | REST endpoints for Q&A and document search |
| `models.py` | RAG session / query persistence |

#### Pipeline

```
StudyMaterial uploaded to classroom
          │
          ▼
Text extraction
  • PDF   → pypdf
  • Word  → python-docx
  • Notes → plaintext
          │
          ▼
Chunking → MaterialChunk records (indexed in meetings.models)
          │
          ▼
Embedding via AI_EMBEDDING_URL (nomic-embed-text)
          │
          ▼
Stored: embedding_vector (JSON) + rag_metadata
          │
          ▼ (at query time)
Student asks a question
          │
          ▼
Query embedding → Cosine similarity → Top-K chunks
          │
          ▼
LLM prompt via AI_LLM_URL (phi, llama, etc.)
          │
          ▼
Answer returned to student
```

#### Configuration

| Variable | Purpose |
|---|---|
| `AI_LLM_URL` | Ollama / Cloudflare tunnel endpoint for LLM generation |
| `AI_LLM_BEARER_TOKEN` | API key for LLM service |
| `AI_MODEL_NAME` | Model name (e.g., `phi:latest`) |
| `AI_EMBEDDING_URL` | Embedding service endpoint |
| `AI_EMBEDDING_MODEL` | Embedding model (e.g., `nomic-embed-text:latest`) |

---

### 6.8 Common Utilities

**Location:** `common/`

**Purpose:** Cross-app shared utilities — encryption field, file validation, soft-delete mixin, and audit logging.

#### Components

| Component | Description |
|---|---|
| `common/encryption.py` | `EncryptedTextField` — custom Django field for AES-256 encrypted text columns (used by `MeetingChat`) |
| `common/validators.py` | Magic-byte binary file signature validation for all uploads |
| `common/models.py` | `SoftDeleteMixin` — adds `is_deleted` + `deleted_at` to models without destroying data |

#### File Validation (Magic-Byte Checks)

All uploaded files are inspected at the **binary level** to prevent extension spoofing and web shell uploads:

| Validator | Allowed Formats |
|---|---|
| `validate_assignment_file` | PDF, Word (.docx), images, ZIP |
| `validate_assignment_submission_file` | PDF, Word, images, code files |
| `validate_video_file` | MP4, AVI, MOV, MKV, WebM |
| `validate_image_file` | JPEG, PNG, WebP, GIF |

---

## 7. Database Schema Summary

### Entity Relationship Overview

```
User (Django Auth)
 ├── UserProfile (1:1)            role, student_id, employee_id, bio
 ├── EmailVerificationOTP (1:N)   SHA-256 OTPs for email verification
 ├── UserAchievement (1:N)        badges/achievements
 ├── StudentFaceProfile (1:1)     encrypted biometric vector
 ├── AttendanceRecord (1:N)       attendance per meeting
 ├── QuizSubmission (1:N)         quiz results
 ├── AssignmentSubmission (1:N)   homework results
 └── VideoProject (1:N)           video editing projects

Classroom
 ├── ClassroomMembership (1:N)    student join requests + approval lifecycle
 ├── Meeting (1:N)
 │    ├── MeetingParticipant (1:N)
 │    ├── MeetingChat (1:N)        encrypted messages
 │    ├── MeetingAttendanceLog (1:N)
 │    ├── AttendanceRecord (1:N)
 │    ├── EngagementReport (1:1)
 │    ├── StudentEngagementSnapshot (1:N)
 │    ├── FaceRecognitionLog (1:N)
 │    ├── KickedParticipant (1:N)
 │    └── QuizSubmission (1:N)
 ├── Assignment (1:N)
 │    ├── AssignmentQuestionFile (1:N)
 │    └── AssignmentSubmission (1:N)
 │         └── AssignmentSubmissionFile (1:N)
 ├── Quiz (1:N)
 │    ├── Question (1:N)
 │    │    └── Choice (1:N)
 │    └── QuizSubmission (1:N)
 │         └── StudentAnswer (1:N)
 ├── StudyMaterial (1:N)
 │    └── MaterialChunk (1:N)     RAG text chunks + embeddings
 ├── MaterialUnit (1:N)           topic/unit folders
 ├── AttendanceSettings (1:1)
 ├── ClassSchedule (1:N)
 └── HeadCountLog (1:N)

Camera
 ├── CameraPermission (1:N)       teacher access grants
 └── CameraRecording (1:N)
      └── RecordingChunk (1:N)    binary storage for large recordings

HeadCountSession (1:N per camera)

VideoProject
 ├── ProjectAsset (1:N)           multi-track media files
 └── EditOperation (1:N)          full edit history log
```

---

## 8. User Roles & Permissions

| Role | Dashboard URL | Access Level |
|---|---|---|
| **Admin / Superuser** | `/admin/` | Full platform control |
| **Teacher** | `/teacher-dashboard/` | Classroom authority |
| **Student** | `/student-dashboard/` | Enrolled access |

### Detailed Capability Matrix

| Capability | Admin | Teacher | Student |
|---|---|---|---|
| Create/manage classrooms | ✅ | ✅ | ❌ |
| Host WebRTC meetings | ✅ | ✅ | ❌ |
| Approve/deny join requests | ✅ | ✅ | ❌ |
| View biometric data | ✅ only | ❌ | ❌ |
| Override attendance | ✅ | ✅ | ❌ |
| View CCTV cameras | ✅ | ✅ (if permitted) | ❌ |
| Access video editor | ✅ | ✅ | ❌ |
| Create assignments/quizzes | ✅ | ✅ | ❌ |
| Submit assignments/quizzes | ❌ | ❌ | ✅ |
| Join live classes | ❌ | hosts only | ✅ (if approved) |
| Complete face setup | ❌ | ❌ | ✅ |
| Watch lecture library | ✅ | ✅ | ✅ |
| Approve face reset requests | ✅ | ❌ | ❌ |
| Manage all users | ✅ | ❌ | ❌ |

### Per-Meeting Teacher Controls

- Mute/unmute individual participants
- Enable/disable individual video feeds
- Enable/disable screen sharing per participant
- Kick users (with configurable ban duration via `KickedParticipant`)
- Toggle global classroom-wide mute / camera-off / screenshare-off
- Put meeting to sleep / wake it up
- Launch quizzes mid-session

---

## 9. Environment Variables Reference

> Template: [`.env.example`](./.env.example) | Active config: [`.env`](./.env)

### Core Django

| Variable | Default | Required | Purpose |
|---|---|---|---|
| `SECRET_KEY` | — | ✅ | Django session and CSRF signing key |
| `DEBUG` | `False` | | Must be `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | ✅ | Comma-separated allowed hosts |
| `LOG_LEVEL` | `INFO` | | Logging verbosity |

### Database

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `postgres://edumi_admin:pass@127.0.0.1:5432/edumi_db` | Full PostgreSQL connection string |
| `POSTGRES_DB` | `edumi_db` | Database name |
| `POSTGRES_USER` | `edumi_admin` | PostgreSQL user |
| `POSTGRES_PASSWORD` | — | PostgreSQL password |

### Redis

| Variable | Default | Purpose |
|---|---|---|
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Channel layers and Celery broker |

### LiveKit WebRTC

| Variable | Default | Purpose |
|---|---|---|
| `LIVEKIT_URL` | `wss://<DOMAIN>/livekit-proxy` | Public WebRTC signaling endpoint |
| `LIVEKIT_INTERNAL_URL` | `ws://127.0.0.1:7880` | Internal LiveKit WS address |
| `LIVEKIT_INTERNAL_HTTP_URL` | `http://127.0.0.1:7880` | Internal LiveKit HTTP address |
| `LIVEKIT_API_KEY` | `devkey` | LiveKit API key |
| `LIVEKIT_API_SECRET` | — (min 32 chars) | LiveKit shared secret |

### Biometric / Face Recognition

| Variable | Default | Purpose |
|---|---|---|
| `FACE_ENCRYPTION_KEY` | — | Fernet Base64 key for 128-D vector encryption |
| `FACE_MATCH_THRESHOLD` | `0.50` | Max Euclidean distance threshold |
| `FACE_PRESENCE_DURATION` | `30` | Seconds of verified presence for "Present" |

**Generate a Fernet key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Camera Service

| Variable | Default | Purpose |
|---|---|---|
| `CAMERA_SERVICE_PORT` | `8008` | Port for the camera microservice |
| `CAMERA_SERVICE_URL` | `http://127.0.0.1:8008` | Internal microservice base URL |
| `CAMERA_SERVICE_SECRET` | — | Service-to-service auth token |

### Email (SMTP)

| Variable | Default | Purpose |
|---|---|---|
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_USE_TLS` | `True` | TLS encryption |
| `EMAIL_HOST_USER` | — | Sender email address |
| `EMAIL_HOST_PASSWORD` | — | App-specific password |
| `DEFAULT_FROM_EMAIL` | — | Display name + address in sent emails |
| `DEFAULT_DOMAIN` | `http://localhost:8002` | Base URL for email verification links |

### AI / RAG

| Variable | Purpose |
|---|---|
| `AI_LLM_URL` | LLM generation endpoint (Ollama via Cloudflare tunnel) |
| `AI_LLM_BEARER_TOKEN` | Bearer auth for LLM |
| `AI_MODEL_NAME` | LLM model name (e.g., `phi:latest`) |
| `AI_EMBEDDING_URL` | Embedding service endpoint |
| `AI_EMBEDDING_MODEL` | Embedding model name (e.g., `nomic-embed-text:latest`) |

### Multimedia Binaries

| Variable | Default | Purpose |
|---|---|---|
| `FFMPEG_BINARY` | `ffmpeg` | Path to FFmpeg binary |
| `FFPROBE_BINARY` | `ffprobe` | Path to FFprobe binary |

### Security / SSL

| Variable | Default | Purpose |
|---|---|---|
| `SECURE_SSL_REDIRECT` | `True` | Force HTTPS redirect |
| `SESSION_COOKIE_SECURE` | `True` | Secure-only session cookies |
| `CSRF_COOKIE_SECURE` | `True` | Secure-only CSRF cookies |
| `CSRF_TRUSTED_ORIGINS` | — | Comma-separated trusted origins |

---

## 10. Microservices & Port Matrix

| Service | Port | Protocol | Description |
|---|---|---|---|
| **Daphne (Main ASGI)** | `8002` | HTTPS / WSS | Primary app — UI, auth, API, WebSockets |
| **Camera Microservice** | `8008` | HTTP | RTSP ingestion, head counting, streaming |
| **LiveKit Signaling** | `7880` | HTTP / WS | WebRTC session creation & room coordination |
| **LiveKit RTC Media** | `7881` | TCP | WebRTC media TCP transport |
| **LiveKit RTC Media** | `7882` | UDP | WebRTC media UDP transport |
| **LiveKit UDP Range** | `50000–60000` | UDP | High-concurrency peer media streams |
| **Redis** | `6379` | TCP | Channel layers + Celery task broker |
| **PostgreSQL** | `5432` | TCP | Relational database |
| **Nginx** | `443` / `80` | HTTPS / HTTP | Reverse proxy, SSL, static files |

---

## 11. Deployment Guide

### Prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| OS | Ubuntu 20.04/22.04/24.04 or Windows 10/11 | Ubuntu recommended for production |
| Python | 3.11+ | With pip and venv |
| FFmpeg + FFprobe | 6.0+ | Must be in system `PATH` |
| Redis | 6.0+ / 7.0+ | Required for Celery + Channels |
| LiveKit Server | 1.5+ | Binary in `livekit-bin/` or via Docker |
| PostgreSQL | 14+ | Strongly recommended over SQLite |
| RAM | 16 GB+ | For concurrent AI + WebRTC processing |

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/GAuravgiy87/Edumi2.git
cd Edumi2

# 2. Copy and edit environment file
cp .env.example .env
nano .env   # or edit with your preferred editor

# 3. Generate Fernet key for biometric encryption
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# → Paste the output value into FACE_ENCRYPTION_KEY in .env

# 4. Create Python virtual environment
python -m venv venv
source venv/bin/activate      # Linux / macOS
.\venv\Scripts\activate        # Windows PowerShell

# 5. Install all dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 6. Run database migrations
python manage.py migrate

# 7. Create admin superuser
python manage.py createsuperuser

# 8. Collect static files
python manage.py collectstatic --noinput
```

### Launch Options

#### Option A — Windows (Development / Testing)

```powershell
# Automated one-click launcher
.\start_app.ps1
# Or double-click: start_app.bat
```

Resolves LAN IP, starts Daphne, Camera Service, LiveKit, and Redis.

- **Local:** `https://localhost:8002`
- **LAN:** `https://<YOUR-LAN-IP>:8002`

#### Option B — Ubuntu Server (Production)

```bash
sudo bash deploy.sh \
  --domain edumi.yourcollege.ac.in \
  --email admin@yourcollege.ac.in
```

Automated orchestrator: installs dependencies, configures Nginx, sets up systemd services, provisions Let's Encrypt SSL.

#### Option C — Docker Compose

```bash
docker compose up -d --build
```

### Diagnostic Tools

```bash
# Django system health check
python manage.py check

# Run test suite
python manage.py test

# Test SMTP email delivery
python scripts/test_smtp.py student@college.ac.in --verbose

# Generate self-signed SSL certificate
python scripts/generate_ssl_cert.py

# Live health endpoint
curl -k https://localhost:8002/health/
```

```powershell
# Windows: Add firewall rules for ports 8002, 8008, 7880–7882
.\scripts\allow_firewall.ps1

# Windows: Trust self-signed certificate in Windows Certificate Store
.\scripts\trust_ssl_cert.ps1
```

---

## 12. Security & Privacy Architecture

| Mechanism | Implementation |
|---|---|
| **Biometric Encryption** | Fernet (AES-128-CBC + HMAC-SHA256) applied to 128-D face vectors in memory before writing to DB |
| **Zero Raw Photo Retention** | Face images computed in memory → embedding extracted → raw image reference discarded |
| **Integrity Verification** | SHA-256 checksum stored alongside encrypted vector for tamper detection on decrypt |
| **Chat Encryption** | `EncryptedTextField` (AES-256) for all `MeetingChat` messages at rest |
| **Upload Security** | Binary magic-byte inspection of all uploads prevents extension spoofing and web shell uploads |
| **Rate Limiting** | Sliding-window Redis-backed rate limiters on all auth endpoints (`ratelimit.py`) |
| **OTP Security** | SHA-256 hashed 6-digit codes; single-use; TTL expiry; per-user attempt counter |
| **Service Isolation** | Camera processing and FFmpeg rendering run in separate processes (Waitress + Celery) |
| **HTTPS Enforcement** | Nginx + Daphne handle SSL termination; all cookies are secure-only in production |
| **CSRF Protection** | Django CSRF middleware + configurable trusted origins |
| **Consent Tracking** | `consent_version` and `consent_at` fields for GDPR/DPDP/FERPA compliance |
| **Soft Deletes** | `SoftDeleteMixin` prevents irreversible user data loss on record deletion |
| **Per-Participant ACL** | Teachers control individual audio/video/screenshare permissions per participant in real time |

---

## 13. Repository Structure

```
Edumi2/
│
├── accounts/                   # Auth, profiles, OTPs, rate-limiting, messaging, notifications
│   ├── models.py               # UserProfile, EmailVerificationOTP, UserAchievement
│   ├── messaging_models.py     # Conversation, Message
│   ├── notification_models.py  # Notification + delivery utilities
│   ├── email_tokens.py         # OTP generation + signed fallback tokens
│   ├── ratelimit.py            # Sliding-window Redis rate limiter
│   ├── identity.py             # Cross-module identity resolution
│   ├── admin_services.py       # Admin user management logic
│   └── services.py             # Registration, login, profile service layer
│
├── meetings/                   # LiveKit WebRTC classrooms + study materials + RAG
│   ├── models.py               # Classroom, Meeting, MeetingChat, StudyMaterial, MaterialChunk
│   ├── consumers.py            # WebSocket event broker for live meeting state
│   ├── services.py             # LiveKit token + room management
│   └── livekit_proxy.py        # WebSocket proxy to LiveKit
│
├── attendance/                 # YuNet + SFace biometric pipeline + attendance ledgers
│   ├── models.py               # StudentFaceProfile, AttendanceRecord, EngagementReport
│   ├── face_service.py         # Core face detection + recognition
│   ├── encryption_service.py   # Fernet encrypt/decrypt for face vectors
│   ├── engagement_service.py   # Per-student emotion scoring
│   ├── consumers.py            # WebSocket consumer for face verification
│   └── face_tracking_consumer.py
│
├── assignments/                # Homework assignments, timed quizzes, auto-grading
│   └── models.py               # Assignment, Quiz, Question, Choice, Submission, StudentAnswer
│
├── cameras/                    # Campus RTSP CCTV, recording engine, head counting
│   ├── models.py               # Camera, CameraRecording, HeadCountLog, HeadCountSession
│   ├── head_count_service.py   # OpenCV-based crowd counting
│   └── recording_engine.py     # RTSP recording pipeline
│
├── camera_service/             # Dedicated OpenCV streaming microservice (port 8008)
│
├── mobile_cameras/             # Mobile IP Webcam streaming
│
├── video_editing/              # Non-destructive browser video editor
│   ├── models.py               # VideoProject, ProjectAsset, EditOperation
│   ├── ffmpeg_utils.py         # FFmpeg command builders
│   ├── timeline_compiler.py    # JSON timeline → FFmpeg filtergraph
│   └── tasks.py                # Celery async render tasks
│
├── rag_workspace/              # Academic document search + AI knowledge base
│   ├── services.py             # Embedding generation, vector search, LLM querying
│   └── views.py                # Q&A REST endpoints
│
├── videos/                     # On-demand lecture library with multi-bitrate HLS
│
├── common/                     # Shared: encryption, validators, SoftDeleteMixin
│
├── school_project/             # Root Django settings, ASGI/WSGI, URL routing
│   ├── settings.py             # Main Django configuration
│   ├── asgi.py                 # ASGI entrypoint (Daphne)
│   ├── urls.py                 # Root URL router
│   └── celery.py               # Celery app configuration
│
├── templates/                  # HTML5 templates (responsive, dark mode)
├── static/                     # CSS, JS, ONNX models, face-api.js
├── scripts/                    # SSL generation, firewall, SMTP test utilities
├── config/                     # livekit.yaml and microservice configs
├── nginx/                      # Nginx server block configurations
│
├── Dockerfile                  # Container image definition
├── docker-compose.yml          # Multi-service container orchestration
├── deploy.sh                   # Single-file Ubuntu production deployment script
├── start_app.bat               # Windows double-click launcher
├── start_app.ps1               # PowerShell multi-service orchestrator
├── run_ssl_server.py           # HTTPS dev server runner
└── requirements.txt            # Production Python dependencies (83 packages)
```

---

## 14. Authors & License

**Copyright © 2026 EduMi Systems. All Rights Reserved.**

This software is licensed under the **EduMi Commercial Enterprise Software License Agreement**.
See [`LICENSE`](./LICENSE) for full terms, conditions, and usage restrictions.

### Core Maintainers

| Name | GitHub Handle |
|---|---|
| **Gaurav Singh** | [@GAuravgiy87](https://github.com/GAuravgiy87) |
| **Tarun Kumar** | [@tarunkumar-sys](https://github.com/tarunkumar-sys) |

---

*This document was generated from live source code analysis of the Edumi2 repository.*
*It serves as the authoritative reference for all EduMi development, integration, and administration tasks.*
