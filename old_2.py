import os
import sys
import json
import threading
import asyncio
import platform
import ctypes
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
from telethon import TelegramClient, errors
import requests

# Alapértelmezett kimeneti mappa
output_dir = 'media_letoltes'
os.makedirs(output_dir, exist_ok=True)



# Naplófájl
log_file = "download_log.txt"

lang_data = {
    "hu": {
        "app_title": "Telegram Média Letöltő",
        "home_title": "Telegram Média Letöltés",
        "home_subtitle": "Egyszerűen töltsd le a csatornáid médiatartalmait!",
        "log_label": "Napló",
        "waiting_label": "Várakozás a letöltésre...",
        "start_button": "Indítás",
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
        "done_message": "A letöltés befejeződött!",
        "missing_settings": "Hiányzó beállítások! Kérjük, adja meg az API ID-t, API Hash-t és a csatornát.",
        "channel_error": "Hiba: A megadott csatorna nem található.",
        "flood_error": "Túl sok kérés. Várjon {sec} másodpercet, és próbálja újra.",
        "no_messages": "Nincsenek letölthető üzenetek a megadott feltételekkel.",
        "finished_download": "Media letöltése befejeződött.",
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
        "check_updates_button": "Frissítések keresése"
    }
}

selected_lang = "hu"
current_version = "1.3"

if not os.path.exists('config.json'):
    default_config = {
        "api_id": "",
        "api_hash": "",
        "target_channel": "",
        "file_type": "pdf",
        "output_dir": output_dir,
        "download_limit": 100,
        "lang": selected_lang,
        "github_owner": "OneNkode",
        "github_repo": "TeleArchiver"
    }
    with open('config.json', 'w') as config_file:
        json.dump(default_config, config_file)

try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    config = {
        "api_id": "",
        "api_hash": "",
        "target_channel": "",
        "file_type": "pdf",
        "output_dir": output_dir,
        "download_limit": 100,
        "lang": selected_lang,
        "github_owner": "OneNkode",
        "github_repo": "TeleArchiver"
    }

selected_lang = config.get("lang", selected_lang)

root = tk.Tk()
root.geometry("1200x800")
root.configure(bg='#2C3E50')
root.option_add('*Font', 'Helvetica 12')

style = ttk.Style()
style.configure("TButton", font=("Helvetica", 13), padding=10)
style.configure("TFrame", background='#34495E')
style.configure("TLabelframe", background='#34495E', foreground='white')
style.configure("TLabelframe.Label", foreground='white', background='#34495E', font=("Helvetica", 14, 'bold'))
style.configure("TLabel", background='#34495E', foreground='white', font=("Helvetica", 12))

def log_message(message):
    texts = lang_data[selected_lang]
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"{datetime.now()}: {message}\n")
    progress_text.insert(tk.END, message + "\n")
    progress_text.see(tk.END)
    status_bar.config(text=message)

