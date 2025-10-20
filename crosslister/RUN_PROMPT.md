# macOS one-click launcher

1. **Maak het script uitvoerbaar (eenmalig):**
   ```bash
   chmod +x mac_launcher.command
   ```
2. **Dubbelklik op `mac_launcher.command`:** het venster vraagt naar:
   - het CSV-bestand;
   - de map met afbeeldingen, credentials en cookies;
   - het JSON-bestand met categoriekoppelingen (`data/category_map.json`);
   - de gewenste platforms (standaard alle vier);
   - de minimale en maximale vertraging per platformactie;
   - het maximum aantal gelijktijdige browsertabs (`--max-parallel`);
   - al dan niet headless draaien.
3. Na het bevestigen start automatisch `python3 -m crosslister.main` met jouw keuzes. Laat het venster open voor statusmeldingen en de verwijzing naar `crosslister_output.json`.

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
