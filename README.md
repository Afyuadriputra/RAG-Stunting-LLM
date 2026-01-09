# 🥗 StuntingBot: Asisten Konsultasi Gizi Anak Berbasis AI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-REST-092E20?style=for-the-badge&logo=django)
![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react)
![RAG](https://img.shields.io/badge/AI-RAG%20%2B%20Vision-orange?style=for-the-badge)

**StuntingBot** adalah sistem konsultasi kesehatan cerdas yang dirancang untuk menangani masalah gizi anak (stunting) menggunakan pendekatan **Multimodal AI**. Sistem ini menggabungkan data pengguna, analisis visual (foto fisik anak), dan mesin **Hybrid RAG (Retrieval-Augmented Generation)** yang mengambil referensi medis dari database lokal maupun jurnal akses terbuka (Open Access) secara real-time.

---

## 🚀 Fitur Unggulan

* **🧠 Advanced RAG Pipeline**: Menggunakan `ChromaDB` sebagai penyimpanan vektor dan `sentence-transformers` untuk embedding yang akurat.
* **👁️ Integrasi Computer Vision**: Menganalisis foto anak untuk mendeteksi tanda-tanda visual malnutrisi menggunakan LLM Vision, hasil analisis disimpan sebagai konteks tambahan.
* **🌐 Evidence Gating (Smart Fetch)**:
    * Sistem mengevaluasi kualitas bukti yang ditemukan di database lokal.
    * **Jika bukti lemah**, sistem secara otomatis mencari, mengunduh, dan mempelajari (ingest) jurnal medis eksternal (dari PMC, Semantic Scholar, OpenAlex).
* **📚 Sitasi Terverifikasi**: Setiap jawaban dilengkapi dengan sitasi yang dapat diklik, mengarah langsung ke sumber PDF atau halaman web jurnal.
* **⚡ Arsitektur Modern**: Menggunakan Django REST Framework (Backend) dan React + Vite (Frontend) yang terpisah.

---

## 🏗️ Arsitektur Sistem

### 1. Backend (Django REST)
Direktori: `backend/stuntingbot`
Menangani logika utama aplikasi:
* **App `consultations`**: Mengelola CRUD data konsultasi dan orkestrasi proses RAG.
* **App `ragapi`**: Menangani ingesti dokumen, retrieval vektor, pencarian jurnal eksternal, dan pipeline visi.
* **Alur Proses**:
    1.  **Analisis Visi**: Foto diubah ke URL data -> LLM Vision -> Output teks `vision_findings`.
    2.  **Retrieval**: Query ke ChromaDB menggunakan Pertanyaan User + Temuan Visual.
    3.  **Gating**: Cek skor relevansi. Jika rendah -> Fetch Sumber Eksternal -> Ingest -> Re-rank.
    4.  **Generation**: LLM menjawab berdasarkan Konteks + Sitasi.

### 2. Frontend (React + Vite)
Direktori: `stuntingbot-wellness`
* Antarmuka pengguna (UI) yang bersih dan responsif.
* Menampilkan status konsultasi secara *real-time*.
* Menampilkan jawaban terformat dengan sitasi aktif.

---

## 🛠️ Teknologi yang Digunakan

| Komponen | Teknologi |
| :--- | :--- |
| **Backend Framework** | Django REST Framework (DRF) |
| **Frontend Framework** | React.js (Build Tool: Vite) |
| **Vector Database** | ChromaDB (Persistent Client) |
| **LLM Orchestration** | OpenRouter API (Akses ke berbagai model LLM) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Sumber Eksternal** | PubMed Central (PMC), Semantic Scholar, OpenAlex |

---

## 🔌 Endpoint API Utama

Sistem menyediakan endpoint berikut melalui DRF:

| Method | Endpoint | Deskripsi |
| :--- | :--- | :--- |
| `POST` | `/api/photos/upload/` | Upload foto anak (Return `photo_id`). |
| `POST` | `/api/consultations/` | Membuat sesi konsultasi baru (data anak + pertanyaan). |
| `POST` | `/api/consultations/{id}/process/` | **Pemicu RAG + Vision**. Menjalankan analisis & generasi jawaban. |
| `GET` | `/api/consultations/{id}/` | Mengambil detail hasil (Jawaban, Sitasi, Temuan Visual). |
| `POST` | `/api/rag/ingest/` | Melakukan ingesti dokumen eksternal secara manual. |

---

## 💻 Instalasi & Pengaturan

### Prasyarat
* Python 3.10+
* Node.js & npm
* API Key OpenRouter

### 1. Setup Backend
```bash
# Masuk ke folder backend
cd backend/stuntingbot

# Buat virtual environment
python -m venv venv
# Aktifkan (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Jalankan Migrasi Database
python manage.py migrate

# Jalankan Server
python manage.py runserver
2. Setup Frontend
Bash

# Masuk ke folder frontend
cd stuntingbot-wellness

# Install dependencies
npm install

# Jalankan Server Development
npm run dev
3. Variabel Lingkungan (.env)
Buat file .env di root folder backend:

Cuplikan kode

OPENROUTER_API_KEY=api_key_anda_disini
CHROMA_DB_PATH=./chroma_db
DEBUG=True
📝 Alur Penggunaan
Upload Foto: Pengguna mengunggah foto anak (opsional). Backend memproses ini melalui Vision Pipeline.

Kirim Pertanyaan: Pengguna memasukkan data anak (usia, BB, TB) dan pertanyaan keluhan.

Pemrosesan:

Backend menganalisis foto.

Mencari konteks medis relevan di ChromaDB.

(Auto-fetch jurnal eksternal jika bukti kurang kuat).

Menghasilkan jawaban komprehensif.

Hasil: Pengguna menerima jawaban lengkap dengan saran medis dan sitasi sumber.

📄 Lisensi
Proyek ini dikembangkan untuk tujuan akademis (Skripsi/Tugas Akhir). Copyright © 2024 - Sekarang.