def download_new_exe(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open("update_new.exe", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
    except Exception as e:
        log_message(f"Hiba a letöltés során: {e}")
    return False





def check_for_github_updates():
    texts = lang_data[selected_lang]

    owner = config.get("github_owner", "")
    repo = config.get("github_repo", "")
    token = config.get("github_token", "")

    if not owner or not repo:
        log_message("Hiányzik a github_owner vagy github_repo a config.json-ből. Állítsd be és próbáld újra.")
        return

    log_message("Frissítések keresése GitHub-on...")

    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            latest_tag = data.get("tag_name", None)
            if latest_tag and latest_tag > current_version:
                log_message(f"Új verzió elérhető: {latest_tag}. Letöltés indul...")
                assets = data.get("assets", [])
                exe_url = None
                for asset in assets:
                    name = asset.get("name", "")
                    browser_download_url = asset.get("browser_download_url", "")
                    if name.endswith(".exe"):
                        exe_url = browser_download_url
                        break
                if exe_url:
                    if download_new_exe(exe_url):
                        log_message("Frissítés letöltve (update_new.exe).")
                        messagebox.showinfo(texts["about_title"], 
                                            "Frissítés letöltve update_new.exe néven.\nLépjen ki és futtassa azt a frissítés befejezéséhez.")
                    else:
                        log_message("A frissítés letöltése sikertelen.")
                else:
                    log_message("Nem található exe asset a release-ben.")
            else:
                log_message("Nincs újabb verzió elérhető.")
        else:
            log_message("Hiba a GitHub lekérdezés során.")
    except Exception as e:
        log_message(f"Hiba a frissítés ellenőrzése során: {e}")

        

def save_config():
    config["api_id"] = api_id_entry.get().strip()
    config["api_hash"] = api_hash_entry.get().strip()
    config["target_channel"] = target_channel_entry.get().strip()
    config["file_type"] = file_type_var.get()
    config["output_dir"] = output_dir_entry.get().strip()
    config["download_limit"] = download_limit_var.get()
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)
    texts = lang_data[selected_lang]
    messagebox.showinfo(texts["settings_tab"], texts["saved_settings"])

def rebuild_menus():
    texts = lang_data[selected_lang]

    menubar.delete(0, 'end')

    fajl_menu = tk.Menu(menubar, tearoff=0, bg='#2C3E50', fg='white', activebackground='#16A085', activeforeground='white')
    fajl_menu.add_command(label=texts["exit_menu"], command=quit_app)

    lang_menu = tk.Menu(fajl_menu, tearoff=0, bg='#2C3E50', fg='white', activebackground='#16A085', activeforeground='white')
    settings_submenu = tk.Menu(lang_menu, tearoff=0, bg='#2C3E50', fg='white', activebackground='#16A085', activeforeground='white')
    settings_submenu.add_command(label=texts["lang_english"], command=lambda: change_language("en"))
    settings_submenu.add_command(label=texts["lang_hungarian"], command=lambda: change_language("hu"))
    settings_submenu.add_command(label=texts["lang_german"], command=lambda: change_language("de"))
    lang_menu.add_cascade(label=texts["lang_menu_title"], menu=settings_submenu)

    fajl_menu.add_cascade(label=texts["settings_submenu"], menu=lang_menu)
    fajl_menu.add_separator()
    fajl_menu.add_command(label=texts["check_updates_button"], command=check_for_github_updates)

    menubar.add_cascade(label=texts["file_menu"], menu=fajl_menu)

    sugo_menu = tk.Menu(menubar, tearoff=0, bg='#2C3E50', fg='white', activebackground='#16A085', activeforeground='white')
    sugo_menu.add_command(label=texts["about_menu"], command=show_about)
    menubar.add_cascade(label=texts["help_menu"], menu=sugo_menu)

def change_language(lang_code):
    global selected_lang
    selected_lang = lang_code
    config["lang"] = lang_code
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file)
    rebuild_menus()
    update_ui_texts()

def update_ui_texts():
    texts = lang_data[selected_lang]
    root.title(texts["app_title"])
    notebook.tab(download_frame, text=texts["download_tab"])
    notebook.tab(settings_frame, text=texts["settings_tab"])
    title_label.config(text=texts["home_title"])
    subtitle_label.config(text=texts["home_subtitle"])
    card_label.config(text=texts["log_label"])
    progress_label.config(text=texts["waiting_label"])
    start_button.config(text=texts["start_button"])
    general_settings.config(text=texts["config_label_general"])
    output_settings.config(text=texts["output_label"])
    file_type_frame.config(text=texts["file_type_label"])
    filter_frame.config(text=texts["advanced_filter"])
    advanced_settings.config(text=texts["advanced_settings"])
    save_button.config(text=texts["save_settings_button"])
    status_bar.config(text=texts["ready_status"])
    

def show_about():
    texts = lang_data[selected_lang]
    about_window = tk.Toplevel(root)
    about_window.title(texts["about_title"])
    about_window.configure(bg='#2C3E50')
    about_window.geometry("400x250")
    about_window.resizable(False, False)

    tk.Label(about_window, text=texts["about_app"], font=("Helvetica", 16, 'bold'), bg='#2C3E50', fg='white').pack(pady=(40,10))
    tk.Label(about_window, text=texts["about_author"], font=("Helvetica", 12), bg='#2C3E50', fg='white').pack(pady=(0,5))
    tk.Label(about_window, text=texts["about_version"], font=("Helvetica", 12), bg='#2C3E50', fg='white').pack(pady=(0,20))
    ttk.Button(about_window, text="OK", command=about_window.destroy).pack(pady=(0,20))

    about_window.transient(root)
    about_window.grab_set()
    root.wait_window(about_window)

def quit_app():
    texts = lang_data[selected_lang]
    if messagebox.askokcancel(texts["exit_menu"], texts["exit_menu"]+"?"):
        root.destroy()

