# ScribeDesk Database Design

## 1. Identity & Auth
### `users`
Core table for doctors. Plan selection is omitted for MVP; all users start with default access.
* `id`: UUID (PK)
* `email`: String (Unique)
* `password_hash`: String
* `first_name`: String
* `last_name`: String
* `signature_url`: String (S3 path to PNG signature)
* `dob`: Date
* `gender`: String
* `speciality`: String
* `created_at`: DateTime
* `updated_at`: DateTime

### `clinics`
Clinic details linked to a doctor.
* `id`: UUID (PK)
* `user_id`: UUID (FK -> users.id)
* `name`: String
* `street`: String
* `city`: String
* `state`: String
* `pincode`: String
* `country`: String
* `address`: Text
* `logo_url`: String (S3 path)

---

## 2. Clinical Data
### `patients`
* `id`: UUID (PK)
* `user_id`: UUID (FK -> users.id)
* `full_name`: String
* `email`: String
* `identifier`: String (MRN or ID)
* `date_of_birth`: Date
* `gender`: String
* `blood_group`: String

### `sessions` (Replaces Consultations)
The primary unit of work for the Scribe.
* `id`: UUID (PK)
* `user_id`: UUID (FK -> users.id)
* `patient_id`: UUID (FK -> patients.id, Nullable)
* `title`: String (Auto-generated on first stop)
* `description`: Text (Auto-generated on first stop)
* `status`: Enum (`active`, `completed`)
* `total_audio_seconds`: Integer (Sum of all closed segments)
* `current_segment_start`: DateTime (Set when WS connects, Null when idle)
* `clinical_summary`: Text (Markdown)

---

## 3. The Timeline (Unified Log)
### `session_timeline`
Stores interleaved events and transcripts in chronological order.
* `id`: UUID (PK)
* `session_id`: UUID (FK -> sessions.id)
* `type`: Enum (`transcript`, `event`)
* `event_type`: Enum (`started`, `stopped`, `resumed`, `None`)
* `content`: Text (The actual words or event description)
* `speaker_id`: Integer (Null for events)
* `relative_seconds`: Integer (Seconds from the start of the total session duration)
* `created_at`: DateTime (Absolute wall-clock time)

---

## 4. Reports & Templates
### `templates`
* `id`: UUID (PK)
* `name`: String
* `root_type`: Enum (`notes`, `letters`, `prescription`)
* `sub_type`: Enum (`soap`, `referral`, `discharge`, etc.)
* `content`: Text (Prompt instructions/structure)
* `is_system`: Boolean (True for seeded templates)
* `user_id`: UUID (FK -> users.id, Null for system templates)

### `reports`
* `id`: UUID (PK)
* `session_id`: UUID (FK -> sessions.id)
* `template_id`: UUID (FK -> templates.id)
* `title`: String
* `content`: Text (Final Markdown)
* `metadata`: JSONB (Stores structured data like prescriptions: `[{name, dosage, ...}]`)
* `is_signed`: Boolean (Default: False)
* `signed_at`: DateTime
* `content_hash`: String (SHA-256 fingerprint for verification)
