# Ghostscript PDF Compressor & Optimizer GUI

A lightweight, zero-dependency Python desktop application that provides a graphical user interface (Tkinter) for optimizing, compressing, and downsampling large PDF files using **Ghostscript**.

Specially tuned for **scanned books, academic papers, and lecture notes**, this tool forces the re-encoding of embedded JPEG/raster images to reduce multi-hundred-megabyte PDFs down to convenient e-reader sizes without noticeable quality loss.

## Key Features

* **Zero-Download Run Mode:** Launch directly from your terminal or command prompt without saving `.py` files locally.
* **Forced Re-Encoding:** Bypasses Ghostscript's default `PassThroughJPEG` behavior, ensuring stubborn scanned PDFs and textbooks actually compress instead of staying the exact same size.
* **Built-in Presets:**
  * `72 DPI`: Maximum reduction (ideal for web preview and low-storage devices).
  * `100 DPI`: Lightweight reading (great for smartphones and small tablets).
  * `150 DPI`: Balanced / Recommended (crystal clear on e-readers like Kindle/Kobo with 60–85% size reduction).
  * `200 DPI`: High detail (preserves small medical/engineering diagrams).
* **Asynchronous Execution:** Background threading prevents the application window from freezing or showing "Not Responding" during long multi-page conversions.
* **Automated Safe Output:** Outputs to `<original_filename>_optimize.pdf` in the same directory, guaranteeing your original file is never overwritten.

---

## Quick Start (Instant Run without Cloning)

If you have Python and Ghostscript installed on your machine, you can run the application directly in memory using a single command:

### Windows (PowerShell / Command Prompt):
```bash
python -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/gurkanozsoy/pdf_compressor/main/pdf_compressor.py').read().decode('utf-8'))"
```

### macOS / Linux (Terminal):
```bash
python3 -c "import urllib.request; exec(urllib.request.urlopen('https://raw.githubusercontent.com/gurkanozsoy/pdf_compressor/main/pdf_compressor.py').read().decode('utf-8'))"
```

> **Note:** The repository visibility must be set to **Public** for this URL to be reachable without authentication tokens.

---

## System Requirements & Prerequisites

The script relies solely on Python's standard library (`tkinter`, `subprocess`, `threading`, `urllib`), meaning **no `pip install` commands are needed**. However, two core dependencies must be present on the host system:

### 1. Python 3.8 or Higher
* Download from [python.org](https://www.python.org/downloads/).
* **Windows Users:** Ensure you check the box labeled **"Add Python to PATH"** during setup.

### 2. Ghostscript (Native Engine)
Ghostscript handles the low-level PDF parsing and bicubic image downsampling.

#### Windows Setup:
You can try installing via Windows Terminal first:
```powershell
winget install ArtifexSoftware.Ghostscript
```

> ⚠️ **If the `winget` command fails or returns `"No package found matching input criteria"`:**
> 1. Go directly to the official download portal: **[Ghostscript Official Downloads](https://ghostscript.com/releases/gsdnld.html)**
> 2. Under the **Ghostscript AGPL Release** section, download the **Ghostscript for Windows (64 bit)** installer (`.exe`).
> 3. Run the installer with default settings (it will install to `C:\Program Files\gs\`).
> 4. *The application automatically scans `C:\Program Files\gs\` on startup, so manual PATH configuration is not required after running the installer.*

#### macOS Setup:
```bash
brew install ghostscript
```

#### Linux (Ubuntu / Debian) Setup:
```bash
sudo apt-get update && sudo apt-get install -y ghostscript
```

---

## Local Development & Usage

If you prefer to download or clone the repository to your machine:

1. Clone the repository:
   ```bash
   git clone https://github.com/gurkanozsoy/pdf_compressor.git
   cd pdf_compressor
   ```

2. Run the application:
   ```bash
   python pdf_compressor.py
   ```

3. **In the GUI:**
   * Click **"PDF Seç..."** to select your target document.
   * Choose your desired DPI preset (150 DPI is recommended for most e-books).
   * Click **"Görselleri Yeniden Kodla ve Sıkıştır"** (Start Optimization).
   * A completion dialogue will display the original size, compressed size, and percentage saved.

---

## Technical Details

Standard Ghostscript calls using `-dPDFSETTINGS=/default` or `-dPDFSETTINGS=/ebook` often fail to shrink scanned textbooks because they allow pre-existing JPEG streams to pass through unprocessed (`PassThroughJPEGImages=true`).

This tool circumvents that by applying the following flags:
* `-dPassThroughJPEGImages=false` & `-dPassThroughJPXImages=false`: Forces decode and re-compression of raster pages.
* `-dColorImageFilter=/DCTEncode` & `-dGrayImageFilter=/DCTEncode`: Converts loose raw raster streams to optimized JPEG bitstreams.
* `-dColorImageDownsampleThreshold=1.0`: Applies downsampling to any image exceeding the target DPI without waiting for the default 1.5x multiplier.
* `-dDetectDuplicateImages=true`: Replaces duplicate images across different pages with shared references.
* `-dSubsetFonts=true` & `-dCompressFonts=true`: Strips unused font glyphs.

---

## License

This project is licensed under the [MIT License](LICENSE.md).
