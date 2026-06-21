"""
Audio Converter Tab — Convert between audio formats using FFmpeg
"""
import os
import threading
import subprocess
import customtkinter as ctk
from tkinter import filedialog

from src.utils.config_manager import load_config
from src.utils.i18n import _

class ConverterTab(ctk.CTkFrame):
    def __init__(self, parent, colors: dict):
        super().__init__(parent, fg_color=colors["bg_dark"], corner_radius=0)
        self.colors = colors
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._input_path = None
        self._build_header()
        self._build_body()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=self.colors["sidebar_bg"], corner_radius=0, height=90)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        ctk.CTkLabel(header, text=_("conv_title"),
                     font=ctk.CTkFont("Segoe UI", 24, "bold"),
                     text_color=self.colors["text_primary"]).grid(row=0, column=0, padx=36, pady=(24, 0), sticky="w")
        ctk.CTkLabel(header, text=_("conv_subtitle"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]).grid(row=1, column=0, padx=36, pady=(4, 16), sticky="w")

    def _build_body(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=self.colors["bg_dark"], corner_radius=0)
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        # ── Source File Card ──
        input_card = self._card(scroll, _("conv_card_input"))
        input_card.grid(row=0, column=0, padx=36, pady=(32, 16), sticky="ew")
        input_card.grid_columnconfigure(1, weight=1)

        btn_choose = ctk.CTkButton(input_card, text=_("btn_choose_file"), width=180, height=48,
                                   corner_radius=12,
                                   font=ctk.CTkFont("Segoe UI", 14, "bold"),
                                   fg_color=self.colors["accent"],
                                   hover_color=self.colors["accent_hover"],
                                   command=self._on_choose_file)
        btn_choose.grid(row=1, column=0, padx=24, pady=20)

        self.lbl_file = ctk.CTkLabel(input_card, text=_("conv_no_file"),
                                     font=ctk.CTkFont("Segoe UI", 14),
                                     text_color=self.colors["text_secondary"], anchor="w")
        self.lbl_file.grid(row=1, column=1, sticky="ew", padx=(0, 24))

        # File info
        self.lbl_info = ctk.CTkLabel(input_card, text="",
                                     font=ctk.CTkFont("Segoe UI", 12),
                                     text_color=self.colors["text_secondary"], anchor="w")
        self.lbl_info.grid(row=2, column=0, columnspan=2, sticky="w", padx=24, pady=(0, 16))

        # ── Output Settings Card ──
        output_card = self._card(scroll, _("conv_card_output"))
        output_card.grid(row=1, column=0, padx=36, pady=16, sticky="ew")
        output_card.grid_columnconfigure((0, 1), weight=1)

        # Output format
        ctk.CTkLabel(output_card, text=_("conv_out_format"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]).grid(row=1, column=0, sticky="w", padx=24, pady=(16, 6))

        self.format_var = ctk.StringVar(value="mp3")
        ctk.CTkOptionMenu(output_card, variable=self.format_var,
                          values=["mp3", "m4a", "flac", "wav", "aac", "ogg", "wma"],
                          height=42, corner_radius=10,
                          fg_color=self.colors["bg_dark"], button_color=self.colors["accent"],
                          font=ctk.CTkFont("Segoe UI", 14)).grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 20))

        # Quality (bitrate)
        ctk.CTkLabel(output_card, text=_("conv_out_quality"),
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=self.colors["text_secondary"]).grid(row=1, column=1, sticky="w", padx=24, pady=(16, 6))

        self.quality_var = ctk.StringVar(value="192kbps")
        ctk.CTkOptionMenu(output_card, variable=self.quality_var,
                          values=["320kbps", "256kbps", "192kbps", "128kbps", "96kbps"],
                          height=42, corner_radius=10,
                          fg_color=self.colors["bg_dark"], button_color=self.colors["accent"],
                          font=ctk.CTkFont("Segoe UI", 14)).grid(row=2, column=1, sticky="ew", padx=24, pady=(0, 20))

        # ── Progress ──
        prog_card = self._card(scroll, "📊  Progress")
        prog_card.grid(row=2, column=0, padx=36, pady=16, sticky="ew")
        prog_card.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_card, height=16, corner_radius=8,
                                                fg_color=self.colors["bg_dark"],
                                                progress_color=self.colors["accent"])
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(16, 8))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(prog_card, text=_("conv_ready"),
                                            font=ctk.CTkFont("Segoe UI", 13),
                                            text_color=self.colors["text_secondary"])
        self.progress_label.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 20))

        # ── Convert Button ──
        self.convert_btn = ctk.CTkButton(
            scroll, text=_("btn_convert"), height=60, corner_radius=16,
            font=ctk.CTkFont("Segoe UI", 18, "bold"),
            fg_color=self.colors["accent"], hover_color=self.colors["accent_hover"],
            command=self._on_convert,
        )
        self.convert_btn.grid(row=3, column=0, padx=36, pady=(12, 40), sticky="ew")

    def _card(self, parent, title: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=self.colors["card_bg"], corner_radius=16,
                              border_width=1, border_color=self.colors["border"])
        frame.grid_columnconfigure(0, weight=1)
        if title:
            ctk.CTkLabel(frame, text=title,
                          font=ctk.CTkFont("Segoe UI", 15, "bold"),
                          text_color=self.colors["accent"]).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 0))
        return frame

    def _on_choose_file(self):
        path = filedialog.askopenfilename(
            title="Choose Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.m4a *.flac *.wav *.ogg *.aac *.wma *.opus"),
                ("All Files", "*.*")
            ]
        )
        if not path:
            return

        self._input_path = path
        basename = os.path.basename(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        ext = os.path.splitext(path)[1].upper().replace(".", "")

        self.lbl_file.configure(text=f"🎵 {basename}", text_color=self.colors["text_primary"])
        self.lbl_info.configure(text=f"Format: {ext}  •  Size: {size_mb:.1f} MB")

    def _on_convert(self):
        if not self._input_path or not os.path.exists(self._input_path):
            self.progress_label.configure(text="❌ Please choose a file first.", text_color=self.colors["error"])
            return

        out_format = self.format_var.get()
        quality = self.quality_var.get().replace("kbps", "")

        # Build output path
        base, _ = os.path.splitext(self._input_path)
        out_path = f"{base}_converted.{out_format}"

        self.convert_btn.configure(state="disabled")
        self.progress_bar.set(0.1)
        self.progress_label.configure(text=_("conv_converting"), text_color=self.colors["text_secondary"])

        def _run():
            try:
                config = load_config()
                ffmpeg = config.get("ffmpeg_path", "") or "ffmpeg"

                cmd = [ffmpeg, "-y", "-i", self._input_path]
                
                if out_format in ["mp3", "aac", "ogg", "wma"]:
                    cmd += ["-b:a", f"{quality}k"]
                elif out_format == "flac":
                    cmd += ["-compression_level", "5"]
                # wav = no compression needed, just format
                
                cmd.append(out_path)

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

                if result.returncode == 0 and os.path.exists(out_path):
                    size_mb = os.path.getsize(out_path) / (1024 * 1024)
                    self.after(0, lambda: self._on_convert_done(out_path, size_mb))
                else:
                    err = result.stderr[-200:] if result.stderr else "Unknown error"
                    self.after(0, lambda: self._on_convert_error(err))
            except Exception as e:
                self.after(0, lambda: self._on_convert_error(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_convert_done(self, path: str, size_mb: float):
        self.progress_bar.set(1)
        self.progress_label.configure(
            text=f"✅ {_('conv_done')}  •  {os.path.basename(path)}  •  {size_mb:.1f} MB",
            text_color=self.colors["success"]
        )
        self.convert_btn.configure(state="normal")

    def _on_convert_error(self, err: str):
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"❌ {err[:100]}", text_color=self.colors["error"])
        self.convert_btn.configure(state="normal")
