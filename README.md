# Telegram Média Letöltő

Egy modern és felhasználóbarát alkalmazás Telegram csatornákról való médiafájlok letöltéséhez.

## Funkciók

- 🖼️ Több fájltípus támogatása (fényképek, videók, dokumentumok, hangfájlok, szövegfájlok)
- 🔍 Részletes szűrési lehetőségek:
  - Fájltípus szerint
  - Méret szerint
  - Dátum szerint
- 📊 Statisztikák követése:
  - Összes letöltés száma
  - Összes letöltött méret
  - Utolsó letöltés időpontja
  - Kedvenc csatornák
- 👁️ Fájl előnézet
- 📥 Letöltési előnézet
- ⚡ Párhuzamos letöltések
- 🔄 Automatikus újrapróbálkozás
- ⏸️ Letöltés szüneteltetése/folytatása
- 🌍 Többnyelvű felület (magyar, angol, német)
- 🔒 Proxy támogatás
- 💾 Automatikus mentés
- 🔄 Automatikus frissítések

## Telepítés

1. Klónozza le a repository-t:

```bash
git clone https://github.com/yourusername/telegram-media-downloader.git
cd telegram-media-downloader
```

2. Telepítse a függőségeket:

```bash
pip install -r requirements.txt
```

3. Konfigurálja az alkalmazást:

   - Nyissa meg a `config.json` fájlt
   - Adja meg a Telegram API ID-t és API Hash-t
   - Állítsa be a célcsatornát
   - Válassza ki a nyelvet
   - Állítsa be a többi beállítást igény szerint

4. Indítsa el az alkalmazást:

```bash
python tele_archiver.py
```

## Használat

1. Adja meg a Telegram API ID-t és API Hash-t
2. Írja be a célcsatorna nevét vagy linkjét
3. Állítsa be a szűrési feltételeket (opcionális)
4. Kattintson az "Előnézet" gombra a letölthető fájlok megtekintéséhez
5. Válassza ki a letölteni kívánt fájlokat vagy kattintson az "Összes letöltése" gombra
6. Kövesse a letöltési folyamatot a folyamatjelzőn

## Fejlesztői információk

### Függőségek

- telethon==1.32.1
- requests==2.31.0
- python-dateutil==2.8.2
- Pillow==10.2.0
- python-socks==2.4.4
- aiohttp==3.9.3
- cryptography==42.0.2
- pytz==2024.1

### Projekt struktúra

```
telegram-media-downloader/
├── tele_archiver.py      # Fő alkalmazás
├── config.json          # Konfigurációs fájl
├── lang.json           # Nyelvi fájlok
├── requirements.txt    # Függőségek
└── README.md          # Dokumentáció
```

### Fordítás

1. Nyissa meg a `lang.json` fájlt
2. Adja hozzá az új fordításokat a megfelelő nyelvi szekcióhoz
3. Mentse el a fájlt

### Fejlesztés

1. Forkolja a repository-t
2. Hozzon létre egy új branch-et (`git checkout -b feature/amazing-feature`)
3. Commitolja a változtatásokat (`git commit -m 'Add some amazing feature'`)
4. Pusholja a branch-et (`git push origin feature/amazing-feature`)
5. Nyisson egy Pull Request-et

## Licenc

Ez a projekt MIT licenc alatt van kiadva. Lásd a [LICENSE](LICENSE) fájlt a részletekért.

## Kapcsolat

- GitHub: [OneNKode](https://github.com/OneNKode)
- Email: your.email@example.com
- Telegram: [@Leventegt](https://t.me/+g-EKpEjQLRRmMzU0)
