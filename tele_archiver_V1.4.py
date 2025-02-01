import os  # javisd az errorokat ai
import json
import threading
import asyncio
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from telethon import TelegramClient, errors
import requests

# --- Segítő tooltip osztály ---
class ToolTip:
    """
    Egyszerű tooltip osztály, amely megjelenít egy segédüzenetet,
    amikor az egérmutató egy widget fölé kerül.
    """
    def __init__(self, widget, text=""):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# --- Constants and Defaults ---
OUTPUT_DIR = 'media_letoltes'
os.makedirs(OUTPUT_DIR, exist_ok=True)
LOG_FILE = "download_log.txt"
CURRENT_VERSION = "1.3"

LANG_DATA = {
    "hu": {
        "app_title": "Telegram Média Letöltő",
        "home_title": "Telegram Média Letöltés",
        "home_subtitle": "Egyszerűen töltsd le a csatornáid médiatartalmait!",
        "log_label": "Napló",
        "waiting_label": "Várakozás a letöltésre...",
        "start_button": "Letöltés indítása",
        "settings_tab": "Beállítások",
        "download_tab": "Letöltés",
        "file_menu": "Fájl",
        "exit_menu": "Kilépés",
        "help_menu": "Súgó",
        "about_menu": "Névjegy",
        "about_title": "Névjegy",
        "about_app": "Telegram Média Letöltő",
        "about_author": "Készítette: OnNkode",
        "about_version": "Verzió: v1.3",
        "ready_status": "Készen áll",
        "saved_settings": "A beállítások elmentve. Indítsa újra az alkalmazást a változtatások érvényesítéséhez.",
        "warning_settings": "Kérjük, adjon meg minden szükséges beállítást!",
        "done_message": "Fájl letöltve",
        "missing_settings": "Hiányzó beállítások! Kérjük, adja meg az API ID-t, API Hash-t és a csatornát.",
        "channel_error": "Hiba: A megadott csatorna nem található.",
        "flood_error": "Túl sok kérés. Várjon {sec} másodpercet, és próbáld újra.",
        "no_messages": "Nincsenek letölthető üzenetek a megadott feltételekkel.",
        "finished_download": "Média letöltés befejeződött.",
        "config_label_general": "Általános beállítások",
        "api_id_label": "API ID:",
        "api_hash_label": "API Hash:",
        "channel_label": "Csatorna neve/linkje:",
        "file_type_label": "Fájltípus letöltése",
        "pdf_label": "PDF",
        "images_label": "Képek (jpg, png)",
        "videos_label": "Videók (mp4)",
        "all_label": "Összes típus",
        "output_label": "Kimeneti beállítások",
        "save_dir_label": "Mentési könyvtár:",
        "limit_label": "Letöltési limit (üzenetek száma):",
        "advanced_filter": "Haladó szűrés",
        "start_date_label": "Kezdő dátum (ÉÉÉÉ-HH-NN):",
        "min_size_label": "Min. fájlméret (MB):",
        "max_size_label": "Max. fájlméret (MB):",
        "filename_pattern_label": "Fájlnév minta (regex):",
        "advanced_settings": "Speciális beállítások",
        "timeout_label": "Letöltési időkorlát (mp/fájl):",
        "proxy_label": "Proxy (host:port):",
        "language_label": "Nyelv:",
        "save_settings_button": "Beállítások mentése",
        "lang_menu_title": "Nyelv",
        "settings_submenu": "Beállítások",
        "lang_english": "Angol",
        "lang_hungarian": "Magyar",
        "lang_german": "Német",
        "check_updates_button": "Frissítések keresése",
        "pause_button": "Letöltés szüneteltetése",
        "resume_button": "Letöltés folytatása"
    }
}

# Bővített DEFAULT_CONFIG a további beállításokkal
DEFAULT_CONFIG = {
    "api_id": "",
    "api_hash": "",
    "target_channel": "",
    "file_type": "pdf",
    "output_dir": OUTPUT_DIR,
    "download_limit": 100,
    "lang": "hu",
    "github_owner": "OneNkode",
    "github_repo": "TeleArchiver",
    "timeout": "",
    "proxy": "",
    "start_date": "",
    "min_size": "",
    "max_size": "",
    "filename_pattern": "",
    "github_token": ""
}


