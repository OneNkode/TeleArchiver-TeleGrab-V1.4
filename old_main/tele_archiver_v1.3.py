from telethon import TelegramClient, errors
import os
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext, simpledialog, messagebox
import threading
import asyncio
import json
import zipfile
from datetime import datetime
import sys
import time
import platform
import ctypes
from PIL import Image, ImageTk


# Létrehozunk egy mappát a letöltött fájlok számára
output_dir = 'media_letoltes'
os.makedirs(output_dir, exist_ok=True)

# Naplózás fájl mentése
log_file = "download_log.txt"

# GUI létrehozása
root = tk.Tk()
root.title("Telegram Media Letöltő")
root.geometry("1200x800")
root.configure(bg='#1e272e')
icon_path = "kep.ico"  # A fájlnevet és a kiterjesztést is megváltoztatjuk, hogy az megfeleljen a valós fájlnak
if os.path.exists(icon_path):
    try:
        icon_img = Image.open(icon_path)
        icon_photo = ImageTk.PhotoImage(icon_img)
        root.tk.call('wm', 'iconphoto', root._w, icon_photo)
    except Exception as e:
        print(f"Hiba az ikon beállítása során: {e}")
else:
    print(f"Hiba: az ikonfájl nem található: {icon_path}")


# Stílusok beállítása
style = ttk.Style()
style.theme_use('clam')
style.configure("TLabel", font=("Helvetica", 14), background='#1e272e', foreground='#ffffff')
style.configure("TButton", font=("Helvetica", 12), background='#00a8ff', foreground='#ffffff', padding=10)
style.configure("TProgressbar", thickness=25, troughcolor='#2f3640', background='#00cec9')
style.configure("TFrame", background='#1e272e')
style.configure("TNotebook", background='#2f3640', foreground='#ffffff')
style.configure("TNotebook.Tab", font=("Helvetica", 12), padding=[10, 5])
style.configure("TRadiobutton", background='#1e272e', foreground='#ffffff', font=("Helvetica", 12))
style.configure("TEntry", fieldbackground='#2f3640', foreground='#ffffff')

# Notebook főmenü
notebook = ttk.Notebook(root)
notebook.pack(pady=10, padx=10, fill='both', expand=True)

# Letöltés főoldal
download_frame = ttk.Frame(notebook, style="TFrame")
notebook.add(download_frame, text="Letöltés")

# Címke a csatlakozási státuszhoz
progress_label = ttk.Label(download_frame, text="Csatlakozás a Telegramhoz...", style="TLabel")
progress_label.pack(pady=15)

# Szövegmező a letöltési folyamat naplózásához
progress_frame = ttk.Frame(download_frame, style="TFrame")
progress_frame.pack(pady=10, padx=15, fill='both', expand=True)
progress_text = scrolledtext.ScrolledText(progress_frame, width=100, height=20, wrap=tk.WORD, font=("Courier New", 11), bg='#2f3640', fg='#ffffff', insertbackground='white', borderwidth=2, relief='sunken')
progress_text.pack(fill='both', expand=True)

# Haladási sáv
progress_bar = ttk.Progressbar(download_frame, orient="horizontal", length=800, mode="determinate", style="TProgressbar")
progress_bar.pack(pady=10)

# Százalékos előrehaladás
progress_percentage = ttk.Label(download_frame, text="0%", style="TLabel")
progress_percentage.pack(pady=5)

# Haladó szűrés: dátum kiválasztása
filter_frame = ttk.Frame(download_frame, style="TFrame")
filter_frame.pack(pady=15)
ttk.Label(filter_frame, text="Letöltés kezdő dátuma (ÉÉÉÉ-HH-NN):", style="TLabel").grid(row=0, column=0, sticky='w', padx=10)
start_date_entry = ttk.Entry(filter_frame, width=20, font=("Helvetica", 12))
start_date_entry.grid(row=0, column=1, padx=10)

# Beállítások lap hozzáadása
settings_frame = ttk.Frame(notebook, style="TFrame")
notebook.add(settings_frame, text="Beállítások")

# Beállítások tartalom
ttk.Label(settings_frame, text="API ID:", style="TLabel").grid(row=0, column=0, sticky='w', pady=10, padx=10)
api_id_entry = ttk.Entry(settings_frame, width=50, font=("Helvetica", 12))
api_id_entry.grid(row=0, column=1, pady=10, padx=10)
api_id_entry.insert(0, '')

