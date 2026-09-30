import os
from pathlib import Path
import platform
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def find_ghostscript_binary() -> str:
  """Locates the Ghostscript executable on the host system."""
  system = platform.system()
  candidates = (
      ["gswin64c", "gswin32c", "gs"] if system == "Windows" else ["gs"]
  )

  # Check PATH environment variable first
  for binary in candidates:
    if shutil.which(binary):
      return binary

  # Scan standard Windows installation paths
  if system == "Windows":
    default_dirs = [
        Path(r"C:\Program Files\gs"),
        Path(r"C:\Program Files (x86)\gs"),
    ]
    for directory in default_dirs:
      if directory.exists():
        # Prefer console binary (gswin64c.exe)
        for exe in sorted(directory.glob("**/gswin*c.exe")):
          return str(exe)
        for exe in sorted(directory.glob("**/gswin*.exe")):
          return str(exe)

  raise FileNotFoundError(
      "Ghostscript was not found!\nPlease ensure Ghostscript is installed and"
      " available in your system PATH."
  )


class PDFOptimizerApp:

  def __init__(self, root: tk.Tk):
    self.root = root
    self.root.title("Ghostscript PDF Compressor & Optimizer")
    self.root.geometry("640x390")
    self.root.resizable(False, False)

    self.input_pdf_path = tk.StringVar()
    self.output_pdf_path = tk.StringVar()
    self.profile_choice = tk.StringVar(
        value="150 DPI (E-Book Balanced - Recommended)"
    )

    self._setup_style()
    self._create_widgets()

  def _setup_style(self):
    self.style = ttk.Style()
    self.style.theme_use("clam")
    self.style.configure(".", font=("Segoe UI", 9))
    self.style.configure("TButton", padding=5)
    self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"))

  def _create_widgets(self):
    main_frame = ttk.Frame(self.root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # 1. Source File Selection
    file_frame = ttk.LabelFrame(main_frame, text=" Source PDF ", padding=10)
    file_frame.pack(fill=tk.X, pady=(0, 10))

    entry_file = ttk.Entry(
        file_frame, textvariable=self.input_pdf_path, state="readonly"
    )
    entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

    btn_browse = ttk.Button(
        file_frame, text="Browse PDF...", command=self.select_pdf
    )
    btn_browse.pack(side=tk.RIGHT)

    # 2. Optimization Preset
    settings_frame = ttk.LabelFrame(
        main_frame, text=" Compression Preset ", padding=10
    )
    settings_frame.pack(fill=tk.X, pady=(0, 10))

    profile_row = ttk.Frame(settings_frame)
    profile_row.pack(fill=tk.X, pady=(0, 5))

    lbl_prof = ttk.Label(profile_row, text="Target Quality:")
    lbl_prof.pack(side=tk.LEFT, padx=(0, 10))

    profiles = [
        "150 DPI (E-Book Balanced - Recommended)",
        "100 DPI (Mobile / Compact)",
        "72 DPI (Screen / Max Compression)",
        "200 DPI (High Quality / Diagrams)",
    ]

    cb_profile = ttk.Combobox(
        profile_row,
        textvariable=self.profile_choice,
        values=profiles,
        state="readonly",
        width=38,
    )
    cb_profile.pack(side=tk.LEFT)

    # Output File Info
    out_row = ttk.Frame(settings_frame)
    out_row.pack(fill=tk.X, pady=(8, 0))

    lbl_out = ttk.Label(out_row, text="Output:", foreground="#555")
    lbl_out.pack(side=tk.LEFT, padx=(0, 8))

    lbl_out_path = ttk.Label(
        out_row,
        textvariable=self.output_pdf_path,
        font=("Segoe UI", 8),
        foreground="#0055aa",
    )
    lbl_out_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 3. Progress and Status
    self.prog_bar = ttk.Progressbar(main_frame, mode="indeterminate")
    self.prog_bar.pack(fill=tk.X, pady=(10, 8))

    self.lbl_status = ttk.Label(
        main_frame, text="Ready. Please select a PDF file.", anchor="center"
    )
    self.lbl_status.pack(fill=tk.X, pady=(0, 10))

    # 4. Action Button
    self.btn_run = ttk.Button(
        main_frame,
        text="Compress & Optimize PDF",
        style="Primary.TButton",
        command=self.start_processing,
    )
    self.btn_run.pack(fill=tk.X, ipady=4)

  def select_pdf(self):
    selected_file = filedialog.askopenfilename(
        title="Select PDF File", filetypes=[("PDF Files", "*.pdf")]
    )
    if not selected_file:
      return

    p = Path(selected_file)
    self.input_pdf_path.set(str(p))

    # Auto-generate output filename with '_optimized' suffix
    out_path = p.parent / f"{p.stem}_optimized{p.suffix}"
    self.output_pdf_path.set(str(out_path))

    file_size_mb = p.stat().st_size / (1024 * 1024)
    self.lbl_status.config(
        text=f"Selected: {p.name} ({file_size_mb:.2f} MB). Ready to optimize."
    )

  def start_processing(self):
    in_path = self.input_pdf_path.get()
    out_path = self.output_pdf_path.get()

    if not in_path or not Path(in_path).exists():
      messagebox.showwarning("Warning", "Please select a valid PDF file.")
      return

    # Resolve DPI based on chosen profile
    profile_str = self.profile_choice.get()
    if "72 DPI" in profile_str:
      dpi = 72
    elif "100 DPI" in profile_str:
      dpi = 100
    elif "200 DPI" in profile_str:
      dpi = 200
    else:
      dpi = 150

    self.btn_run.config(state="disabled")
    self.prog_bar.start(10)
    self.lbl_status.config(
        text=f"Re-encoding images at {dpi} DPI, please wait..."
    )

    thread = threading.Thread(
        target=self._run_ghostscript_task,
        args=(in_path, out_path, dpi),
        daemon=True,
    )
    thread.start()

  def _run_ghostscript_task(self, in_path: str, out_path: str, dpi: int):
    try:
      gs_bin = find_ghostscript_binary()

      # Ghostscript command flags to enforce downsampling and recompression
      cmd = [
          gs_bin,
          "-sDEVICE=pdfwrite",
          "-dCompatibilityLevel=1.4",
          "-dNOPAUSE",
          "-dQUIET",
          "-dBATCH",
          # Prevent pass-through without re-encoding
          "-dPassThroughJPEGImages=false",
          "-dPassThroughJPXImages=false",
          # Font and duplicate resource optimizations
          "-dDetectDuplicateImages=true",
          "-dCompressFonts=true",
          "-dSubsetFonts=true",
          # Color images re-encoding
          "-dAutoFilterColorImages=false",
          "-dColorImageFilter=/DCTEncode",
          "-dDownsampleColorImages=true",
          "-dColorImageDownsampleType=/Bicubic",
          f"-dColorImageResolution={dpi}",
          "-dColorImageDownsampleThreshold=1.0",
          # Grayscale images re-encoding
          "-dAutoFilterGrayImages=false",
          "-dGrayImageFilter=/DCTEncode",
          "-dDownsampleGrayImages=true",
          "-dGrayImageDownsampleType=/Bicubic",
          f"-dGrayImageResolution={dpi}",
          "-dGrayImageDownsampleThreshold=1.0",
          # Monochrome (1-bit) images downsampling
          "-dDownsampleMonoImages=true",
          "-dMonoImageDownsampleType=/Bicubic",
          f"-dMonoImageResolution={dpi}",
          "-dMonoImageDownsampleThreshold=1.0",
          f"-sOutputFile={out_path}",
          in_path,
      ]

      flags = (
          subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
      )

      proc = subprocess.run(
          cmd,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
          text=True,
          creationflags=flags,
      )

      if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "An unknown error occurred.")

      in_size = Path(in_path).stat().st_size
      out_size = Path(out_path).stat().st_size
      saved_percent = (
          ((in_size - out_size) / in_size) * 100 if in_size > 0 else 0
      )

      self.root.after(
          0, self._on_success, in_size, out_size, saved_percent, out_path
      )

    except Exception as exc:
      self.root.after(0, self._on_failure, str(exc))

  def _on_success(
      self, in_size: int, out_size: int, saved_percent: float, out_path: str
  ):
    self.prog_bar.stop()
    self.btn_run.config(state="normal")

    in_mb = in_size / (1024 * 1024)
    out_mb = out_size / (1024 * 1024)

    msg = f"Done: {in_mb:.2f} MB ➔ {out_mb:.2f} MB (Saved: {saved_percent:.1f}%)"
    self.lbl_status.config(text=msg)

    messagebox.showinfo(
        "Success",
        f"Optimization completed successfully!\n\n"
        f"Original Size : {in_mb:.2f} MB\n"
        f"Optimized Size: {out_mb:.2f} MB\n"
        f"Space Saved   : {saved_percent:.1f}%\n\n"
        f"Saved to:\n{out_path}",
    )

  def _on_failure(self, error_msg: str):
    self.prog_bar.stop()
    self.btn_run.config(state="normal")
    self.lbl_status.config(text="An error occurred.")
    messagebox.showerror(
        "Error", f"An error occurred during processing:\n{error_msg}"
    )


if __name__ == "__main__":
  root = tk.Tk()
  app = PDFOptimizerApp(root)
  root.mainloop()