import os
from pathlib import Path
import platform
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def find_ghostscript_binary() -> str:
  system = platform.system()
  candidates = (
      ["gswin64c", "gswin32c", "gs"] if system == "Windows" else ["gs"]
  )
  for binary in candidates:
    if shutil.which(binary):
      return binary

  if system == "Windows":
    default_dirs = [
        Path(r"C:\Program Files\gs"),
        Path(r"C:\Program Files (x86)\gs"),
    ]
    for directory in default_dirs:
      if directory.exists():
        for exe in sorted(directory.glob("**/gswin*c.exe")):
          return str(exe)
        for exe in sorted(directory.glob("**/gswin*.exe")):
          return str(exe)

  raise FileNotFoundError(
      "Ghostscript bulunamadı!\nLütfen Ghostscript'in kurulu olduğundan emin"
      " olun."
  )


class PDFOptimizerApp:

  def __init__(self, root: tk.Tk):
    self.root = root
    self.root.title("Ghostscript PDF Zorlamalı Sıkıştırıcı")
    self.root.geometry("640x390")
    self.root.resizable(False, False)

    self.input_pdf_path = tk.StringVar()
    self.output_pdf_path = tk.StringVar()
    self.profile_choice = tk.StringVar(value="150 DPI (E-Kitap Dengeli)")

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

    # 1. Kaynak Dosya Seçimi
    file_frame = ttk.LabelFrame(main_frame, text=" Kaynak PDF ", padding=10)
    file_frame.pack(fill=tk.X, pady=(0, 10))

    entry_file = ttk.Entry(
        file_frame, textvariable=self.input_pdf_path, state="readonly"
    )
    entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

    btn_browse = ttk.Button(
        file_frame, text="PDF Seç...", command=self.select_pdf
    )
    btn_browse.pack(side=tk.RIGHT)

    # 2. Optimizasyon Profili
    settings_frame = ttk.LabelFrame(
        main_frame, text=" Sıkıştırma Profili ", padding=10
    )
    settings_frame.pack(fill=tk.X, pady=(0, 10))

    profile_row = ttk.Frame(settings_frame)
    profile_row.pack(fill=tk.X, pady=(0, 5))

    lbl_prof = ttk.Label(profile_row, text="Profil Seçimi:")
    lbl_prof.pack(side=tk.LEFT, padx=(0, 10))

    profiles = [
        "150 DPI (E-Kitap Dengeli - Önerilen)",
        "100 DPI (Mobil/Hafif Okuma)",
        "72 DPI (Maksimum Küçültme)",
        "200 DPI (Yüksek Kalite / Şemalar)",
    ]

    cb_profile = ttk.Combobox(
        profile_row,
        textvariable=self.profile_choice,
        values=profiles,
        state="readonly",
        width=35,
    )
    cb_profile.pack(side=tk.LEFT)

    # Çıktı Yolu Bilgisi
    out_row = ttk.Frame(settings_frame)
    out_row.pack(fill=tk.X, pady=(8, 0))

    lbl_out = ttk.Label(out_row, text="Hedef:", foreground="#555")
    lbl_out.pack(side=tk.LEFT, padx=(0, 8))

    lbl_out_path = ttk.Label(
        out_row,
        textvariable=self.output_pdf_path,
        font=("Segoe UI", 8),
        foreground="#0055aa",
    )
    lbl_out_path.pack(side=tk.LEFT, fill=tk.X, expand=True)

    # 3. İlerleme ve Durum
    self.prog_bar = ttk.Progressbar(main_frame, mode="indeterminate")
    self.prog_bar.pack(fill=tk.X, pady=(10, 8))

    self.lbl_status = ttk.Label(
        main_frame, text="Hazır. Lütfen bir PDF dosyası seçin.", anchor="center"
    )
    self.lbl_status.pack(fill=tk.X, pady=(0, 10))

    # 4. Başlat Butonu
    self.btn_run = ttk.Button(
        main_frame,
        text="Görselleri Yeniden Kodla ve Sıkıştır",
        style="Primary.TButton",
        command=self.start_processing,
    )
    self.btn_run.pack(fill=tk.X, ipady=4)

  def select_pdf(self):
    selected_file = filedialog.askopenfilename(
        title="PDF Dosyasını Seçin", filetypes=[("PDF Dosyaları", "*.pdf")]
    )
    if not selected_file:
      return

    p = Path(selected_file)
    self.input_pdf_path.set(str(p))

    out_path = p.parent / f"{p.stem}_optimize{p.suffix}"
    self.output_pdf_path.set(str(out_path))

    file_size_mb = p.stat().st_size / (1024 * 1024)
    self.lbl_status.config(
        text=f"Seçildi: {p.name} ({file_size_mb:.2f} MB). İşleme hazır."
    )

  def start_processing(self):
    in_path = self.input_pdf_path.get()
    out_path = self.output_pdf_path.get()

    if not in_path or not Path(in_path).exists():
      messagebox.showwarning("Uyarı", "Lütfen geçerli bir PDF dosyası seçin.")
      return

    # Profil üzerinden hedef DPI çözümleme
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
        text=(
            f"Görseller {dpi} DPI seviyesine yeniden kodlanıyor, lütfen"
            " bekleyin..."
        )
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

      # Görselleri zorunlu JPEG sıkıştırmasına sokan ve pas geçmeyi engelleyen bayraklar
      cmd = [
          gs_bin,
          "-sDEVICE=pdfwrite",
          "-dCompatibilityLevel=1.4",
          "-dNOPAUSE",
          "-dQUIET",
          "-dBATCH",
          # 1. Doğrudan kopyalamayı kesinlikle engelle
          "-dPassThroughJPEGImages=false",
          "-dPassThroughJPXImages=false",
          # 2. Font ve nesne tekilleştirme
          "-dDetectDuplicateImages=true",
          "-dCompressFonts=true",
          "-dSubsetFonts=true",
          # 3. Renkli görselleri zorunlu JPEG kodlamaya al
          "-dAutoFilterColorImages=false",
          "-dColorImageFilter=/DCTEncode",
          "-dDownsampleColorImages=true",
          "-dColorImageDownsampleType=/Bicubic",
          f"-dColorImageResolution={dpi}",
          "-dColorImageDownsampleThreshold=1.0",
          # 4. Gri tonlamalı görselleri zorunlu JPEG kodlamaya al
          "-dAutoFilterGrayImages=false",
          "-dGrayImageFilter=/DCTEncode",
          "-dDownsampleGrayImages=true",
          "-dGrayImageDownsampleType=/Bicubic",
          f"-dGrayImageResolution={dpi}",
          "-dGrayImageDownsampleThreshold=1.0",
          # 5. Monokrom (1-bit) görselleri yeniden örnekle
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
        raise RuntimeError(proc.stderr.strip() or "Bilinmeyen bir hata oluştu.")

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

    msg = f"Tamamlandı: {in_mb:.2f} MB ➔ {out_mb:.2f} MB (Tasarruf: %{saved_percent:.1f})"
    self.lbl_status.config(text=msg)

    messagebox.showinfo(
        "Başarılı",
        f"İşlem tamamlandı!\n\n"
        f"Orijinal Boyut : {in_mb:.2f} MB\n"
        f"Optimize Boyut : {out_mb:.2f} MB\n"
        f"Kazanım Oranı  : %{saved_percent:.1f}\n\n"
        f"Kayıt Yeri:\n{out_path}",
    )

  def _on_failure(self, error_msg: str):
    self.prog_bar.stop()
    self.btn_run.config(state="normal")
    self.lbl_status.config(text="Hata oluştu.")
    messagebox.showerror("Hata", f"İşlem sırasında bir hata oluştu:\n{error_msg}")


if __name__ == "__main__":
  root = tk.Tk()
  app = PDFOptimizerApp(root)
  root.mainloop()