ttk.Label(settings_frame, text="API Hash:", style="TLabel").grid(row=1, column=0, sticky='w', pady=10, padx=10)
api_hash_entry = ttk.Entry(settings_frame, width=50, font=("Helvetica", 12))
api_hash_entry.grid(row=1, column=1, pady=10, padx=10)
api_hash_entry.insert(0, '')

ttk.Label(settings_frame, text="Csatorna neve/linkje:", style="TLabel").grid(row=2, column=0, sticky='w', pady=10, padx=10)
target_channel_entry = ttk.Entry(settings_frame, width=50, font=("Helvetica", 12))
target_channel_entry.grid(row=2, column=1, pady=10, padx=10)
target_channel_entry.insert(0, '')

# Fájl típus kiválasztása
ttk.Label(settings_frame, text="Fájl típusok letöltése:", style="TLabel").grid(row=3, column=0, sticky='w', pady=10, padx=10)
file_type_var = tk.StringVar(value='pdf')
file_type_frame = ttk.Frame(settings_frame, style="TFrame")
file_type_frame.grid(row=3, column=1, pady=10, padx=10, sticky='w')
ttk.Radiobutton(file_type_frame, text="PDF", variable=file_type_var, value="pdf", style="TRadiobutton").pack(side='left', padx=5)
ttk.Radiobutton(file_type_frame, text="Képek (jpg, png)", variable=file_type_var, value="images", style="TRadiobutton").pack(side='left', padx=5)
ttk.Radiobutton(file_type_frame, text="Videók (mp4)", variable=file_type_var, value="videos", style="TRadiobutton").pack(side='left', padx=5)
ttk.Radiobutton(file_type_frame, text="Összes típus", variable=file_type_var, value="all", style="TRadiobutton").pack(side='left', padx=5)

# Extra beállítások hozzáadása
# Mentési hely kiválasztása
ttk.Label(settings_frame, text="Mentési könyvtár:", style="TLabel").grid(row=4, column=0, sticky='w', pady=10, padx=10)
output_dir_entry = ttk.Entry(settings_frame, width=50, font=("Helvetica", 12))
output_dir_entry.grid(row=4, column=1, pady=10, padx=10)
output_dir_entry.insert(0, output_dir)

# Letöltési határérték beállítása
ttk.Label(settings_frame, text="Letöltési limit (üzenetek száma):", style="TLabel").grid(row=5, column=0, sticky='w', pady=10, padx=10)
download_limit_var = tk.IntVar(value=100)
download_limit_entry = ttk.Entry(settings_frame, textvariable=download_limit_var, width=10, font=("Helvetica", 12))
download_limit_entry.grid(row=5, column=1, pady=10, padx=10, sticky='w')

# Mentés gomb
save_button_frame = ttk.Frame(settings_frame, style="TFrame")
save_button_frame.grid(row=6, columnspan=2, pady=20)

def save_settings(api_id_entry, api_hash_entry, target_channel_entry, file_type_var, output_dir_entry, download_limit_var):
    new_config = {
        "api_id": api_id_entry.get(),
        "api_hash": api_hash_entry.get(),
        "target_channel": target_channel_entry.get(),
        "file_type": file_type_var.get(),
        "output_dir": output_dir_entry.get(),
        "download_limit": download_limit_var.get()
    }
    with open('config.json', 'w') as config_file:
        json.dump(new_config, config_file)
    progress_text.insert(tk.END, "Beállítások elmentve. Az alkalmazás újraindul a változtatások érvényesítéséhez.\n")
    progress_text.see(tk.END)
    restart_program()

def restart_program():
    root.destroy()
    os.execl(sys.executable, sys.executable, *sys.argv)

ttk.Button(save_button_frame, text="Mentés és Újraindítás", command=lambda: save_settings(api_id_entry, api_hash_entry, target_channel_entry, file_type_var, output_dir_entry, download_limit_var), style="TButton").pack()

root.update()

# API adatok betöltése konfigurációs fájlból
config = {}
if not os.path.exists('config.json'):
    default_config = {
        "api_id": "",
        "api_hash": "",
        "target_channel": "",
        "file_type": "pdf",
        "output_dir": output_dir,
        "download_limit": 100
    }
    with open('config.json', 'w') as config_file:
        json.dump(default_config, config_file)

try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    progress_text.insert(tk.END, "Hiba: A konfigurációs fájl (config.json) nem található.\n")
    root.update()