async def async_download_media(api_id, api_hash, target_channel, file_type, output_dir, download_limit, start_date_str):
    texts = lang_data[selected_lang]
    if not api_id or not api_hash or not target_channel:
        log_message(texts["missing_settings"])
        return
    try:
        from datetime import datetime
        async with TelegramClient('my_downloader_session', int(api_id), api_hash) as client:
            try:
                entity = await client.get_entity(target_channel)
                progress_label.config(text=texts["waiting_label"])
                root.update()
            except errors.UsernameNotOccupiedError:
                log_message(texts["channel_error"])
                return
            except errors.FloodWaitError as e:
                log_message(texts["flood_error"].format(sec=e.seconds))
                return

            start_date_obj = None
            if start_date_str:
                try:
                    start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
                except ValueError:
                    log_message(texts["no_messages"])
                    return

            all_messages = []
            async for msg in client.iter_messages(entity, limit=download_limit):
                if start_date_obj and msg.date < start_date_obj:
                    continue
                all_messages.append(msg)
            total_messages = len(all_messages)
            if total_messages == 0:
                log_message(texts["no_messages"])
                return
            progress_bar["maximum"] = total_messages

            idx = 0
            for message in all_messages:
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
                                log_message(f"{texts['done_message']}: {file_path}")
                            else:
                                log_message(f"{file_path}... already exists, skipped")
                except Exception as e:
                    log_message(f"Error processing message (ID: {message.id}): {e}")

                idx += 1
                progress_bar["value"] = idx
                percentage = (idx / total_messages) * 100
                progress_percentage.config(text=f"{percentage:.2f}%")
                root.update()

            progress_label.config(text=texts["finished_download"])
            log_message(texts["finished_download"])
            root.update()

    except Exception as e:
        log_message(f"Error connecting to Telegram: {e}")

def start_download():
    texts = lang_data[selected_lang]
    api_id_val = api_id_entry.get().strip()
    api_hash_val = api_hash_entry.get().strip()
    target_channel_val = target_channel_entry.get().strip()
    file_type_val = file_type_var.get()
    output_dir_val = output_dir_entry.get().strip()
    download_limit_val = download_limit_var.get()
    start_date_val = start_date_entry.get().strip()

    if not api_id_val or not api_hash_val or not target_channel_val:
        messagebox.showwarning(texts["settings_tab"], texts["warning_settings"])
        return

    def run_download():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            async_download_media(api_id_val, api_hash_val, target_channel_val, file_type_val, output_dir_val, download_limit_val, start_date_val)
        )

    threading.Thread(target=run_download, daemon=True).start()

menubar = tk.Menu(root, bg='#2C3E50', fg='white', activebackground='#16A085', activeforeground='white')
root.config(menu=menubar)

notebook = ttk.Notebook(root)
notebook.pack(pady=10, padx=10, fill='both', expand=True)

api_id = config.get("api_id")
api_hash = config.get("api_hash")
target_channel = config.get("target_channel")
file_type = config.get("file_type", "pdf")
download_limit = config.get("download_limit", 100)
output_dir = config.get("output_dir", output_dir)

download_frame = ttk.Frame(notebook, style="TFrame")
notebook.add(download_frame, text="Letöltés")

header_frame = ttk.Frame(download_frame, style="TFrame")
header_frame.pack(pady=(40,20), padx=20, fill='x')
title_label = ttk.Label(header_frame, text="Telegram Média Letöltés", font=("Helvetica", 24, 'bold'), background='#34495E', foreground='white')
title_label.pack(pady=(0,5))
subtitle_label = ttk.Label(header_frame, text="Egyszerűen töltsd le a csatornáid médiatartalmait!", font=("Helvetica", 14), background='#34495E', foreground='white')
subtitle_label.pack(pady=(0,10))

log_card = ttk.Frame(download_frame, style="TFrame")
log_card.pack(pady=(10, 20), padx=20, fill='both', expand=True)
card_label = ttk.Label(log_card, text="Napló", font=("Helvetica", 14, 'bold'), foreground='white', background='#34495E')
card_label.pack(pady=(10,5))

progress_text = scrolledtext.ScrolledText(
    log_card,
    width=100,
    height=20,
    wrap=tk.WORD,
    font=("Courier New", 11),
    bg='#34495E',
    fg='white',
    insertbackground='white',
    relief='flat',
    borderwidth=0,
    highlightthickness=0
)
progress_text.pack(pady=10, padx=10, fill='both', expand=True)





