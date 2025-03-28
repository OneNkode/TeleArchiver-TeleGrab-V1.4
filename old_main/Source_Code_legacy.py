from telethon import TelegramClient
import os
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext, simpledialog
import threading
import asyncio

# Létrehozunk egy mappát a letöltött PDF-ek számára
output_dir = 'pdf_letoltes'
os.makedirs(output_dir, exist_ok=True)

# GUI létrehozása
root = tk.Tk()
root.title("Telegram PDF Letöltő")
root.geometry("800x600")
root.configure(bg='#2e3b4e')

# Stílusok beállítása
style = ttk.Style()
style.theme_use('clam')
style.configure("TLabel", font=("Helvetica", 12), background='#2e3b4e', foreground='#ffffff')
style.configure("TButton", font=("Helvetica", 10), background='#4e5d6c', foreground='#ffffff', padding=6)
style.configure("TProgressbar", thickness=20, troughcolor='#4e5d6c', background='#61afef')

# Címke a csatlakozási státuszhoz
progress_label = ttk.Label(root, text="Csatlakozás a Telegramhoz...", style="TLabel")
progress_label.pack(pady=15)

# Szövegmező a letöltési folyamat naplózásához
progress_frame = ttk.Frame(root)
progress_frame.pack(pady=10, padx=15, fill='both', expand=True)
progress_text = scrolledtext.ScrolledText(progress_frame, width=80, height=15, wrap=tk.WORD, font=("Courier", 10), bg='#1c252e', fg='#dcdcdc', insertbackground='white')
progress_text.pack(fill='both', expand=True)

# Haladási sáv
progress_bar = ttk.Progressbar(root, orient="horizontal", length=700, mode="determinate", style="TProgressbar")
progress_bar.pack(pady=10)

# Százalékos előrehaladás
progress_percentage = ttk.Label(root, text="0%", style="TLabel")
progress_percentage.pack(pady=5)

root.update()

# Csatorna kiválasztása és API adatok
api_id = simpledialog.askstring("API ID", "Add meg a Telegram API ID-t:")
api_hash = simpledialog.askstring("API Hash", "Add meg a Telegram API Hash-t:")
target_channel = simpledialog.askstring("Csatorna kiválasztása", "Add meg a csatorna nevét vagy linkjét:")

if not api_id or not api_hash or not target_channel:
    progress_text.insert(tk.END, "Nem adott meg minden szükséges adatot, a letöltés megszakad.\n")
    root.update()
else:
    # Letöltési folyamat végrehajtása külön szálon
    def download_pdfs():
        asyncio.run(async_download_pdfs())

    async def async_download_pdfs():
        try:
            async with TelegramClient('my_downloader_session', api_id, api_hash) as client:
                # Csatlakozás a megadott csatornához
                entity = await client.get_entity(target_channel)
                progress_label.config(text=f"Csatorna feldolgozása: {target_channel}")
                root.update()

                # Az összes üzenet bejárása a csatornán
                total_messages = 0
                async for _ in client.iter_messages(entity):
                    total_messages += 1
                progress_bar["maximum"] = total_messages

                idx = 0
                async for message in client.iter_messages(entity):
                    try:
                        # Ha az üzenet fájl mellékletet tartalmaz, és az PDF
                        if message.document and message.document.mime_type == 'application/pdf':
                            # Letöltés az adott könyvtárba
                            file_name = message.document.attributes[0].file_name or f"document_{message.id}.pdf"
                            file_path = os.path.join(output_dir, file_name)
                            if not os.path.exists(file_path):
                                await client.download_media(message, file=file_path)
                                progress_text.insert(tk.END, f"Letöltve: {file_path}\n")
                            else:
                                progress_text.insert(tk.END, f"Már létező fájl, kihagyva: {file_path}\n")
                        progress_text.see(tk.END)
                    except Exception as e:
                        progress_text.insert(tk.END, f"Hiba történt az üzenet feldolgozása során (ID: {message.id}): {e}\n")
                        progress_text.see(tk.END)
                    
                    # Frissítés a GUI-ban
                    idx += 1
                    progress_bar["value"] = idx
                    progress_percentage.config(text=f"{(idx / total_messages) * 100:.2f}%")
                    root.update()

                progress_label.config(text="PDF-ek letöltése befejeződött.")
                root.update()
        except Exception as e:
            progress_text.insert(tk.END, f"Hiba a Telegramhoz való csatlakozás során: {e}\n")
            progress_text.see(tk.END)

    # Letöltési folyamat indítása külön szálon
    threading.Thread(target=download_pdfs, daemon=True).start()

# GUI futtatása
if __name__ == "__main__":
    root.mainloop()
