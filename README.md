# 📊 SlidePDF Studio — Professional PPTX to PDF Converter Suite

<p align="center">
  <img src="assets/icon.png" width="128" height="128" alt="SlidePDF Studio Icon" />
</p>

<p align="center">
  <b>A modern, cross-platform PowerPoint to PDF converter software.</b><br>
  Featuring a sleek Desktop GUI (CustomTkinter), powerful CLI (Rich), multi-engine conversion architecture, batch processing, slide range filtering, and PDF merging.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/CI-GitHub%20Actions-brightgreen?style=flat-square" />
  <img src="https://img.shields.io/badge/Build-PyInstaller%20Ready-purple?style=flat-square" />
</p>

---

## 🌟 Fitur Utama (Key Features)

1. **Dukungan Format Luas (Multi-Format Support)**:
   - 📽️ **Presentasi**: `.pptx`, `.ppt` (legacy), `.pptm` (macro), `.ppsx`/`.pps` (slideshow), `.potx`, dan `.odp` (OpenDocument Impress).
   - 🖼️ **Gambar ke Slide PDF**: `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff` (dikonversi otomatis menjadi halaman PDF beresolusi tajam).
   - 📄 **Dokumen Kantor**: `.docx`, `.doc`, `.odt`, `.rtf` (didukung penuh via LibreOffice engine).
   - 📑 **Batch Mixed Merge**: Kamu bisa menggabungkan presentasi PowerPoint DAN gambar-gambar slide menjadi 1 file PDF master terpadu!

2. **Multi-Engine Conversion Architecture**:
   - ⚡ **LibreOffice Engine**: Menghasilkan PDF berbasis vector dengan rendering OpenXML presisi tinggi via daemon headless (`soffice`).
   - ⚡ **Microsoft Office COM Engine**: Otomasi native PowerPoint di Windows untuk kualitas 100% pixel-perfect.
   - 📦 **Native Python Engine**: Engine bawaan pure-Python (berbasis `python-pptx`, `Pillow`, dan `ReportLab`). Siap konversi langsung **tanpa wajib install LibreOffice atau Microsoft Office**!
   - 🤖 **Auto-Detect Engine**: Otomatis mendeteksi engine terbaik di sistem komputer pengguna.

2. **Modern Desktop GUI (CustomTkinter)**:
   - Antarmuka modern dengan Dark Mode & Light Mode switch.
   - Sistem antrean (Queue Table) dengan indikator status file, progress bar per file, ukuran, dan jumlah slide.
   - Background worker multi-threading sehingga aplikasi **tidak pernah freeze/not-responding** saat mengonversi file besar.
   - Expandable Log Console Drawer untuk memantau proses secara transparan.

3. **Batch Processing & Master PDF Merging**:
   - Konversi banyak file sekaligus (folder scan rekursif).
   - Mode **Merge All into 1 PDF**: Menggabungkan seluruh presentasi dalam antrean menjadi 1 file PDF lengkap dengan bookmark/outline per presentasi.

4. **Kontrol Halaman & Kompresi**:
   - Filter halaman/slide spesifik (contoh: `1-5, 8, 10-12`).
   - Pilihan kualitas: **Standard (High-Res Vector)** vs **Compressed (Optimasi Web & Email)**.

5. **Powerful Command-Line Interface (CLI)**:
   - Perintah terminal lengkap dengan progress bar warna-warni (`rich`).
   - Tool `slidepdf doctor` untuk mengecek status engine dan kesiapan sistem.

6. **Siap Dipaketkan Menjadi Software Standalone (`.exe` / Binary)**:
   - Dilengkapi script PyInstaller otomatis (`scripts/build_executable.py`) untuk membuat file executable portable.

---

## ⚡ Shortcut Super Keren (Super Cool Shortcuts)

SlidePDF Studio sudah diintegrasikan langsung ke sistem kamu dengan 4 tingkatan shortcut:

### 1. File Executable Langsung di Workspace
Executable standalone (portable single-file) sekarang tersedia langsung di root workspace:
- 🚀 **[`/workspace/SlidePDF-Studio`](file:///workspace/SlidePDF-Studio)** (bisa langsung diklik 2x atau dijalankan `./SlidePDF-Studio`)
- 📦 Lokasi binary asli: [`/workspace/Projects/pptx-to-pdf-converter/dist/SlidePDF-Studio`](file:///workspace/Projects/pptx-to-pdf-converter/dist/SlidePDF-Studio)

### 2. Global Terminal Command (Dari Folder Mana Saja)
Karena sudah dimasukkan ke `$PATH`, kamu bisa mengetik perintah berikut di terminal mana pun:
- `slidepdf` — Langsung membuka Desktop GUI!
- `slidepdf presentasi.pptx` — Langsung konversi `presentasi.pptx` ke PDF secara instan!
- `pptx2pdf presentasi.pptx` — Alias shortcut cepat untuk konversi terminal.

### 3. Integrasi Klik Kanan File Manager (Nautilus Scripts)
Kamu bisa konversi file tanpa buka aplikasi atau terminal:
1. Buka File Manager (Nautilus).
2. Klik kanan file `.pptx` mana pun.
3. Pilih **Scripts** ➔ **`Convert to PDF (SlidePDF)`**.
4. Sistem akan otomatis mengonversi dan menampilkan desktop notification saat selesai! 🔔

### 4. Keyboard Shortcuts di Dalam Aplikasi GUI
| Shortcut | Fungsi |
|---|---|
| <kbd>Ctrl</kbd> + <kbd>O</kbd> | Tambah Berkas PPTX (`+ Add Files`) |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>O</kbd> | Tambah Seluruh Folder (`+ Add Folder`) |
| <kbd>Ctrl</kbd> + <kbd>Enter</kbd> | Mulai Konversi (`Start Conversion`) |
| <kbd>Esc</kbd> | Batalkan Konversi Sedang Berjalan |
| <kbd>Ctrl</kbd> + <kbd>L</kbd> | Buka/Tutup Drawer Console Log |
| <kbd>Ctrl</kbd> + <kbd>D</kbd> | Bersihkan Antrean (`Clear Queue`) |
| <kbd>Ctrl</kbd> + <kbd>Q</kbd> | Keluar dari Aplikasi |

### 5. Menu Aplikasi Desktop (App Launcher / Super Key)
Aplikasi sudah terdaftar di sistem (`~/.local/share/applications/slidepdf.desktop`). Cukup tekan tombol `Super` (Windows key) di keyboard dan ketik **SlidePDF Studio**!

---

## 📁 Struktur Direktori Proyek

```text
slidepdf/
├── .github/workflows/          # CI/CD otomatis (testing & release build)
│   ├── ci.yml                  # Automated pytest di Linux & Windows
│   └── release.yml             # Auto-build executable saat git tag release
├── pyproject.toml              # Standar packaging PEP 518/621
├── requirements.txt            # Dependensi Python
├── Makefile                    # Shortcut developer (make install, make test, dll)
├── install.sh                  # Skrip installer 1-klik untuk integrasi sistem
├── CONTRIBUTING.md             # Panduan kontributor open-source
├── README.md                   # Dokumentasi lengkap
├── ARCHITECTURE.md             # Arsitektur & desain teknis mesin
├── LICENSE                     # Lisensi open-source (MIT)
├── run.sh                      # Launcher 1-klik untuk Linux & macOS
├── run.bat                     # Launcher 1-klik untuk Windows
├── slidepdf.desktop            # File shortcut aplikasi desktop Linux
├── assets/
│   ├── icon.png                # Icon aplikasi resolusi tinggi (PNG)
│   └── icon.svg                # Icon aplikasi format vektor (SVG)
├── src/slidepdf/               # Sumber kode aplikasi
├── scripts/                    # Skrip build & tools
├── samples/                    # Contoh berkas presentasi untuk uji coba
└── tests/                      # Rangkaian pengujian unit & integrasi (Pytest)
```

---

## 🚀 Panduan Penggunaan Cepat (Quickstart)

### 1. Instalasi Otomatis (Rekomendasi Linux)
Kamu bisa menggunakan installer 1-klik untuk memasang dependensi, shortcut aplikasi desktop, integrasi klik-kanan Nautilus, dan command terminal:

```bash
cd /workspace/Projects/slidepdf
bash install.sh
```

### 2. Instalasi Manual

Gunakan `uv` (sangat cepat) atau `pip` standar:

```bash
# Masuk ke direktori proyek
cd /workspace/Projects/slidepdf

# Buat virtual environment
uv venv
source .venv/bin/activate   # Di Linux/macOS
# atau di Windows: .venv\Scripts\activate

# Install dependensi
uv pip install -r requirements.txt
```
uv pip install -r requirements.txt
```

---

### 2. Menjalankan Aplikasi Desktop GUI

Cukup jalankan script launcher:

```bash
# Linux / macOS:
./run.sh

# Windows:
run.bat

# Atau via Python:
python -m slidepdf.app
```

---

### 3. Menggunakan Command-Line Interface (CLI)

SlidePDF Studio menyediakan antarmuka terminal profesional:

#### a. Cek Kesiapan Sistem & Engine (Diagnostics)
```bash
python -m slidepdf.cli doctor
```

Output:
```text
                     System Environment & Available Engines                     
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component            ┃ Status / Detection        ┃ Details                   ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Operating System     │ Detected                  │ Linux (x86_64)            │
│ Best Engine (Auto)   │ Recommended               │ Native Python Engine      │
│ Native Python Engine │ Available (Bundled)       │ Bundled pure-Python       │
│ LibreOffice Engine   │ Ready / Optional          │ High-fidelity vector      │
│ MS Office COM Engine │ Windows Only              │ Native COM Automation     │
└──────────────────────┴───────────────────────────┴───────────────────────────┘
```

#### b. Konversi File Tunggal
```bash
# Konversi standar
python -m slidepdf.cli convert presentation.pptx -o output.pdf

# Konversi hanya slide 1 sampai 3 dan slide 5:
python -m slidepdf.cli convert presentation.pptx -o output.pdf --slides 1-3,5

# Menggunakan mode kompresi (ukuran berkas lebih hemat):
python -m slidepdf.cli convert presentation.pptx -o output.pdf --compress

# Membuka langsung PDF setelah selesai:
python -m slidepdf.cli convert presentation.pptx --open
```

#### c. Batch Processing (Banyak File Sekaligus)
```bash
# Konversi semua berkas PPTX di suatu folder:
python -m slidepdf.cli batch ./slides/ -o ./output/

# Batch konversi DAN gabungkan semuanya menjadi 1 file master PDF:
python -m slidepdf.cli batch ./slides/ -o ./output/ --merge --merge-name "Laporan_Lengkap.pdf"
```

---

## 📦 Menjadikan Software Standalone (`.exe` / Linux Binary)

Software ini sudah siap dipaketkan menjadi executable mandiri menggunakan script `build_executable.py`:

```bash
# Buat standalone distribution folder:
python scripts/build_executable.py

# Atau buat single-file executable tunggal:
python scripts/build_executable.py --onefile
```

Hasil build akan otomatis tersedia di folder `dist/`:
- **Windows**: `dist/SlidePDF-Studio/SlidePDF-Studio.exe` (atau single-file `.exe`)
- **Linux**: `dist/SlidePDF-Studio/SlidePDF-Studio` (ELF executable mandiri)

Pengguna akhir dapat langsung klik 2x pada file `.exe` tersebut dan aplikasi desktop langsung terbuka tanpa perlu install Python!

---

## 🧪 Pengujian Otomatis (Automated Tests)

Jalankan rangkaian unit & integration tests dengan `pytest`:

```bash
PYTHONPATH=src pytest -v
```

Hasil uji:
```text
tests/test_cli.py::test_cli_parser_defaults PASSED                       [  6%]
tests/test_cli.py::test_cli_doctor_execution PASSED                      [ 13%]
tests/test_engines.py::test_detector_defaults PASSED                     [ 20%]
tests/test_engines.py::test_detector_native_always_available PASSED      [ 26%]
tests/test_engines.py::test_diagnostics_structure PASSED                 [ 33%]
tests/test_merger.py::test_pdf_merger PASSED                             [ 40%]
tests/test_models.py::test_engine_type_from_string PASSED                [ 46%]
tests/test_models.py::test_conversion_job_formatting PASSED              [ 53%]
tests/test_models.py::test_conversion_options_defaults PASSED            [ 60%]
tests/test_native_converter.py::test_native_converter_full_presentation PASSED [ 66%]
tests/test_native_converter.py::test_native_converter_slide_range PASSED [ 73%]
tests/test_native_converter.py::test_native_converter_compression PASSED [ 80%]
tests/test_utils.py::test_parse_slide_range_all PASSED                   [ 86%]
tests/test_utils.py::test_parse_slide_range_specific PASSED              [ 93%]
tests/test_utils.py::test_get_default_output_path PASSED                 [100%]
============================== 15 passed in 0.29s ==============================
```

---

## 💡 Tips & Rekomendasi Mesin Konversi

- **Apakah wajib install LibreOffice atau Microsoft Office?**
  **Tidak wajib!** SlidePDF Studio telah dilengkapi dengan **Native Python Engine** bawaan yang langsung bekerja di semua sistem operasi tanpa ketergantungan software luar.
- **Kapan sebaiknya menggunakan LibreOffice atau MS Office?**
  Jika presentasi memiliki animasi vektor kompleks, SmartArt bertingkat, atau font tipografi berpemilik Microsoft khusus, LibreOffice / MS Office akan memberikan representasi visual 100% identik dengan aplikasi aslinya.

---

## 📄 Lisensi
SlidePDF Studio dirilis di bawah lisensi [MIT License](LICENSE). Bebas digunakan, dimodifikasi, dan didistribusikan untuk keperluan pribadi maupun komersial.