progress_area = ttk.Frame(download_frame, style="TFrame")
progress_area.pack(pady=20)
progress_label = ttk.Label(progress_area, text="Várakozás a letöltésre...", font=("Helvetica", 14), foreground='white', background='#34495E')
progress_label.pack(pady=(0,10))
progress_bar = ttk.Progressbar(progress_area, orient="horizontal", length=600, mode="determinate")
progress_bar.pack(pady=(0,5))
progress_percentage = ttk.Label(progress_area, text="0%", font=("Helvetica", 12), foreground='white', background='#34495E')
progress_percentage.pack()

button_frame = ttk.Frame(download_frame, style="TFrame")
button_frame.pack(pady=(20,40))
start_button = ttk.Button(button_frame, text="Indítás", command=start_download)
start_button.pack()

settings_frame = ttk.Frame(notebook, style="TFrame")
notebook.add(settings_frame, text="Beállítások")

general_settings = ttk.Labelframe(settings_frame, text="Általános beállítások", padding=10)
general_settings.pack(pady=10, padx=10, fill='x')

ttk.Label(general_settings, text="API ID:").grid(row=0, column=0, sticky='w', pady=5, padx=10)
api_id_entry = ttk.Entry(general_settings, width=50)
api_id_entry.grid(row=0, column=1, pady=5, padx=10)
api_id_entry.insert(0, api_id)

ttk.Label(general_settings, text="API Hash:").grid(row=1, column=0, sticky='w', pady=5, padx=10)
api_hash_entry = ttk.Entry(general_settings, width=50)
api_hash_entry.grid(row=1, column=1, pady=5, padx=10)
api_hash_entry.insert(0, api_hash)

ttk.Label(general_settings, text="Csatorna neve/linkje:").grid(row=2, column=0, sticky='w', pady=5, padx=10)
target_channel_entry = ttk.Entry(general_settings, width=50)
target_channel_entry.grid(row=2, column=1, pady=5, padx=10)
target_channel_entry.insert(0, target_channel)

file_type_frame = ttk.Labelframe(settings_frame, text="Fájltípus letöltése", padding=10)
file_type_frame.pack(pady=10, padx=10, fill='x')

file_type_var = tk.StringVar(value=file_type)
ttk.Radiobutton(file_type_frame, text="PDF", variable=file_type_var, value="pdf").pack(side='left', padx=5, pady=5)
ttk.Radiobutton(file_type_frame, text="Képek (jpg, png)", variable=file_type_var, value="images").pack(side='left', padx=5, pady=5)
ttk.Radiobutton(file_type_frame, text="Videók (mp4)", variable=file_type_var, value="videos").pack(side='left', padx=5, pady=5)
ttk.Radiobutton(file_type_frame, text="Összes típus", variable=file_type_var, value="all").pack(side='left', padx=5, pady=5)

output_settings = ttk.Labelframe(settings_frame, text="Kimeneti beállítások", padding=10)
output_settings.pack(pady=10, padx=10, fill='x')

ttk.Label(output_settings, text="Mentési könyvtár:").grid(row=0, column=0, sticky='w', pady=5, padx=10)
output_dir_entry = ttk.Entry(output_settings, width=50)
output_dir_entry.grid(row=0, column=1, pady=5, padx=10)
output_dir_entry.insert(0, output_dir)

ttk.Label(output_settings, text="Letöltési limit (üzenetek száma):").grid(row=1, column=0, sticky='w', pady=5, padx=10)
download_limit_var = tk.IntVar(value=download_limit)
download_limit_entry = ttk.Entry(output_settings, textvariable=download_limit_var, width=10)
download_limit_entry.grid(row=1, column=1, pady=5, padx=10, sticky='w')

filter_frame = ttk.Labelframe(settings_frame, text="Haladó szűrés", padding=10)
filter_frame.pack(pady=10, padx=10, fill='x')