api_id = config.get("api_id")
api_hash = config.get("api_hash")
target_channel = config.get("target_channel")
file_type = config.get("file_type", "pdf")
output_dir = config.get("output_dir", output_dir)
download_limit = config.get("download_limit", 100)

# Előzetesen beállítjuk a beviteli mezők értékeit
api_id_entry.delete(0, tk.END)
api_id_entry.insert(0, api_id)
api_hash_entry.delete(0, tk.END)
api_hash_entry.insert(0, api_hash)
target_channel_entry.delete(0, tk.END)
target_channel_entry.insert(0, target_channel)
file_type_var.set(file_type)
output_dir_entry.delete(0, tk.END)
output_dir_entry.insert(0, output_dir)
download_limit_var.set(download_limit)

# Naplózási funkció
def log_message(message):
    with open(log_file, "a") as log:
        log.write(f"{datetime.now()}: {message}\n")
    progress_text.insert(tk.END, message + "\n")
    progress_text.see(tk.END)
    # Értesítés, ha a letöltés befejeződött
    if 'letöltése befejeződött' in message:
        if platform.system() == "Windows":
            ctypes.windll.user32.MessageBoxW(0, "A letöltés befejeződött!", "Értesítés", 1)
        else:
            messagebox.showinfo("Értesítés", "A letöltés befejeződött!")

if not api_id or not api_hash or not target_channel:
    log_message("Nem adott meg minden szükséges adatot, a letöltés megszakad.")
    root.update()
else:
    # Letöltési folyamat végrehajtása külön szálon
    def download_media():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_download_media())

    async def async_download_media():
        try:
            async with TelegramClient('my_downloader_session', api_id, api_hash) as client:
                # Csatlakozás a megadott csatornához
                try:
                    entity = await client.get_entity(target_channel)
                    progress_label.config(text=f"Csatorna feldolgozása: {target_channel}")
                    root.update()
                except errors.UsernameNotOccupiedError:
                    log_message("Hiba: A megadott csatorna nem található.")
                    return
                except errors.FloodWaitError as e:
                    log_message(f"Túl sok kérés. Várjon {e.seconds} másodpercet, és próbálja újra.")
                    return

                # Az összes üzenet bejárása a csatornán, letöltési limit alkalmazásával
                total_messages = 0
                start_date = start_date_entry.get()
                try:
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
                except ValueError:
                    log_message("Hiba: Érvénytelen dátumformátum. Használja az ÉÉÉÉ-HH-NN formátumot.")
                    return

                async for message in client.iter_messages(entity, limit=download_limit):
                    if start_date_obj and message.date < start_date_obj:
                        continue
                    total_messages += 1
                progress_bar["maximum"] = total_messages

                idx = 0
                async for message in client.iter_messages(entity, limit=download_limit):
                    if start_date_obj and message.date < start_date_obj:
                        continue
                    try:
                        # Ha az üzenet fájl mellékletet tartalmaz
                        if message.document:
                            mime_type = message.document.mime_type
                            if (
                                (file_type == "pdf" and mime_type == 'application/pdf') or
                                (file_type == "images" and mime_type in ['image/jpeg', 'image/png']) or
                                (file_type == "videos" and mime_type == 'video/mp4') or
                                (file_type == "all")
                            ):
                                # Letöltés az adott könyvtárba
                                file_name = message.document.attributes[0].file_name or f"document_{message.id}"
                                file_path = os.path.join(output_dir, file_name)
                                if not os.path.exists(file_path):
                                    await client.download_media(message, file=file_path)
                                    log_message(f"Letöltve: {file_path}")
                                else:
                                    log_message(f"Már létező fájl, kihagyva: {file_path}")
                        progress_text.see(tk.END)
                    except Exception as e:
                        log_message(f"Hiba történt az üzenet feldolgozása során (ID: {message.id}): {e}")
                        progress_text.see(tk.END)
                    
                    # Frissítés a GUI-ban
                    idx += 1
                    progress_bar["value"] = idx
                    progress_percentage.config(text=f"{(idx / total_messages) * 100:.2f}%")
                    root.update()

                progress_label.config(text="Media letöltése befejeződött.")
                log_message("Media letöltése befejeződött.")
                root.update()
        except Exception as e:
            log_message(f"Hiba a Telegramhoz való csatlakozás során: {e}")
            progress_text.see(tk.END)

    # Letöltési folyamat indítása külön szálon
    threading.Thread(target=download_media, daemon=True).start()

# GUI futtatása
if __name__ == "__main__":
    root.mainloop()
