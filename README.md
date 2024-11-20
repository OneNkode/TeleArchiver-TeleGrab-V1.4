# Telegram Media Downloader

## Leírás
A **Telegram Media Downloader** egy egyszerű alkalmazás, amely lehetővé teszi a különböző típusú médiafájlok letöltését a Telegram csatornákról. Az alkalmazás támogatja a PDF-eket, képeket (JPEG, PNG), videókat (MP4), valamint az összes típusú fájl letöltését is.

Ez a projekt tartalmaz egy EXE verziót is, amely lehetővé teszi a program futtatását Python telepítése nélkül.

## Jellemzők
- Egyszerű grafikus felhasználói felület (GUI) a Telegram média letöltéséhez.
- Konfigurációs beállítások mentése, ahol megadható az API ID, API Hash és a cél csatorna.
- Támogatott fájltípusok: PDF, képek, videók és összes fájl típus.
- Naplózás a letöltési folyamat részleteiről.


3. A kész EXE fájl a `dist` mappában lesz megtalálható.

### Hogyan Futtasd Az EXE Fájlt
1. Nyisd meg a `dist` mappát, ahol a létrehozott `.exe` fájl található.
2. Dupla kattintással indítsd el az alkalmazást.

## Használati Útmutató
1. Indítsd el az alkalmazást.
2. Menj a **Beállítások** menübe, és add meg a szükséges API ID-t, API Hash-t, valamint a letölteni kívánt Telegram csatorna nevét vagy linkjét.
3. Válaszd ki a kívánt fájl típust (PDF, képek, videók, összes fájl).
4. Kattints a **Mentés** gombra a beállítások rögzítéséhez.
5. Menj vissza a **Letöltés** fülre, majd várd meg, míg a program csatlakozik a Telegram csatornához és letölti a kiválasztott fájlokat.

## Fontos Megjegyzések
- Az alkalmazás futtatásához meg kell adnod egy Telegram API ID-t és API Hash-t, amelyet a [Telegram Developer Portal](https://my.telegram.org/auth) oldalon szerezhetsz be.
- Ha a letöltési folyamat során hiba lép fel, ellenőrizd a csatorna nevét/linkjét, valamint az API adatokat.

## Fejlesztőknek
Ha szeretnéd módosítani a forráskódot, akkor klónozd a projektet a GitHub-ról, és győződj meg róla, hogy minden szükséges Python csomag telepítve van.

## Hozzájárulás
Ha szeretnél hozzájárulni a projekthez, kérjük, nyiss egy pull requestet, vagy jelezd az ötleteidet az **Issues** részlegben.

## Licenc
Ez a projekt MIT Licenc alatt érhető el.

