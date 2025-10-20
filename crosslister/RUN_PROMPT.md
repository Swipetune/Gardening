# macOS one-click launcher

1. **Verwijder eventueel het Gatekeeper-slot:** download je dit project als ZIP, dan markeert macOS het bestand soms met *"mac_launcher.command kan niet worden geopend omdat Apple niet kan controleren of het schadelijke software is"*. Open Terminal in deze map en voer uit:
   ```bash
   xattr -d com.apple.quarantine mac_launcher.command
   ```
   > Alternatief: klik met **Ctrl+klik** (of rechtsklik) op `mac_launcher.command`, kies **Open** en bevestig nogmaals **Open** om het bestand toe te staan.
2. **Maak het script uitvoerbaar (eenmalig):**
   ```bash
   chmod +x mac_launcher.command
   ```
3. **Dubbelklik op `mac_launcher.command`:** er verschijnt nu een kleurrijke wizard met duidelijke nummeropties. Per stap kies je:
   - **1 of 2** om het standaardpad te gebruiken of zelf een bestand/map te kiezen (CSV, afbeeldingen, credentials, cookies, categorieën);
   - het vertragingstempo: standaard 12–18 s, extra voorzichtig 18–25 s of een eigen bereik;
   - hoeveel browsers tegelijk mogen draaien (1, 2 of een vrij getal);
   - of headless-modus aan/uit moet staan;
   - welke platforms actief zijn via nummers of namen (Enter = allemaal).
   Tijdens elke stap zie je in kleur welke keuze actief is en kun je Enter indrukken voor de veilige standaard.
4. Na de samenvatting bevestig je met Enter. De launcher draait automatisch `python3 -m crosslister.main` met alle gekozen waarden. Laat het venster open voor statusmeldingen en de verwijzing naar `crosslister_output.json`.

> Tip: zet eventueel `PYTHON_BIN=/pad/naar/python3` voor het dubbelklikken als je een specifieke Python-versie wilt forceren.

## macOS handmatig via Terminal

```bash
python3 -m crosslister.main data/listings.csv \
    --images-dir data/images \
    --credentials config/credentials.json \
    --cookies-dir "$HOME/Library/Application Support/Crosslister/cookies" \
    --category-map data/category_map.json \
    --delay 12 18 \
    --max-parallel 1
```

Voeg naar wens `--platforms marktplaats facebook vinted` of `--headless` toe.

# Windows PowerShell runbook

1. Open **PowerShell**.
2. Ga naar de projectmap:
   ```powershell
   Set-Location "C:\Users\aschi\OneDrive\Documenten\AYCD NSB\Crosslist\crosslist\crosslister"
   ```
3. Start met een pauze van 12–18 seconden:
   ```powershell
   python -m crosslister.main data\listings.csv \
       --images-dir data\images \
       --credentials config\credentials.json \
       --cookies-dir .cookies \
       --category-map data\category_map.json \
       --delay 12 18
   ```
   > Optioneel: voeg `--platforms marktplaats facebook` toe of `--headless` om de browser te verbergen.

De resultaten verschijnen in de console en worden ook opgeslagen in `crosslister_output.json`.