ttk.Label(filter_frame, text="Kezdő dátum (ÉÉÉÉ-HH-NN):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
start_date_entry = ttk.Entry(filter_frame, width=20)
start_date_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(filter_frame, text="Min. fájlméret (MB):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
min_size_entry = ttk.Entry(filter_frame, width=10)
min_size_entry.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(filter_frame, text="Max. fájlméret (MB):").grid(row=2, column=0, sticky='w', padx=10, pady=5)
max_size_entry = ttk.Entry(filter_frame, width=10)
max_size_entry.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(filter_frame, text="Fájlnév minta (regex):").grid(row=3, column=0, sticky='w', padx=10, pady=5)
filename_pattern_entry = ttk.Entry(filter_frame, width=30)
filename_pattern_entry.grid(row=3, column=1, padx=10, pady=5)

advanced_settings = ttk.Labelframe(settings_frame, text="Speciális beállítások", padding=10)
advanced_settings.pack(pady=10, padx=10, fill='x')

ttk.Label(advanced_settings, text="Letöltési időkorlát (mp/fájl):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
timeout_entry = ttk.Entry(advanced_settings, width=10)
timeout_entry.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(advanced_settings, text="Proxy (host:port):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
proxy_entry = ttk.Entry(advanced_settings, width=30)
proxy_entry.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(advanced_settings, text="Nyelv:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
lang_var = tk.StringVar(value=selected_lang)
lang_menu_combobox = ttk.Combobox(advanced_settings, textvariable=lang_var, values=["en", "hu", "de"], width=10)
lang_menu_combobox.grid(row=2, column=1, padx=10, pady=5)
lang_var.trace("w", lambda *args: change_language(lang_var.get()))

save_button_frame = ttk.Frame(settings_frame, style="TFrame")
save_button_frame.pack(pady=20)
save_button = ttk.Button(save_button_frame, text="Beállítások mentése", command=save_config)
save_button.pack(pady=10)

status_bar = ttk.Label(root, text="Készen áll", relief=tk.SUNKEN, anchor='w', font=("Helvetica", 10), background='#2C3E50', foreground='white')
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

async def async_download_media(api_id, api_hash, target_channel, file_type, output_dir, download_limit, start_date_str):
    texts = lang_data[selected_lang]
    if not api_id or not api_hash or not target_channel:
        log_message(texts["missing_settings"])
        return
    try:
        from datetime import datetime
        async with TelegramClient('my_downloader_session', int(api_id), api_hash) as client:
            try:
                entity = await client.get_entity(target_channel)
                progress_label.config(text=texts["waiting_label"])
                root.update()
            except errors.UsernameNotOccupiedError:
                log_message(texts["channel_error"])
                return
            except errors.FloodWaitError as e:
                log_message(texts["flood_error"].format(sec=e.seconds))
                return

            start_date_obj = None
            if start_date_str:
                try:
                    start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
                except ValueError:
                    log_message(texts["no_messages"])
                    return

            all_messages = []
            async for msg in client.iter_messages(entity, limit=download_limit):
                if start_date_obj and msg.date < start_date_obj:
                    continue
                all_messages.append(msg)
            total_messages = len(all_messages)
            if total_messages == 0:
                log_message(texts["no_messages"])
                return
            progress_bar["maximum"] = total_messages

            idx = 0
            for message in all_messages:
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
                                log_message(f"{texts['done_message']}: {file_path}")
                            else:
                                log_message(f"{file_path}... already exists, skipped")
                except Exception as e:
                    log_message(f"Error processing message (ID: {message.id}): {e}")

                idx += 1
                progress_bar["value"] = idx
                percentage = (idx / total_messages) * 100
                progress_percentage.config(text=f"{percentage:.2f}%")
                root.update()

            progress_label.config(text=texts["finished_download"])
            log_message(texts["finished_download"])
            root.update()

    except Exception as e:
        log_message(f"Error connecting to Telegram: {e}")

def start_download():
    texts = lang_data[selected_lang]
    api_id_val = api_id_entry.get().strip()
    api_hash_val = api_hash_entry.get().strip()
    target_channel_val = target_channel_entry.get().strip()
    file_type_val = file_type_var.get()
    output_dir_val = output_dir_entry.get().strip()
    download_limit_val = download_limit_var.get()
    start_date_val = start_date_entry.get().strip()

    if not api_id_val or not api_hash_val or not target_channel_val:
        messagebox.showwarning(texts["settings_tab"], texts["warning_settings"])
        return

    def run_download():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            async_download_media(api_id_val, api_hash_val, target_channel_val, file_type_val, output_dir_val, download_limit_val, start_date_val)
        )

    threading.Thread(target=run_download, daemon=True).start()

menubar = tk.Menu(root, bg='#2C3E50', fg='white', activebackground='#16A085', activeforeground='white')
root.config(menu=menubar)

rebuild_menus()
update_ui_texts()

root.mainloop()
