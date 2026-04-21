import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import yt_dlp
import threading
import os
import imageio_ffmpeg
import tomllib

# --- Стили и цвета ---
COLOR_BG = "#121212"
COLOR_BANANA = "#FFE135"
COLOR_WHITE = "#FFFFFF"
COLOR_GRAY = "#2A2A2A"

LANGUAGES = {
    "Russian": {
        "title": "Banana Downloader",
        "settings": "НАСТРОЙКИ",
        "back": "← НАЗАД",
        "path_btn": "📁 Выбрать папку скачивания",
        "cover": "Скачивать с обложкой",
        "download_btn": "СКАЧАТЬ",
        "placeholder": "Вставьте ссылку сюда...",
        "pause": "ПАУЗА",
        "resume": "ПРОДОЛЖИТЬ",
        "paste": "Вставить"
    },
    "English": {
        "title": "Banana Downloader",
        "settings": "SETTINGS",
        "back": "← BACK",
        "path_btn": "📁 Choose path",
        "cover": "Download with cover",
        "download_btn": "DOWNLOAD",
        "placeholder": "Paste link here...",
        "pause": "PAUSE",
        "resume": "RESUME",
        "paste": "Paste"
    }
}

class BananaDownloader:
    def __init__(self, root):
        self.root = root
        
        # Пути конфигурации
        self.config_dir = os.path.join(os.path.expanduser("~"), "Documents", "Banana-Downloader")
        self.config_file = os.path.join(self.config_dir, "config.toml")
        
        # Настройки по умолчанию
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.current_lang = "Russian"
        self.show_cover = True
        
        # Переменные для управления потоком
        self.is_paused = False
        self.pause_event = threading.Event()
        self.pause_event.set() 

        self.load_config()

        self.root.title("Banana Downloader")
        self.root.geometry("500x600")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.main_frame = tk.Frame(root, bg=COLOR_BG)
        self.settings_frame = tk.Frame(root, bg=COLOR_BG)

        self.setup_ui()
        self.main_frame.pack(fill="both", expand=True)

    def load_config(self):
        if not os.path.exists(self.config_dir): os.makedirs(self.config_dir)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "rb") as f:
                    data = tomllib.load(f)
                    self.download_path = data.get("download_path", self.download_path)
                    self.current_lang = data.get("language", "Russian")
                    self.show_cover = data.get("show_cover", True)
            except: pass

    def save_config(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(f'download_path = "{self.download_path.replace(chr(92), "/")}"\n')
            f.write(f'language = "{self.current_lang}"\n')
            f.write(f'show_cover = {str(self.show_cover).lower()}\n')

    def setup_ui(self):
        # --- Главный экран ---
        # Кнопка настроек справа сверху
        tk.Button(self.main_frame, text="⚙", font=("Arial", 20), bg=COLOR_BG, fg=COLOR_BANANA, bd=0, 
                  command=self.show_settings, activebackground=COLOR_BG).place(x=450, y=10)

        # Блок логотипа
        self.logo_frame = tk.Frame(self.main_frame, bg=COLOR_BG)
        self.logo_frame.pack(pady=(60, 20))

        tk.Label(self.logo_frame, text="🍌 Banana", font=("Impact", 60), bg=COLOR_BG, fg=COLOR_BANANA).pack()
        tk.Label(self.logo_frame, text="DOWNLOADER", font=("Arial", 16, "bold"), bg=COLOR_BG, fg=COLOR_WHITE).pack()

        # Поле ввода URL
        self.url_entry = tk.Entry(self.main_frame, font=("Arial", 12), bg=COLOR_GRAY, fg=COLOR_WHITE, 
                                  bd=0, insertbackground=COLOR_BANANA, highlightthickness=1, highlightbackground="#444444")
        self.url_entry.pack(fill="x", padx=60, pady=(0, 20), ipady=10)
        self.url_entry.insert(0, LANGUAGES[self.current_lang]["placeholder"])
        self.url_entry.bind("<FocusIn>", lambda e: self.url_entry.delete(0, tk.END) if self.url_entry.get() == LANGUAGES[self.current_lang]["placeholder"] else None)
        self.url_entry.bind("<Button-3>", self.show_context_menu)

        # Кнопка Download
        self.btn_download = tk.Button(self.main_frame, text=LANGUAGES[self.current_lang]["download_btn"], font=("Arial", 12, "bold"),
                                      bg=COLOR_BANANA, fg="#000000", bd=0, command=self.start_download)
        self.btn_download.pack(fill="x", padx=60, pady=10, ipady=12)

        # Кнопка Pause
        self.btn_pause = tk.Button(self.main_frame, text=LANGUAGES[self.current_lang]["pause"], font=("Arial", 10, "bold"),
                                   bg="#333333", fg=COLOR_WHITE, bd=0, state="disabled", command=self.toggle_pause)
        self.btn_pause.pack(fill="x", padx=100, pady=5, ipady=5)

        # Прогресс-бар всего альбома
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure("Banana.Horizontal.TProgressbar", background=COLOR_BANANA, troughcolor=COLOR_GRAY, bordercolor=COLOR_GRAY, thickness=15)
        self.progress = ttk.Progressbar(self.main_frame, style="Banana.Horizontal.TProgressbar", orient="horizontal", length=380, mode="determinate")
        self.progress.pack(pady=(30, 30))

        # --- Экран настроек ---
        tk.Label(self.settings_frame, text=LANGUAGES[self.current_lang]["settings"], font=("Arial", 20, "bold"), bg=COLOR_BG, fg=COLOR_BANANA).pack(pady=40)
        tk.Button(self.settings_frame, text=LANGUAGES[self.current_lang]["path_btn"], bg=COLOR_GRAY, fg=COLOR_WHITE, bd=0, command=self.choose_folder).pack(fill="x", padx=80, pady=10, ipady=10)
        self.path_lbl = tk.Label(self.settings_frame, text=self.download_path, bg=COLOR_BG, fg="#888888", font=("Arial", 8), wraplength=350)
        self.path_lbl.pack()
        self.cover_var = tk.BooleanVar(value=self.show_cover)
        tk.Checkbutton(self.settings_frame, text=LANGUAGES[self.current_lang]["cover"], variable=self.cover_var, bg=COLOR_BG, fg=COLOR_WHITE, selectcolor="#000000", activebackground=COLOR_BG, command=self.update_cover_setting).pack(pady=20)
        self.lang_cb = ttk.Combobox(self.settings_frame, values=["Russian", "English"], state="readonly")
        self.lang_cb.set(self.current_lang)
        self.lang_cb.pack(pady=10)
        self.lang_cb.bind("<<ComboboxSelected>>", self.change_lang)
        tk.Button(self.settings_frame, text=LANGUAGES[self.current_lang]["back"], bg="#444444", fg=COLOR_WHITE, bd=0, command=self.show_main).pack(fill="x", padx=120, pady=40, ipady=8)

    # --- Логика скачивания ---
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Процент текущей песни
                p_str = d.get('_percent_str', '0%').replace('%', '').strip()
                current_file_percent = float(p_str)
                
                # Позиция в плейлисте
                playlist_index = d.get('info_dict', {}).get('playlist_index', 1)
                n_entries = d.get('info_dict', {}).get('n_entries', 1)

                # Математика общего прогресса всего альбома
                total_progress = ((playlist_index - 1) * 100 + current_file_percent) / n_entries
                self.progress['value'] = total_progress
            except: pass
        self.pause_event.wait()

    def start_download(self):
        url = self.url_entry.get().strip()
        if "http" not in url: return
        self.btn_download.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.progress['value'] = 0
        threading.Thread(target=self.download_worker, args=(url,), daemon=True).start()

    def download_worker(self, url):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'progress_hooks': [self.progress_hook],
            'ffmpeg_location': ffmpeg_exe,
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
            'quiet': True, 'nocheckcertificate': True,
            'ignoreerrors': True
        }
        if self.cover_var.get():
            ydl_opts['writethumbnail'] = True
            ydl_opts['postprocessors'].append({'key': 'EmbedThumbnail'})
            ydl_opts['postprocessors'].append({'key': 'FFmpegMetadata'})

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.progress['value'] = 100
        except: pass
        finally:
            self.btn_download.config(state="normal")
            self.btn_pause.config(state="disabled", text=LANGUAGES[self.current_lang]["pause"])
            self.is_paused = False
            self.pause_event.set()

    def toggle_pause(self):
        if not self.is_paused:
            self.pause_event.clear()
            self.is_paused = True
            self.btn_pause.config(text=LANGUAGES[self.current_lang]["resume"], bg=COLOR_BANANA, fg="black")
        else:
            self.pause_event.set()
            self.is_paused = False
            self.btn_pause.config(text=LANGUAGES[self.current_lang]["pause"], bg="#333333", fg=COLOR_WHITE)

    def show_context_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg=COLOR_GRAY, fg=COLOR_WHITE)
        menu.add_command(label=LANGUAGES[self.current_lang]["paste"], command=lambda: self.url_entry.insert(tk.INSERT, self.root.clipboard_get()))
        menu.post(event.x_root, event.y_root)

    def change_lang(self, e):
        self.current_lang = self.lang_cb.get(); self.save_config()
        messagebox.showinfo("Banana", "Restart app / Перезапустите программу")

    def choose_folder(self):
        f = filedialog.askdirectory()
        if f: self.download_path = f; self.path_lbl.config(text=f); self.save_config()

    def update_cover_setting(self):
        self.show_cover = self.cover_var.get(); self.save_config()

    def show_settings(self):
        self.main_frame.pack_forget(); self.settings_frame.pack(fill="both", expand=True)

    def show_main(self):
        self.settings_frame.pack_forget(); self.main_frame.pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = BananaDownloader(root)
    root.mainloop()
