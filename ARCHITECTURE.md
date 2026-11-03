# SlidePDF Studio — Technical Architecture & Engine Design

This document details the software architecture, design patterns, coordinate transformations, and thread model of **SlidePDF Studio**.

---

## 1. High-Level System Architecture

SlidePDF Studio is structured into three clean, decoupled layers:

```
┌─────────────────────────────────────────────────────────────┐
│                     Presentation Layer                      │
│   ┌──────────────────────────────┬───────────────────────┐  │
│   │   Desktop GUI (CustomTkinter)│  Rich CLI (argparse)  │  │
│   └──────────────┬───────────────┴───────────┬───────────┘  │
└──────────────────┼───────────────────────────┼──────────────┘
                   │                           │
┌──────────────────▼───────────────────────────▼──────────────┐
│                    Orchestration Layer                      │
│   ┌──────────────────────────────────────────────────────┐  │
│   │                 ConversionManager                    │  │
│   │   - Job Queue Coordinator                            │  │
│   │   - Background Thread Lifecycle                      │  │
│   │   - Status Callbacks & Cancellation                  │  │
│   └──────────────┬───────────────────────────┬───────────┘  │
│                  │                           │              │
│   ┌──────────────▼────────┐         ┌────────▼───────────┐  │
│   │    EngineDetector     │         │   PDFMergerUtil    │  │
│   │ (Health & Diagnostics)│         │(Master PDF Stitch) │  │
│   └──────────────┬────────┘         └────────────────────┘  │
└──────────────────┼──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                   Conversion Engine Layer                   │
│   ┌───────────────────┬───────────────────┬──────────────┐  │
│   │ LibreOfficeEngine │  MSOfficeEngine   │ NativeEngine │  │
│   │ (Headless daemon) │(Windows COM / OLE)│(Pure Python) │  │
│   └───────────────────┴───────────────────┴──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Multi-Engine Strategy & Resolution

Converting `.pptx` (ECMA-376 OpenXML) to PDF with precision is notoriously complex due to proprietary Office drawingML shapes, animations, custom vector fonts, and text layout metrics. SlidePDF Studio solves this using a **Trier-based Adaptive Fallback Strategy**:

| Engine | Priority | Platform | Fidelity | Requirements |
|---|---|---|---|---|
| **Microsoft Office COM** | 1 (on Windows) | Windows | 100% (Pixel Perfect) | Microsoft PowerPoint |
| **LibreOffice Headless** | 1 (Linux/macOS) / 2 (Win) | Cross-Platform | High Vector Fidelity | `soffice` / `libreoffice` |
| **Native Python Engine** | Fallback / Standalone | Universal | Standard Vector + Images | Zero external dependencies |

### Resolution Logic (`EngineDetector.get_best_engine`):
1. **Windows**: If Microsoft PowerPoint is registered in COM registry (`winreg.HKEY_CLASSES_ROOT\PowerPoint.Application`), dispatch to `MSOfficeEngine`.
2. **Linux & macOS**: If `soffice` / `libreoffice` binary exists on PATH or in standard paths (`/usr/bin/soffice`, `/Applications/LibreOffice.app/Contents/MacOS/soffice`), dispatch to `LibreOfficeEngine`.
3. **Fallback**: If no office suite exists, cleanly fall back to `NativePythonEngine` without crashing or throwing missing executable errors.

---

## 3. Native Python Engine Mechanics (`native.py`)

The native engine translates PPTX OpenXML constructs directly into Adobe PDF primitives using `reportlab.pdfgen.canvas.Canvas`:

### 3.1 Coordinate System Transformation
PPTX OpenXML uses a top-left origin:
- $X=0$: Left edge
- $Y=0$: Top edge, increasing downwards.

Adobe PDF / PostScript uses a bottom-left origin:
- $X=0$: Left edge
- $Y=0$: Bottom edge, increasing upwards.

To render a bounding box at $(X_{pptx}, Y_{pptx})$ with dimensions $(W_{pt}, H_{pt})$ on a slide of height $H_{slide}$:
$$Y_{pdf} = H_{slide} - (Y_{pptx} + H_{pt})$$

### 3.2 Slide Background & Elements
1. **Background**: Renders solid RGB color fills or defaults to `#FFFFFF`.
2. **Text Frames & Runs**:
   - Calculates font metrics and point sizes.
   - Converts RGB colors (`pptx.dml.color.RGBColor` $\rightarrow$ `reportlab.lib.colors.Color`).
   - Implements automated word wrapping within bounding box limits.
   - Supports text alignments (`Left`, `Center`, `Right`).
3. **Pictures**:
   - Extracts raw byte blobs from slide shape parts (`shape.image.blob`).
   - Loads into PIL (`Image.open(io.BytesIO(blob))`).
   - If `quality == COMPRESSED`, applies Lanczos downsampling and optimized JPEG/PNG compression.
   - Draws onto the PDF canvas preserving spatial bounding boxes.
4. **Tables**:
   - Computes dynamic row heights and column widths.
   - Draws cell border strokes (`#CCCCCC`) and cell background fills.
   - Recursively renders cell text frames with padding.

---

## 4. Concurrency & Thread Model

In graphical desktop software, running synchronous I/O or multi-second conversions on the main UI thread freezes the window ("Not Responding").

SlidePDF Studio isolates workload execution:
1. **Main UI Thread**:
   - Handles CustomTkinter event loop, user clicks, animations, and repaints.
2. **Worker Daemon Thread (`_run_conversion_worker`)**:
   - Runs `ConversionManager.convert_batch()`.
   - Dispatches progress and status updates to the UI thread via `self.after(0, callback)`.
3. **COM Apartment Threading (Windows)**:
   - Microsoft COM requires Apartment Thread initialization for background threads.
   - `pythoncom.CoInitialize()` and `pythoncom.CoUninitialize()` are strictly called inside `msoffice.py` to prevent Windows RPC deadlocks.

---

## 5. Merging & Document Consolidation (`merger.py`)

When the user selects **"Merge All into 1 PDF"**:
1. All presentations in the queue are individually converted to PDF.
2. `PDFMergerUtil.merge_pdfs` utilizes `pypdf.PdfWriter` to assemble pages in queue sequence.
3. Each presentation's filename is injected as a root PDF Outline item (bookmark), allowing instant jump-to navigation in standard PDF viewers (Acrobat, Evince, Preview, Chrome).
4. Standard metadata tags (`/Title`, `/Producer`, `/Creator`) are injected into the PDF trailer dictionary.
