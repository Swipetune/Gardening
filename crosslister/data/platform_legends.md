# Crosslister CSV-legende (BE/NL)

Dit document beschrijft alle kolommen in `listings.csv`. Vul de algemene kolommen in en gebruik optionele overrides per platform waar nodig. De crosslister zorgt er vervolgens voor dat elke advertentie valide is voor Marktplaats, 2dehands, Facebook Marketplace en Vinted.

## Algemene gegevens (zonder prefix)
| Kolom | Beschrijving | Verwachte waarden |
| --- | --- | --- |
| `id` | Interne naam van de advertentie (verschijnt in logs). | Unieke string, geen spaties verplicht. |
| `title` | Titel voor alle platformen. | Maximaal ±120 tekens; de tool knipt automatisch af op 80-100. |
| `description` | Volledige beschrijving. | Minimaal 10 tekens, mag nieuwe regels bevatten via `\n`. |
| `price` | Vraagprijs. | Decimaal getal, punt of komma toegestaan. |
| `currency` | Valuta. | Alleen `EUR` wordt ondersteund. |
| `condition` | Generieke conditie. | Gebruik een sleutel uit de tabel [Conditiemapping](#conditiemapping). |
| `category_hint` | Logische productgroep. | Sleutel die voorkomt in `data/category_map.json` (bv. `audio_accessoires`, `barkrukken`). |
| `brand` | Merknaam. | Vrije tekst; verplicht voor Vinted. |
| `size` | Maat / formaat. | Vrije tekst; verplicht voor Vinted (bv. `One size`, `EU 42`). |
| `color` | Kleurenlijst. | Max. drie waarden gescheiden door `|` (bv. `zwart|grijs`). |
| `gender` | Doelgroep indien relevant. | `heren`, `dames`, `unisex`, `kids`, … |
| `material` | Belangrijk materiaal. | Vrije tekst, meerdere materialen scheiden met `|`. |
| `sku` | Eigen productcode. | Vrije tekst. |
| `quantity` | Aantal stuks in de aanbieding. | Geheel getal ≥ 1. |
| `images` | Paden naar afbeeldingen. | Scheid met `|`; paden zijn relatief aan `data/images/`. |

### Locatievelden
| Kolom | Beschrijving | Opmerking |
| --- | --- | --- |
| `location_country` | ISO-landcode. | `NL` of `BE`. |
| `location_postcode` | Postcode. | NL-formaat `1234AB` of BE-formaat `1000`. |
| `location_city` | Plaatsnaam. | Vereist voor alle platformen. |
| `location_region` | Provincie/regio of extra context. | Optioneel; gebruikt voor Facebook-weergave. |

### Verzendgegevens
| Kolom | Beschrijving | Waarden |
| --- | --- | --- |
| `shipping_pickup` | Afhalen toegestaan? | `TRUE` of `FALSE`. |
| `shipping_carriers` | Verzenddiensten. | Lijst gescheiden met `|` (bv. `PostNL|DPD|bpost`). |
| `shipping_buyer_pays_shipping` | Betaalt koper de verzendkosten? | `TRUE` of `FALSE`. |

## Platformspecifieke overrides
Alle kolomnamen met een prefix overschrijven uitsluitend de gekoppelde waarde voor dat platform. Laat ze leeg als de algemene kolom volstaat.

### 2dehands (`tweedehands_`)
| Kolom | Gebruik |
| --- | --- |
| `tweedehands_location_country` | Overschrijft het land (typisch `BE`). |
| `tweedehands_location_postcode` | Belgische postcode voor het zoekertje. |
| `tweedehands_location_city` | Plaatsnaam voor het zoekertje. |
| `tweedehands_category` (optioneel) | Override voor de rubriekzoekterm. |
| `tweedehands_condition` (optioneel) | Override voor de conditielabels. |

### Marktplaats (`marktplaats_`)
| Kolom | Gebruik |
| --- | --- |
| `marktplaats_postal_code` | Alleen nodig als de NL-postcode afwijkt van `location_postcode`. |
| `marktplaats_category` (optioneel) | Eigen categoriezoekterm. |
| `marktplaats_condition` (optioneel) | Specifieke conditiewaarde voor Marktplaats. |

### Facebook Marketplace (`facebook_`)
| Kolom | Gebruik |
| --- | --- |
| `facebook_category` | Engelse zoekterm voor de categorie. |
| `facebook_condition` | Eén van `New`, `Used - Like New`, `Used - Good`, `Used - Fair`. |
| `facebook_location` | Override voor het locatiezoekveld (bv. `Amsterdam, North Holland`). |

### Vinted (`vinted_`)
| Kolom | Gebruik |
| --- | --- |
| `vinted_category` | Zoekterm voor de Vinted-categorie. |
| `vinted_condition` | Indien anders dan de generieke conditie (volledige NL-benaming). |
| `vinted_brand` | Specifieke merkoverride. |
| `vinted_size` | Specifieke maatoverride (bv. `One size`, `EU 42`). |

## Conditiemapping
Gebruik onderstaande sleutels in de kolom `condition`. De tool vertaalt deze automatisch naar de juiste waarde per platform.

| Sleutel | Betekenis | Marktplaats & 2dehands | Facebook | Vinted |
| --- | --- | --- | --- | --- |
| `nieuw_met_kaartje` | Nieuw, met labels/folies. | Nieuw | New | Nieuw met kaartje |
| `nieuw_zonder_kaartje` | Nieuw, geen labels. | Nieuw | New | Nieuw zonder kaartje |
| `zeer_goed` | Zo goed als nieuw. | Zo goed als nieuw | Used – Like New | Zeer goed |
| `goed` | Licht gebruikt. | Gebruikt | Used – Good | Goed |
| `redelijk` | Zichtbare slijtage. | Gebruikt/Redelijk | Used – Fair | Redelijk |

## Automatische controles
* De tool trimt automatisch het aantal foto's: max. 10 (Facebook), 20 (Vinted) en 24 (Marktplaats/2dehands).
* Postcodes worden gevalideerd op NL- (`1234AB`) en BE-formaat (`1000`).
* Beschrijvingen korter dan 10 tekens en prijzen ≤ 0 worden geweigerd.
* Voor Vinted zijn `brand` en `size` verplicht; bij ontbrekende waarden stopt het script met een duidelijke foutmelding.

Met deze richtlijnen kun je de CSV volledig voorbereiden zonder de Python-code te wijzigen. Voeg nieuwe categorieën toe in `data/category_map.json` en verwijs ernaar via `category_hint` om nieuwe producttypes te ondersteunen.