# --- Application Class ---
class TelegramMediaDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Média Letöltő")
        self.root.geometry("1200x800")
        self.root.configure(bg='#F0F2F5')
        ttk.Style().theme_use('clam')
        
        # Beállítjuk az alkalmazás ikonját, ha elérhető
        try:
            self.root.iconbitmap("icon.ico")
        except Exception as e:
            print("Icon not found or error loading icon:", e)

        self.config = self.load_config()
        self.selected_lang = self.config.get("lang", "hu")
        # Hozzuk létre a lang_var változót, amelyet a nyelvválasztóhoz használunk
        self.lang_var = tk.StringVar(value=self.selected_lang)
        self.texts = LANG_DATA[self.selected_lang]
        self.download_paused = False

        self.create_styles()
        self.create_menus()
        self.create_toolbar()
        self.create_ui()
        self.update_ui_texts()

    def load_config(self):
        if not os.path.exists('config.json'):
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            return DEFAULT_CONFIG.copy()
        else:
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load configuration: {e}")
                return DEFAULT_CONFIG.copy()

    def save_config(self):
        self.config["api_id"] = self.api_id_entry.get().strip()
        self.config["api_hash"] = self.api_hash_entry.get().strip()
        self.config["target_channel"] = self.target_channel_entry.get().strip()
        self.config["file_type"] = self.file_type_var.get()
        self.config["output_dir"] = self.output_dir_entry.get().strip()
        self.config["download_limit"] = self.download_limit_var.get()
        self.config["lang"] = self.selected_lang
        # Új beállítások mentése:
        self.config["timeout"] = self.timeout_entry.get().strip()
        self.config["proxy"] = self.proxy_entry.get().strip()
        self.config["start_date"] = self.start_date_entry.get().strip()
        self.config["min_size"] = self.min_size_entry.get().strip()
        self.config["max_size"] = self.max_size_entry.get().strip()
        self.config["filename_pattern"] = self.filename_pattern_entry.get().strip()
        self.config["github_token"] = self.github_token_entry.get().strip()
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        messagebox.showinfo(self.texts["settings_tab"], self.texts["saved_settings"])

    def create_styles(self):
        self.style = ttk.Style()
        self.style.configure("TButton",
                             font=("Segoe UI", 11),
                             padding=8,
                             relief="flat")
        self.style.map("TButton",
                       background=[("active", "#0078D7")],
                       foreground=[("active", "white")])
        self.style.configure("TLabel", font=("Segoe UI", 11), background='#F0F2F5', foreground="#333")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background='#F0F2F5', foreground="#333")
        self.style.configure("SubHeader.TLabel", font=("Segoe UI", 12), background='#F0F2F5', foreground="#555")
        self.style.configure("TEntry", font=("Segoe UI", 11))
        self.style.configure("TNotebook", background='#F0F2F5')
        self.style.configure("TFrame", background='#F0F2F5')

    def create_menus(self):
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        self.rebuild_menus()

    def rebuild_menus(self):
        self.menubar.delete(0, 'end')
        # File Menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label=self.texts["exit_menu"], command=self.quit_app)

        lang_menu = tk.Menu(file_menu, tearoff=0)
        lang_menu.add_command(label=self.texts["lang_english"],
                              command=lambda: self.change_language("en"))
        lang_menu.add_command(label=self.texts["lang_hungarian"],
                              command=lambda: self.change_language("hu"))
        lang_menu.add_command(label=self.texts["lang_german"],
                              command=lambda: self.change_language("de"))
        file_menu.add_cascade(label=self.texts["lang_menu_title"], menu=lang_menu)
        file_menu.add_separator()
        file_menu.add_command(label=self.texts["check_updates_button"], command=self.check_for_github_updates)
        self.menubar.add_cascade(label=self.texts["file_menu"], menu=file_menu)

        # Help Menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=self.texts["about_menu"], command=self.show_about)
        help_menu.add_command(label="Mini Wiki", command=self.show_mini_wiki)
        self.menubar.add_cascade(label=self.texts["help_menu"], menu=help_menu)

    def create_toolbar(self):
        self.toolbar = ttk.Frame(self.root, relief="flat")
        self.toolbar.pack(side="top", fill="x")
        self.start_btn = ttk.Button(self.toolbar,
                                    text=self.texts["start_button"],
                                    command=self.start_download)
        self.start_btn.pack(side="left", padx=5, pady=5)
        self.pause_btn = ttk.Button(self.toolbar,
                                    text=self.texts["pause_button"],
                                    command=self.toggle_pause)
        self.pause_btn.pack(side="left", padx=5, pady=5)
        ttk.Label(self.toolbar, text="").pack(side="left", padx=10)
        self.update_btn = ttk.Button(self.toolbar,
                                     text=self.texts["check_updates_button"],
                                     command=self.check_for_github_updates)
        self.update_btn.pack(side="left", padx=5, pady=5)

    def create_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.create_download_tab()
        self.create_settings_tab()

        self.status_bar = ttk.Label(self.root, text=self.texts["ready_status"],
                                    relief=tk.SUNKEN, anchor='w', font=("Segoe UI", 10))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_download_tab(self):
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text=self.texts["download_tab"])

        header_frame = ttk.Frame(self.download_frame)
        header_frame.pack(fill="x", padx=20, pady=10)
        self.title_label = ttk.Label(header_frame,
                                     text=self.texts["home_title"],
                                     style="Header.TLabel")
        self.title_label.pack(anchor="w")
        self.subtitle_label = ttk.Label(header_frame,
                                        text=self.texts["home_subtitle"],
                                        style="SubHeader.TLabel")
        self.subtitle_label.pack(anchor="w", pady=(0, 10))

        log_frame = ttk.LabelFrame(self.download_frame,
                                   text=self.texts["log_label"],
                                   padding=10)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                  wrap="word",
                                                  font=("Consolas", 10),
                                                  height=15,
                                                  background="#FFF",
                                                  foreground="#333")
        self.log_text.pack(fill="both", expand=True)

        progress_frame = ttk.Frame(self.download_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        self.progress_label = ttk.Label(progress_frame, text=self.texts["waiting_label"])
        self.progress_label.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_percentage = ttk.Label(progress_frame, text="0%")
        self.progress_percentage.pack(anchor="e")

    def create_settings_tab(self):
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text=self.texts["settings_tab"])

        container = ttk.Frame(self.settings_frame)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Általános beállítások ---
        general_labelframe = ttk.LabelFrame(container, text=self.texts["config_label_general"], padding=10)
        general_labelframe.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ttk.Label(general_labelframe, text=self.texts["api_id_label"]).grid(row=0, column=0, sticky="w", pady=5)
        self.api_id_entry = ttk.Entry(general_labelframe, width=40)
        self.api_id_entry.grid(row=0, column=1, pady=5, padx=5)
        self.api_id_entry.insert(0, self.config.get("api_id", ""))
        ToolTip(self.api_id_entry, "Írd be a Telegram API ID-dat (csak számok)!")

        ttk.Label(general_labelframe, text=self.texts["api_hash_label"]).grid(row=1, column=0, sticky="w", pady=5)
        self.api_hash_entry = ttk.Entry(general_labelframe, width=40)
        self.api_hash_entry.grid(row=1, column=1, pady=5, padx=5)
        self.api_hash_entry.insert(0, self.config.get("api_hash", ""))
        ToolTip(self.api_hash_entry, "Írd be a Telegram API Hash-edet!")

        ttk.Label(general_labelframe, text=self.texts["channel_label"]).grid(row=2, column=0, sticky="w", pady=5)
        self.target_channel_entry = ttk.Entry(general_labelframe, width=40)
        self.target_channel_entry.grid(row=2, column=1, pady=5, padx=5)
        self.target_channel_entry.insert(0, self.config.get("target_channel", ""))
        ToolTip(self.target_channel_entry, "Írd be a csatorna nevét vagy linkjét!")

        # --- Fájltípus beállítások ---
        filetype_labelframe = ttk.LabelFrame(container, text=self.texts["file_type_label"], padding=10)
        filetype_labelframe.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.file_type_var = tk.StringVar(value=self.config.get("file_type", "pdf"))
        ttk.Radiobutton(filetype_labelframe, text=self.texts["pdf_label"],
                        variable=self.file_type_var, value="pdf").pack(anchor="w", pady=2)
        ttk.Radiobutton(filetype_labelframe, text=self.texts["images_label"],
                        variable=self.file_type_var, value="images").pack(anchor="w", pady=2)
        ttk.Radiobutton(filetype_labelframe, text=self.texts["videos_label"],
                        variable=self.file_type_var, value="videos").pack(anchor="w", pady=2)
        ttk.Radiobutton(filetype_labelframe, text=self.texts["all_label"],
                        variable=self.file_type_var, value="all").pack(anchor="w", pady=2)
        ToolTip(filetype_labelframe, "Válaszd ki, mely típusú fájlokat szeretnéd letölteni!")

        # --- Kimeneti beállítások ---
        output_labelframe = ttk.LabelFrame(container, text=self.texts["output_label"], padding=10)
        output_labelframe.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        ttk.Label(output_labelframe, text=self.texts["save_dir_label"]).grid(row=0, column=0, sticky="w", pady=5)
        self.output_dir_entry = ttk.Entry(output_labelframe, width=40)
        self.output_dir_entry.grid(row=0, column=1, pady=5, padx=5)
        self.output_dir_entry.insert(0, self.config.get("output_dir", OUTPUT_DIR))
        ToolTip(self.output_dir_entry, "Írd be azt a könyvtárat, ahová a letöltött fájlok kerülnek!")
        ttk.Label(output_labelframe, text=self.texts["limit_label"]).grid(row=1, column=0, sticky="w", pady=5)
        self.download_limit_var = tk.IntVar(value=self.config.get("download_limit", 100))
        self.download_limit_entry = ttk.Entry(output_labelframe, textvariable=self.download_limit_var, width=10)
        self.download_limit_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        ToolTip(self.download_limit_entry, "Add meg, hány üzenet legyen feldolgozva!")

        # --- Speciális beállítások ---
        advanced_labelframe = ttk.LabelFrame(container, text=self.texts["advanced_settings"], padding=10)
        advanced_labelframe.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        # Eredetileg: Timeout, Proxy, Nyelv
        ttk.Label(advanced_labelframe, text=self.texts["timeout_label"]).grid(row=0, column=0, sticky="w", pady=5)
        self.timeout_entry = ttk.Entry(advanced_labelframe, width=10)
        self.timeout_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        self.timeout_entry.insert(0, self.config.get("timeout", ""))
        ToolTip(self.timeout_entry, "Állítsd be a letöltési időkorlátot (másodpercben)!")

        ttk.Label(advanced_labelframe, text=self.texts["proxy_label"]).grid(row=1, column=0, sticky="w", pady=5)
        self.proxy_entry = ttk.Entry(advanced_labelframe, width=20)
        self.proxy_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        self.proxy_entry.insert(0, self.config.get("proxy", ""))
        ToolTip(self.proxy_entry, "Adott esetben add meg a proxy-t (pl. host:port)!")

        ttk.Label(advanced_labelframe, text=self.texts["language_label"]).grid(row=2, column=0, sticky="w", pady=5)
        self.lang_menu_combobox = ttk.Combobox(advanced_labelframe, textvariable=self.lang_var,
                                               values=["en", "hu", "de"], width=8)
        self.lang_menu_combobox.grid(row=2, column=1, sticky="w", pady=5, padx=5)
        ToolTip(self.lang_menu_combobox, "Válaszd ki a felhasználói felület nyelvét!")
        self.lang_var.trace("w", lambda *args: self.change_language(self.lang_var.get()))

        # Új beállítások: Kezdő dátum, Min/Max fájlméret, Fájlnév minta, GitHub Token
        ttk.Label(advanced_labelframe, text=self.texts["start_date_label"]).grid(row=3, column=0, sticky="w", pady=5)
        self.start_date_entry = ttk.Entry(advanced_labelframe, width=10)
        self.start_date_entry.grid(row=3, column=1, sticky="w", pady=5, padx=5)
        self.start_date_entry.insert(0, self.config.get("start_date", ""))
        ToolTip(self.start_date_entry, "Add meg a kezdő dátumot (ÉÉÉÉ-HH-NN)!")

        ttk.Label(advanced_labelframe, text=self.texts["min_size_label"]).grid(row=4, column=0, sticky="w", pady=5)
        self.min_size_entry = ttk.Entry(advanced_labelframe, width=10)
        self.min_size_entry.grid(row=4, column=1, sticky="w", pady=5, padx=5)
        self.min_size_entry.insert(0, self.config.get("min_size", ""))
        ToolTip(self.min_size_entry, "Add meg a minimális fájlméretet MB-ban!")

        ttk.Label(advanced_labelframe, text=self.texts["max_size_label"]).grid(row=5, column=0, sticky="w", pady=5)
        self.max_size_entry = ttk.Entry(advanced_labelframe, width=10)
        self.max_size_entry.grid(row=5, column=1, sticky="w", pady=5, padx=5)
        self.max_size_entry.insert(0, self.config.get("max_size", ""))
        ToolTip(self.max_size_entry, "Add meg a maximális fájlméretet MB-ban!")

        ttk.Label(advanced_labelframe, text=self.texts["filename_pattern_label"]).grid(row=6, column=0, sticky="w", pady=5)
        self.filename_pattern_entry = ttk.Entry(advanced_labelframe, width=20)
        self.filename_pattern_entry.grid(row=6, column=1, sticky="w", pady=5, padx=5)
        self.filename_pattern_entry.insert(0, self.config.get("filename_pattern", ""))
        ToolTip(self.filename_pattern_entry, "Adja meg a fájlnév mintát (regex), ha szükséges!")

        ttk.Label(advanced_labelframe, text="GitHub Token:").grid(row=7, column=0, sticky="w", pady=5)
        self.github_token_entry = ttk.Entry(advanced_labelframe, width=20)
        self.github_token_entry.grid(row=7, column=1, sticky="w", pady=5, padx=5)
        self.github_token_entry.insert(0, self.config.get("github_token", ""))
        ToolTip(self.github_token_entry, "Adja meg a GitHub token-t, ha szükséges!")

        save_frame = ttk.Frame(container)
        save_frame.grid(row=2, column=0, columnspan=2, pady=10)
        self.save_button = ttk.Button(save_frame,
                                      text=self.texts["save_settings_button"],
                                      command=self.save_config)
        self.save_button.pack()

        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)

    def update_ui_texts(self):
        self.texts = LANG_DATA[self.selected_lang]
        self.root.title(self.texts["app_title"])
        self.notebook.tab(self.download_frame, text=self.texts["download_tab"])
        self.notebook.tab(self.settings_frame, text=self.texts["settings_tab"])
        self.title_label.config(text=self.texts["home_title"])
        self.subtitle_label.config(text=self.texts["home_subtitle"])
        self.progress_label.config(text=self.texts["waiting_label"])
        self.start_btn.config(text=self.texts["start_button"])
        self.pause_btn.config(text=self.texts["pause_button"])
        self.save_button.config(text=self.texts["save_settings_button"])
        self.status_bar.config(text=self.texts["ready_status"])
        self.rebuild_menus()

    def change_language(self, lang_code):
        self.selected_lang = lang_code
        self.config["lang"] = lang_code
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        self.update_ui_texts()

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{timestamp}: {message}"
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(full_message + "\n")
        self.log_text.insert(tk.END, full_message + "\n")
        self.log_text.see(tk.END)
        self.status_bar.config(text=message)
        self.root.update()

    def download_new_exe(self, url):
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open("update_new.exe", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except Exception as e:
            self.log_message(f"Hiba a letöltés során: {e}")
        return False

    def check_for_github_updates(self):
        owner = self.config.get("github_owner", "")
        repo = self.config.get("github_repo", "")
        token = self.config.get("github_token", "")
        if not owner or not repo:
            self.log_message("Hiányzik a github_owner vagy github_repo a config.json-ből. Állítsd be és próbáld újra.")
            return

        self.log_message("Frissítések keresése GitHub-on...")
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        headers = {"Authorization": f"token {token}"} if token else {}

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                latest_tag = data.get("tag_name")
                if latest_tag and latest_tag > CURRENT_VERSION:
                    self.log_message(f"Új verzió elérhető: {latest_tag}. Letöltés indul...")
                    assets = data.get("assets", [])
                    exe_url = next((asset.get("browser_download_url") for asset in assets
                                    if asset.get("name", "").endswith(".exe")), None)
                    if exe_url:
                        if self.download_new_exe(exe_url):
                            self.log_message("Frissítés letöltve (update_new.exe).")
                            messagebox.showinfo(self.texts["about_title"],
                                                "Frissítés letöltve update_new.exe néven.\nLépjen ki és futtassa azt a frissítés befejezéséhez.")
                        else:
                            self.log_message("A frissítés letöltése sikertelen.")
                    else:
                        self.log_message("Nem található exe asset a release-ben.")
                else:
                    self.log_message("Nincs újabb verzió elérhető.")
            else:
                self.log_message("Hiba a GitHub lekérdezés során.")
        except Exception as e:
            self.log_message(f"Hiba a frissítés ellenőrzése során: {e}")

    async def async_download_media(self, api_id, api_hash, target_channel, file_type,
                                   output_dir, download_limit, start_date_str):
        if not api_id or not api_hash or not target_channel:
            self.log_message(self.texts["missing_settings"])
            return

        try:
            async with TelegramClient('my_downloader_session', int(api_id), api_hash) as client:
                try:
                    entity = await client.get_entity(target_channel)
                    self.progress_label.config(text=self.texts["waiting_label"])
                    self.root.update()
                except errors.UsernameNotOccupiedError:
                    self.log_message(self.texts["channel_error"])
                    return
                except errors.FloodWaitError as e:
                    self.log_message(self.texts["flood_error"].format(sec=e.seconds))
                    return

                start_date_obj = None
                if start_date_str:
                    try:
                        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
                    except ValueError:
                        self.log_message(self.texts["no_messages"])
                        return

                all_messages = []
                async for msg in client.iter_messages(entity, limit=download_limit):
                    if start_date_obj and msg.date < start_date_obj:
                        continue
                    all_messages.append(msg)
                total_messages = len(all_messages)
                if total_messages == 0:
                    self.log_message(self.texts["no_messages"])
                    return

                self.progress_bar["maximum"] = total_messages

                for idx, message in enumerate(all_messages, start=1):
                    if self.download_paused:
                        while self.download_paused:
                            await asyncio.sleep(0.5)
                    try:
                        if message.document:
                            mime_type = message.document.mime_type
                            condition = (
                                (file_type == "pdf" and mime_type == 'application/pdf') or
                                (file_type == "images" and mime_type in ['image/jpeg', 'image/png']) or
                                (file_type == "videos" and mime_type == 'video/mp4') or
                                (file_type == "all")
                            )
                            if condition:
                                file_name_attr = None
                                for attr in message.document.attributes:
                                    if hasattr(attr, 'file_name'):
                                        file_name_attr = attr.file_name
                                        break
                                file_name = file_name_attr or f"document_{message.id}"
                                file_path = os.path.join(output_dir, file_name)
                                if not os.path.exists(file_path):
                                    await client.download_media(message, file=file_path)
                                    self.log_message(f"{self.texts['done_message']}: {file_path}")
                                else:
                                    self.log_message(f"{file_path} already exists, skipped")
                    except Exception as e:
                        self.log_message(f"Error processing message (ID: {message.id}): {e}")

                    self.progress_bar["value"] = idx
                    percentage = (idx / total_messages) * 100
                    self.progress_percentage.config(text=f"{percentage:.2f}%")
                    self.root.update()

                self.progress_label.config(text=self.texts["finished_download"])
                self.log_message(self.texts["finished_download"])
                self.root.update()

        except Exception as e:
            self.log_message(f"Error connecting to Telegram: {e}")

    def start_download(self):
        api_id_val = self.api_id_entry.get().strip()
        api_hash_val = self.api_hash_entry.get().strip()
        target_channel_val = self.target_channel_entry.get().strip()
        file_type_val = self.file_type_var.get()
        output_dir_val = self.output_dir_entry.get().strip()
        download_limit_val = self.download_limit_var.get()
        start_date_val = self.start_date_entry.get().strip() if hasattr(self, "start_date_entry") else ""

        if not api_id_val or not api_hash_val or not target_channel_val:
            messagebox.showwarning(self.texts["settings_tab"], self.texts["warning_settings"])
            return

        self.progress_bar["value"] = 0
        self.progress_percentage.config(text="0%")
        self.download_paused = False

        def run_download():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                self.async_download_media(api_id_val, api_hash_val, target_channel_val,
                                            file_type_val, output_dir_val, download_limit_val, start_date_val)
            )
        threading.Thread(target=run_download, daemon=True).start()

    def toggle_pause(self):
        self.download_paused = not self.download_paused
        if self.download_paused:
            self.pause_btn.config(text=self.texts["resume_button"])
            self.log_message("Letöltés szüneteltetve.")
        else:
            self.pause_btn.config(text=self.texts["pause_button"])
            self.log_message("Letöltés folytatva.")

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title(self.texts["about_title"])
        about_window.geometry("400x250")
        about_window.resizable(False, False)
        about_window.configure(bg='#F0F2F5')
        ttk.Label(about_window, text=self.texts["about_app"],
                  font=("Segoe UI", 16, "bold"), background='#F0F2F5', foreground="#333").pack(pady=(40, 10))
        ttk.Label(about_window, text=self.texts["about_author"],
                  font=("Segoe UI", 12), background='#F0F2F5', foreground="#555").pack(pady=5)
        ttk.Label(about_window, text=self.texts["about_version"],
                  font=("Segoe UI", 12), background='#F0F2F5', foreground="#555").pack(pady=5)
        ttk.Button(about_window, text="OK", command=about_window.destroy).pack(pady=20)
        about_window.transient(self.root)
        about_window.grab_set()
        self.root.wait_window(about_window)

    def show_mini_wiki(self):
        """Megjeleníti a mini wiki-t egy új ablakban, ahol részletes útmutatás található a beállításokról."""
        wiki_window = tk.Toplevel(self.root)
        wiki_window.title("Mini Wiki")
        wiki_window.geometry("600x400")
        wiki_text = scrolledtext.ScrolledText(wiki_window, wrap="word", font=("Segoe UI", 10))
        wiki_text.pack(fill="both", expand=True, padx=10, pady=10)
        instructions = (
            "=== Telegram Média Letöltő - Mini Wiki ===\n\n"
            "1. Általános beállítások:\n"
            "   - API ID: A Telegram API-hoz szükséges azonosító (csak számok).\n"
            "   - API Hash: A Telegram API használatához szükséges titkos kód.\n"
            "   - Csatorna neve/linkje: A Telegram csatorna azonosítója, ahonnan a médiát le szeretnéd tölteni.\n\n"
            "2. Fájltípus beállítások:\n"
            "   - Válaszd ki, milyen típusú fájlokat szeretnél letölteni (PDF, képek, videók, vagy mindegyik).\n\n"
            "3. Kimeneti beállítások:\n"
            "   - Mentési könyvtár: Az a mappa, ahová a letöltött fájlok kerülnek.\n"
            "   - Letöltési limit: Az üzenetek száma, amelyeket feldolgoz a program.\n\n"
            "4. Speciális beállítások:\n"
            "   - Letöltési időkorlát: Fájlonkénti maximális várakozás másodpercben.\n"
            "   - Proxy: Ha proxy-n keresztül szeretnéd használni, add meg a host:port formátumban.\n"
            "   - Kezdő dátum: Az az időpont, amely után a letöltés elindul (ÉÉÉÉ-HH-NN formátum).\n"
            "   - Min/Max fájlméret: Szűrés a fájlméret alapján (MB-ban).\n"
            "   - Fájlnév minta: Regex alapján szűrés, ha csak bizonyos nevű fájlokat szeretnél letölteni.\n"
            "   - GitHub Token: Opció a GitHub token megadására a frissítésekhez.\n\n"
            "5. GitHub frissítések:\n"
            "   - A config.json-ban a github_owner és github_repo értékek megadása kötelező, ha a program GitHub frissítések keresését szeretnéd használni.\n\n"
            "További információért keresd a dokumentációt vagy vedd fel a kapcsolatot a fejlesztővel."
        )
        wiki_text.insert("1.0", instructions)
        wiki_text.configure(state="disabled")

    def quit_app(self):
        if messagebox.askokcancel(self.texts["exit_menu"], f"{self.texts['exit_menu']}?"):
            self.root.destroy()


# --- Main Execution ---
if __name__ == '__main__':
    root = tk.Tk()
    app = TelegramMediaDownloaderApp(root)
    root.mainloop()
