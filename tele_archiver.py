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
CURRENT_VERSION = "1.5"
STATS_FILE = "download_stats.json"

# Statisztikák alapértelmezett értékei
DEFAULT_STATS = {
    "total_downloads": 0,
    "total_size": 0,
    "last_download": None,
    "download_history": [],
    "favorite_channels": []
}

class DownloadStats:
    def __init__(self):
        self.stats = self.load_stats()
    
    def load_stats(self):
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return DEFAULT_STATS.copy()
        return DEFAULT_STATS.copy()
    
    def save_stats(self):
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=4)
    
    def update_stats(self, file_size, channel_name):
        self.stats["total_downloads"] += 1
        self.stats["total_size"] += file_size
        self.stats["last_download"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Letöltési előzmények frissítése
        self.stats["download_history"].append({
            "date": self.stats["last_download"],
            "channel": channel_name,
            "size": file_size
        })
        
        # Csak az utolsó 100 letöltést tároljuk
        if len(self.stats["download_history"]) > 100:
            self.stats["download_history"] = self.stats["download_history"][-100:]
        
        # Kedvenc csatornák frissítése
        if channel_name not in self.stats["favorite_channels"]:
            self.stats["favorite_channels"].append(channel_name)
            if len(self.stats["favorite_channels"]) > 10:
                self.stats["favorite_channels"] = self.stats["favorite_channels"][-10:]
        
        self.save_stats()

class FilePreview:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Fájl előnézet")
        self.window.geometry("800x600")
        self.window.configure(bg='#FFFFFF')
        
        # Előnézeti terület
        self.preview_frame = ttk.Frame(self.window)
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Fájl információk
        self.info_frame = ttk.LabelFrame(self.preview_frame, text="Fájl információk")
        self.info_frame.pack(fill="x", pady=(0, 10))
        
        self.name_label = ttk.Label(self.info_frame, text="")
        self.name_label.pack(padx=10, pady=5)
        
        self.size_label = ttk.Label(self.info_frame, text="")
        self.size_label.pack(padx=10, pady=5)
        
        self.date_label = ttk.Label(self.info_frame, text="")
        self.date_label.pack(padx=10, pady=5)
        
        # Előnézeti terület
        self.preview_area = ttk.LabelFrame(self.preview_frame, text="Előnézet")
        self.preview_area.pack(fill="both", expand=True)
        
        self.preview_text = scrolledtext.ScrolledText(self.preview_area,
                                                    wrap="word",
                                                    font=("Consolas", 10))
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Gombok
        self.button_frame = ttk.Frame(self.preview_frame)
        self.button_frame.pack(fill="x", pady=10)
        
        ttk.Button(self.button_frame,
                  text="Letöltés",
                  command=self.download_file).pack(side="right", padx=5)
        
        ttk.Button(self.button_frame,
                  text="Bezárás",
                  command=self.window.destroy).pack(side="right", padx=5)
    
    def show_preview(self, file_info):
        self.name_label.config(text=f"Név: {file_info['name']}")
        self.size_label.config(text=f"Méret: {file_info['size']} MB")
        self.date_label.config(text=f"Dátum: {file_info['date']}")
        
        # Előnézet betöltése
        self.preview_text.delete("1.0", tk.END)
        if file_info['type'] == 'text':
            self.preview_text.insert("1.0", file_info['content'])
        else:
            self.preview_text.insert("1.0", f"Előnézet nem elérhető: {file_info['type']} fájl")
    
    def download_file(self):
        # Letöltés implementálása
        pass

class DownloadPreview:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Letöltési előnézet")
        self.window.geometry("1000x600")
        self.window.configure(bg='#FFFFFF')
        
        # Fájllista
        self.list_frame = ttk.LabelFrame(self.window, text="Letölthető fájlok")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Rendezési opciók
        sort_frame = ttk.Frame(self.list_frame)
        sort_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(sort_frame, text="Rendezés:").pack(side="left", padx=5)
        self.sort_var = tk.StringVar(value="date")
        ttk.Radiobutton(sort_frame, text="Dátum",
                       variable=self.sort_var,
                       value="date",
                       command=self.sort_files).pack(side="left", padx=5)
        ttk.Radiobutton(sort_frame, text="Méret",
                       variable=self.sort_var,
                       value="size",
                       command=self.sort_files).pack(side="left", padx=5)
        
        # Fájllista táblázat
        columns = ("name", "size", "date", "type")
        self.tree = ttk.Treeview(self.list_frame, columns=columns, show="headings")
        
        self.tree.heading("name", text="Név")
        self.tree.heading("size", text="Méret")
        self.tree.heading("date", text="Dátum")
        self.tree.heading("type", text="Típus")
        
        self.tree.column("name", width=300)
        self.tree.column("size", width=100)
        self.tree.column("date", width=150)
        self.tree.column("type", width=100)
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Görgetősáv
        scrollbar = ttk.Scrollbar(self.list_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Gombok
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Button(button_frame,
                  text="Kiválasztottak letöltése",
                  command=self.download_selected).pack(side="right", padx=5)
        
        ttk.Button(button_frame,
                  text="Összes letöltése",
                  command=self.download_all).pack(side="right", padx=5)
        
        ttk.Button(button_frame,
                  text="Bezárás",
                  command=self.window.destroy).pack(side="right", padx=5)
    
    def show_preview(self, files):
        self.tree.delete(*self.tree.get_children())
        for file in files:
            self.tree.insert("", "end", values=(
                file["name"],
                f"{file['size']:.1f} MB",
                file["date"],
                file["type"]
            ))
    
    def sort_files(self):
        items = self.tree.get_children()
        if not items:
            return
        
        sort_by = self.sort_var.get()
        if sort_by == "date":
            items.sort(key=lambda x: self.tree.item(x)["values"][2])
        else:  # size
            items.sort(key=lambda x: float(self.tree.item(x)["values"][1].split()[0]))
        
        for item in items:
            self.tree.move(item, "", "end")
    
    def download_selected(self):
        selected = self.tree.selection()
        # Letöltés implementálása
        pass
    
    def download_all(self):
        # Összes letöltése implementálása
        pass

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
        self.root.configure(bg='#FFFFFF')
        ttk.Style().theme_use('clam')
        
        # Statisztikák inicializálása
        self.stats = DownloadStats()
        
        # Automatikus mentés időzítő
        self.auto_save_timer = None
        
        # Beállítjuk az alkalmazás ikonját, ha elérhető
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                print("Icon file not found at:", icon_path)
        except Exception as e:
            print("Icon not found or error loading icon:", e)

        self.config = self.load_config()
        self.selected_lang = self.config.get("lang", "hu")
        self.lang_var = tk.StringVar(value=self.selected_lang)
        self.texts = LANG_DATA[self.selected_lang]
        self.download_paused = False

        self.create_styles()
        self.create_menus()
        self.create_toolbar()
        self.create_ui()
        self.update_ui_texts()
        
        # Statisztikák frissítése
        self.update_stats_display()
        
        # Automatikus mentés indítása
        self.start_auto_save()

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
        # Modern gomb stílus
        self.style.configure("TButton",
                             font=("Segoe UI", 11),
                             padding=10,
                             relief="flat",
                             background="#2196F3",
                             foreground="white")
        self.style.map("TButton",
                       background=[("active", "#1976D2")],
                       foreground=[("active", "white")])
        
        # Modern címke stílus
        self.style.configure("TLabel", 
                           font=("Segoe UI", 11), 
                           background='#FFFFFF', 
                           foreground="#212121")
        self.style.configure("Header.TLabel", 
                           font=("Segoe UI", 24, "bold"), 
                           background='#FFFFFF', 
                           foreground="#1976D2")
        self.style.configure("SubHeader.TLabel", 
                           font=("Segoe UI", 14), 
                           background='#FFFFFF', 
                           foreground="#757575")
        
        # Modern beviteli mező stílus
        self.style.configure("TEntry", 
                           font=("Segoe UI", 11),
                           padding=8,
                           fieldbackground="#F5F5F5",
                           borderwidth=0)
        
        # Modern notebook stílus
        self.style.configure("TNotebook", 
                           background='#FFFFFF',
                           tabmargins=[2, 5, 2, 0])
        self.style.configure("TNotebook.Tab",
                           padding=[15, 5],
                           font=("Segoe UI", 10))
        self.style.map("TNotebook.Tab",
                      background=[("selected", "#E3F2FD")],
                      foreground=[("selected", "#1976D2")])
        
        # Modern keret stílus
        self.style.configure("TFrame", 
                           background='#FFFFFF')
        
        # Modern progress bar stílus
        self.style.configure("Horizontal.TProgressbar",
                           troughcolor='#F5F5F5',
                           background='#2196F3',
                           thickness=8)
        
        # Modern LabelFrame stílus
        self.style.configure("TLabelframe",
                           background='#FFFFFF',
                           foreground="#212121",
                           font=("Segoe UI", 11, "bold"))
        self.style.configure("TLabelframe.Label",
                           background='#FFFFFF',
                           foreground="#1976D2",
                           font=("Segoe UI", 11, "bold"))
        
        # Modern Combobox stílus
        self.style.configure("TCombobox",
                           background="#F5F5F5",
                           fieldbackground="#F5F5F5",
                           selectbackground="#E3F2FD",
                           selectforeground="#1976D2")
        
        # Modern Spinbox stílus
        self.style.configure("TSpinbox",
                           background="#F5F5F5",
                           fieldbackground="#F5F5F5")

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
        self.menubar.add_cascade(label=self.texts["file_menu"], menu=file_menu)

        # Settings Menu
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        settings_menu.add_command(label=self.texts["settings_submenu"], command=self.show_settings)
        self.menubar.add_cascade(label=self.texts["settings_submenu"], menu=settings_menu)

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

    def create_ui(self):
        # Fő keret
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Notebook létrehozása
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Frame-ek létrehozása
        self.download_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)
        self.advanced_frame = ttk.Frame(self.notebook)
        
        # Frame-ek hozzáadása a notebook-hoz
        self.notebook.add(self.download_frame, text="Letöltés")
        self.notebook.add(self.settings_frame, text="Beállítások")
        self.notebook.add(self.advanced_frame, text="Haladó")
        
        # Fejléc
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Logo és cím
        logo_frame = ttk.Frame(header_frame)
        logo_frame.pack(side="left", fill="x", expand=True)
        
        self.title_label = ttk.Label(logo_frame,
                                   text="Telegram Média Letöltő",
                                   font=("Helvetica", 24, "bold"))
        self.title_label.pack(side="left", padx=(0, 20))
        
        self.subtitle_label = ttk.Label(logo_frame,
                                      text="v" + CURRENT_VERSION,
                                      font=("Helvetica", 12))
        self.subtitle_label.pack(side="left")
        
        # Statisztikák
        stats_frame = ttk.LabelFrame(header_frame, text="Statisztikák")
        stats_frame.pack(side="right", fill="x", padx=(20, 0))
        
        self.total_downloads_label = ttk.Label(stats_frame, text="Összes letöltés: 0")
        self.total_downloads_label.pack(side="left", padx=10, pady=5)
        
        self.total_size_label = ttk.Label(stats_frame, text="Összes méret: 0 MB")
        self.total_size_label.pack(side="left", padx=10, pady=5)
        
        # Tab-ok tartalmának létrehozása
        self.create_download_tab()
        self.create_settings_tab()
        self.create_advanced_tab()

    def create_download_tab(self):
        # Fő konténer
        main_frame = ttk.Frame(self.download_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Csatorna beállítások
        channel_frame = ttk.LabelFrame(main_frame, text="Csatorna beállítások")
        channel_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(channel_frame, text="Csatorna:").pack(padx=10, pady=5)
        self.target_channel_entry = ttk.Entry(channel_frame, width=50)
        self.target_channel_entry.pack(padx=10, pady=5)
        self.target_channel_entry.insert(0, self.config.get("target_channel", ""))
        
        # Fájltípus választó
        file_type_frame = ttk.LabelFrame(main_frame, text="Fájltípus")
        file_type_frame.pack(fill="x", pady=(0, 10))
        
        self.file_type_var = tk.StringVar(value=self.config.get("file_type", "all"))
        ttk.Radiobutton(file_type_frame, text="PDF", 
                       variable=self.file_type_var, value="pdf").pack(padx=10, pady=2)
        ttk.Radiobutton(file_type_frame, text="Képek", 
                       variable=self.file_type_var, value="images").pack(padx=10, pady=2)
        ttk.Radiobutton(file_type_frame, text="Videók", 
                       variable=self.file_type_var, value="videos").pack(padx=10, pady=2)
        ttk.Radiobutton(file_type_frame, text="Összes", 
                       variable=self.file_type_var, value="all").pack(padx=10, pady=2)
        
        # Letöltési beállítások
        download_frame = ttk.LabelFrame(main_frame, text="Letöltési beállítások")
        download_frame.pack(fill="x", pady=(0, 10))
        
        # Letöltési limit
        limit_frame = ttk.Frame(download_frame)
        limit_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(limit_frame, text="Letöltési limit:").pack(side="left")
        self.download_limit_var = tk.IntVar(value=self.config.get("download_limit", 100))
        limit_spinbox = ttk.Spinbox(limit_frame, from_=1, to=1000, 
                                  textvariable=self.download_limit_var)
        limit_spinbox.pack(side="left", padx=5)
        
        # Párhuzamos letöltések
        parallel_frame = ttk.Frame(download_frame)
        parallel_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(parallel_frame, text="Párhuzamos letöltések:").pack(side="left")
        self.parallel_spinbox = ttk.Spinbox(parallel_frame, from_=1, to=10, width=5)
        self.parallel_spinbox.set(3)
        self.parallel_spinbox.pack(side="left", padx=5)
        
        # Napló
        log_frame = ttk.LabelFrame(main_frame, text="Napló")
        log_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Folyamatjelző
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame,
                                          variable=self.progress_var,
                                          maximum=100)
        self.progress_bar.pack(side="left", fill="x", expand=True)
        
        self.progress_percentage = ttk.Label(progress_frame, text="0%")
        self.progress_percentage.pack(side="right", padx=(10, 0))
        
        # Státusz címke
        self.progress_label = ttk.Label(main_frame, text="Várakozás a letöltésre...")
        self.progress_label.pack(fill="x", pady=(0, 10))
        
        # Gombok
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Előnézet",
                  command=self.show_download_preview).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Letöltés indítása",
                  command=self.start_download).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Szüneteltetés",
                  command=self.toggle_pause).pack(side="left", padx=5)

    def create_settings_tab(self):
        # Görgetősáv létrehozása
        canvas = tk.Canvas(self.settings_frame)
        scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Görgetősáv és canvas elrendezése
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # API beállítások
        api_frame = ttk.LabelFrame(scrollable_frame, text="API beállítások")
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(api_frame, text="API ID:").pack(padx=10, pady=5)
        self.api_id_entry = ttk.Entry(api_frame, width=30)
        self.api_id_entry.pack(padx=10, pady=5)
        self.api_id_entry.insert(0, self.config.get("api_id", ""))
        
        ttk.Label(api_frame, text="API Hash:").pack(padx=10, pady=5)
        self.api_hash_entry = ttk.Entry(api_frame, width=50)
        self.api_hash_entry.pack(padx=10, pady=5)
        self.api_hash_entry.insert(0, self.config.get("api_hash", ""))
        
        # Kimeneti beállítások
        output_frame = ttk.LabelFrame(scrollable_frame, text="Kimeneti beállítások")
        output_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(output_frame, text="Mentési könyvtár:").pack(padx=10, pady=5)
        self.output_dir_entry = ttk.Entry(output_frame, width=50)
        self.output_dir_entry.pack(padx=10, pady=5)
        self.output_dir_entry.insert(0, self.config.get("output_dir", OUTPUT_DIR))
        
        # Nyelv beállítások
        lang_frame = ttk.LabelFrame(scrollable_frame, text="Nyelv beállítások")
        lang_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(lang_frame, text="Nyelv:").pack(padx=10, pady=5)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, 
                                values=["hu", "en", "de"], state="readonly")
        lang_combo.pack(padx=10, pady=5)
        
        # Mentés gomb
        self.save_button = ttk.Button(scrollable_frame, 
                                    text="Beállítások mentése",
                                    command=self.save_config)
        self.save_button.pack(pady=10)

    def create_advanced_tab(self):
        # Görgetősáv létrehozása
        canvas = tk.Canvas(self.advanced_frame)
        scrollbar = ttk.Scrollbar(self.advanced_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Görgetősáv és canvas elrendezése
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Haladó szűrés
        filter_frame = ttk.LabelFrame(scrollable_frame, text="Haladó szűrés")
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Dátum szűrés
        date_frame = ttk.Frame(filter_frame)
        date_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(date_frame, text="Kezdő dátum (ÉÉÉÉ-HH-NN):").pack(side="left")
        self.start_date_entry = ttk.Entry(date_frame, width=20)
        self.start_date_entry.pack(side="left", padx=5)
        self.start_date_entry.insert(0, self.config.get("start_date", ""))
        
        # Fájlméret szűrés
        size_frame = ttk.Frame(filter_frame)
        size_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(size_frame, text="Min. méret (MB):").pack(side="left")
        self.min_size_entry = ttk.Entry(size_frame, width=10)
        self.min_size_entry.pack(side="left", padx=5)
        
        ttk.Label(size_frame, text="Max. méret (MB):").pack(side="left", padx=(10, 0))
        self.max_size_entry = ttk.Entry(size_frame, width=10)
        self.max_size_entry.pack(side="left", padx=5)
        self.max_size_entry.insert(0, self.config.get("max_size", ""))
        
        # Fájlnév minta
        pattern_frame = ttk.Frame(filter_frame)
        pattern_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(pattern_frame, text="Fájlnév minta (regex):").pack(side="left")
        self.filename_pattern_entry = ttk.Entry(pattern_frame, width=40)
        self.filename_pattern_entry.pack(side="left", padx=5)
        self.filename_pattern_entry.insert(0, self.config.get("filename_pattern", ""))
        
        # Proxy beállítások
        proxy_frame = ttk.LabelFrame(scrollable_frame, text="Proxy beállítások")
        proxy_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(proxy_frame, text="Proxy (host:port):").pack(padx=10, pady=5)
        self.proxy_entry = ttk.Entry(proxy_frame, width=50)
        self.proxy_entry.pack(padx=10, pady=5)
        self.proxy_entry.insert(0, self.config.get("proxy", ""))
        
        # Időkorlát beállítások
        timeout_frame = ttk.LabelFrame(scrollable_frame, text="Időkorlát beállítások")
        timeout_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(timeout_frame, text="Letöltési időkorlát (mp/fájl):").pack(padx=10, pady=5)
        self.timeout_entry = ttk.Entry(timeout_frame, width=10)
        self.timeout_entry.pack(padx=10, pady=5)
        self.timeout_entry.insert(0, self.config.get("timeout", ""))
        
        # GitHub beállítások
        github_frame = ttk.LabelFrame(scrollable_frame, text="GitHub beállítások")
        github_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(github_frame, text="GitHub Token:").pack(padx=10, pady=5)
        self.github_token_entry = ttk.Entry(github_frame, width=50)
        self.github_token_entry.pack(padx=10, pady=5)
        self.github_token_entry.insert(0, self.config.get("github_token", ""))

    def update_ui_texts(self):
        self.texts = LANG_DATA[self.selected_lang]
        self.root.title(self.texts["app_title"])
        self.notebook.tab(self.download_frame, text=self.texts["download_tab"])
        self.notebook.tab(self.settings_frame, text=self.texts["settings_tab"])
        self.title_label.config(text=self.texts["home_title"])
        self.subtitle_label.config(text=self.texts["home_subtitle"])
        if hasattr(self, 'progress_label'):
            self.progress_label.config(text=self.texts["waiting_label"])
        self.start_btn.config(text=self.texts["start_button"])
        self.pause_btn.config(text=self.texts["pause_button"])
        self.save_button.config(text=self.texts["save_settings_button"])
        self.rebuild_menus()

    def change_language(self, lang_code):
        self.selected_lang = lang_code
        self.config["lang"] = lang_code
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)
        self.update_ui_texts()

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(full_message + "\n")
        self.log_text.insert(tk.END, full_message + "\n")
        self.log_text.see(tk.END)
        self.status_label.config(text=message)
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

    async def download_media(self, message, output_dir):
        try:
            if message.media:
                # Fájl típusának meghatározása
                file_type = self.get_file_type(message.media)
                
                # Szűrés ellenőrzése
                if not self.check_filters(message, file_type):
                    return
                
                # Fájl nevének meghatározása
                file_name = self.get_file_name(message, file_type)
                file_path = os.path.join(output_dir, file_name)
                
                # Fájl méretének meghatározása
                file_size = self.get_file_size(message.media)
                
                # Fájl előnézet létrehozása
                file_info = {
                    "name": file_name,
                    "size": file_size / (1024 * 1024),  # MB
                    "date": message.date.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": file_type
                }
                
                # Fájl letöltése
                await message.download_media(file_path)
                
                # Statisztikák frissítése
                self.stats.update_stats(file_size / (1024 * 1024), message.chat.title)
                self.update_stats_display()
                
                # Naplózás
                self.log(f"Letöltve: {file_name} ({file_size / (1024 * 1024):.1f} MB)")
                
                return file_info
        except Exception as e:
            self.log(f"Hiba a letöltés során: {str(e)}")
            return None
    
    def check_filters(self, message, file_type):
        # Fájltípus szűrés
        if not self.type_vars[file_type].get():
            return False
        
        # Méret szűrés
        file_size = self.get_file_size(message.media) / (1024 * 1024)  # MB
        try:
            min_size = float(self.min_size_entry.get() or 0)
            max_size = float(self.max_size_entry.get() or float('inf'))
            if not (min_size <= file_size <= max_size):
                return False
        except ValueError:
            pass
        
        # Dátum szűrés
        try:
            start_date = datetime.strptime(self.start_date_entry.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_entry.get(), "%Y-%m-%d")
            if not (start_date <= message.date <= end_date):
                return False
        except ValueError:
            pass
        
        return True
    
    def get_file_type(self, media):
        if hasattr(media, 'photo'):
            return 'photo'
        elif hasattr(media, 'video'):
            return 'video'
        elif hasattr(media, 'document'):
            return 'document'
        elif hasattr(media, 'audio'):
            return 'audio'
        elif hasattr(media, 'text'):
            return 'text'
        return 'unknown'
    
    def get_file_name(self, message, file_type):
        if hasattr(message.media, 'document'):
            return message.media.document.attributes[0].file_name
        elif hasattr(message.media, 'photo'):
            return f"photo_{message.id}.jpg"
        elif hasattr(message.media, 'video'):
            return f"video_{message.id}.mp4"
        elif hasattr(message.media, 'audio'):
            return f"audio_{message.id}.mp3"
        elif hasattr(message.media, 'text'):
            return f"text_{message.id}.txt"
        return f"file_{message.id}"
    
    def get_file_size(self, media):
        if hasattr(media, 'document'):
            return media.document.size
        elif hasattr(media, 'photo'):
            return sum(photo.size for photo in media.photo.sizes)
        elif hasattr(media, 'video'):
            return media.video.size
        elif hasattr(media, 'audio'):
            return media.audio.size
        return 0
    
    async def start_download(self):
        try:
            # API beállítások ellenőrzése
            api_id = self.api_id_entry.get()
            api_hash = self.api_hash_entry.get()
            if not api_id or not api_hash:
                self.log("Hiba: API ID és API Hash megadása kötelező!")
                return
            
            # Csatorna ellenőrzése
            channel = self.channel_entry.get()
            if not channel:
                self.log("Hiba: Csatorna megadása kötelező!")
                return
            
            # Letöltési beállítások
            parallel_downloads = int(self.parallel_spinbox.get())
            max_retries = int(self.retry_spinbox.get())
            
            # Kimeneti könyvtár létrehozása
            output_dir = os.path.join(OUTPUT_DIR, channel)
            os.makedirs(output_dir, exist_ok=True)
            
            # Telegram kliens inicializálása
            client = TelegramClient('anon', api_id, api_hash)
            await client.start()
            
            # Csatorna üzeneteinek lekérése
            messages = await client.get_messages(channel)
            
            # Fájlok szűrése és előnézet létrehozása
            files = []
            for message in messages:
                if message.media:
                    file_info = await self.download_media(message, output_dir)
                    if file_info:
                        files.append(file_info)
            
            # Előnézet megjelenítése
            self.show_download_preview(files)
            
            # Letöltés indítása
            self.progress_var.set(0)
            total_files = len(files)
            
            for i, file_info in enumerate(files):
                if self.download_paused:
                    await asyncio.sleep(1)
                    continue
                
                # Folyamatjelző frissítése
                progress = (i + 1) / total_files * 100
                self.progress_var.set(progress)
                self.status_label.config(text=f"Letöltés: {i + 1}/{total_files}")
                
                # Letöltés újrapróbálása
                for retry in range(max_retries):
                    try:
                        await self.download_media(message, output_dir)
                        break
                    except Exception as e:
                        if retry == max_retries - 1:
                            self.log(f"Hiba a letöltés során: {str(e)}")
                        await asyncio.sleep(1)
            
            self.status_label.config(text="Letöltés befejezve!")
            
        except Exception as e:
            self.log(f"Hiba: {str(e)}")
        finally:
            if 'client' in locals():
                await client.disconnect()
    
    def toggle_pause(self):
        self.download_paused = not self.download_paused
        self.status_label.config(
            text="Letöltés szüneteltetve" if self.download_paused else "Letöltés folytatva")
    
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title(self.texts["about_title"])
        about_window.geometry("1200x900")
        about_window.resizable(False, False)
        about_window.configure(bg='#F0F2F5')
        
        # Fő konténer
        main_frame = ttk.Frame(about_window)
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Fejléc
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill="x", pady=(0, 30))
        
        # Alkalmazás neve és verzió
        ttk.Label(header_frame, text=self.texts["about_app"],
                  font=("Segoe UI", 32, "bold"), background='#F0F2F5', foreground="#1976D2").pack(pady=(0, 15))
        
        # Verzió és fejlesztő
        info_frame = ttk.Frame(header_frame)
        info_frame.pack(fill="x")
        
        ttk.Label(info_frame, text=f"Verzió: {CURRENT_VERSION}",
                  font=("Segoe UI", 16), background='#F0F2F5', foreground="#555").pack(side="left", padx=15)
        
        ttk.Label(info_frame, text=self.texts["about_author"],
                  font=("Segoe UI", 16), background='#F0F2F5', foreground="#555").pack(side="left", padx=15)
        
        # Elválasztó vonal
        ttk.Separator(main_frame, orient='horizontal').pack(fill='x', pady=30)
        
        # Részletes információk
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Bal oldali panel - Alkalmazás leírása
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 30))
        
        ttk.Label(left_panel, text="Alkalmazás leírása",
                  font=("Segoe UI", 20, "bold"), background='#F0F2F5', foreground="#1976D2").pack(pady=(0, 15))
        
        description_text = (
            "A Telegram Média Letöltő egy modern és hatékony eszköz, "
            "amely segít a Telegram csatornákról való médiatartalmak "
            "könnyű és gyors letöltésében. Az alkalmazás felhasználóbarát "
            "felülettel és fejlett funkciókkal rendelkezik, hogy a letöltési "
            "folyamat minél hatékonyabb legyen.\n\n"
            "Az alkalmazás segítségével könnyedén letöltheted a kedvenc "
            "Telegram csatornáid médiatartalmait, szűrheted őket típus, "
            "méret és dátum szerint, valamint követheted a letöltési "
            "statisztikákat is."
        )
        
        ttk.Label(left_panel, text=description_text, justify='left',
                 font=("Segoe UI", 12), background='#F0F2F5').pack(pady=(0, 25))
        
        ttk.Label(left_panel, text="Főbb funkciók",
                  font=("Segoe UI", 20, "bold"), background='#F0F2F5', foreground="#1976D2").pack(pady=(0, 15))
        
        features_text = (
            "• Több fájltípus támogatása (képek, videók, dokumentumok, hangfájlok)\n"
            "• Részletes szűrési lehetőségek (típus, méret, dátum)\n"
            "• Párhuzamos letöltések a gyorsabb folyamat érdekében\n"
            "• Automatikus újrapróbálkozás hiba esetén\n"
            "• Statisztikák követése és megjelenítése\n"
            "• Többnyelvű felület (magyar, angol, német)\n"
            "• Proxy támogatás speciális hálózati beállításokhoz\n"
            "• Automatikus frissítések az új funkciókhoz\n"
            "• Felhasználóbarát felület és könnyű kezelhetőség\n"
            "• Részletes naplózás és hibakezelés"
        )
        
        ttk.Label(left_panel, text=features_text, justify='left',
                 font=("Segoe UI", 12), background='#F0F2F5').pack(pady=(0, 25))
        
        # Jobb oldali panel - Kapcsolat és jogi információk
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True)
        
        ttk.Label(right_panel, text="Kapcsolat",
                  font=("Segoe UI", 20, "bold"), background='#F0F2F5', foreground="#1976D2").pack(pady=(0, 15))
        
        contact_text = (
            "Fejlesztő: OnNkode\n\n"
            "GitHub: https://github.com/OneNkode\n"
            "Email: onnkode@gmail.com\n"
            "Telegram: @OnNkode\n"
            "Telegram Csoport: https://t.me/+g-EKpEjQLRRmMzU0\n\n"
            "© 2024 OnNkode. Minden jog fenntartva."
        )
        
        ttk.Label(right_panel, text=contact_text, justify='left',
                 font=("Segoe UI", 12), background='#F0F2F5').pack(pady=(0, 25))
        
        # Gombok
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(30, 40))
        
        ttk.Button(button_frame, text="GitHub", 
                  command=lambda: os.startfile("https://github.com/OneNkode")).pack(side='left', padx=15)
        
        ttk.Button(button_frame, text="Telegram", 
                  command=lambda: os.startfile("https://t.me/OnNkode")).pack(side='left', padx=15)
        
        ttk.Button(button_frame, text="OK", 
                  command=about_window.destroy).pack(side='right', padx=15)
        
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

    def update_stats_display(self):
        self.total_downloads_label.config(
            text=f"Összes letöltés: {self.stats.stats['total_downloads']}")
        self.total_size_label.config(
            text=f"Összes méret: {self.stats.stats['total_size']:.1f} MB")

    def start_auto_save(self):
        # 5 percenként automatikus mentés
        self.auto_save_timer = self.root.after(300000, self.auto_save)

    def auto_save(self):
        self.save_config()
        self.stats.save_stats()
        # Új időzítő indítása
        self.start_auto_save()

    def show_file_preview(self, file_info):
        preview = FilePreview(self.root)
        preview.show_preview(file_info)

    def show_download_preview(self, files):
        preview = DownloadPreview(self.root)
        preview.show_preview(files)

    def show_settings(self):
        """Megjeleníti a beállítások ablakot."""
        self.notebook.select(self.settings_frame)


# --- Main Execution ---
if __name__ == '__main__':
    root = tk.Tk()
    app = TelegramMediaDownloaderApp(root)
    root.mainloop()
