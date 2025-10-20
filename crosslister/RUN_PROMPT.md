# Running the crosslister from Windows PowerShell

1. Open **PowerShell**.
2. Change to the project directory (adjust only if you unpacked somewhere else):
   ```powershell
   Set-Location "C:\Users\aschi\OneDrive\Documenten\AYCD NSB\Crosslist\crosslist\crosslister"
   ```
3. Launch the poster with a human-like pause between platforms (12–18 seconds):
   ```powershell
   python -m crosslister.main data\listings.csv \
       --images-dir data\images \
       --credentials config\credentials.json \
       --cookies-dir .cookies \
       --delay 12 18
   ```
   > Tip: add `--platforms marktplaats facebook` (for example) if you temporarily want to post to fewer sites, or append `--headless` to hide the browser window.

This command reads the CSV, loads images, signs in with the credentials file, keeps session cookies in the `.cookies` folder, and waits a random 12–18 seconds between platform submissions so the automation behaves more like a person.
