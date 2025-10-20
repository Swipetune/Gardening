# Platformlegende voor `listings.csv`

Dit bestand beschrijft alle kolommen in `listings.csv` en welke waarden je kunt invullen per platform. Elke advertentie wordt automatisch naar **Marktplaats**, **2dehands**, **Facebook Marketplace** en **Vinted** gestuurd, dus de CSV bevat velden voor elk platform.

## Algemene kolommen (zonder prefix)
| Kolom | Beschrijving | Ondersteunde waarden |
| --- | --- | --- |
| `id` | Unieke naam voor de advertentie. Verschijnt in de logbestanden. | Vrije tekst, geen komma's. |
| `title` | Titel die standaard naar alle platformen gaat (kan per platform overschreven worden). | Vrije tekst. |
| `description` | Volledige beschrijving van de advertentie. | Vrije tekst, nieuwe regels mogen via `\n`. |
| `price` | Vraagprijs in euro. | Getal met punt of komma (bijv. `75` of `75,00`). |
| `images` | Afbeeldingsbestanden, gescheiden door `|`. Paden worden relatief aan de map `data/images/`. | Bestandsnamen of submappen, bv. `nike_air_max/foto1.jpg|nike_air_max/foto2.jpg`. |
| `shipping` | Schakelt verzendopties in waar beschikbaar. | `TRUE` (verzenden + afhalen) of `FALSE` (alleen afhalen). |
| `category` | Standaard categoriezoekterm indien geen platform-specifieke override is opgegeven. | Vrije tekst (zoekterm). |
| `condition` | Algemene conditie indien geen override aanwezig is. | Zie platformsecties hieronder. |
| `location` | Standaard plaatsnaam indien geen override bestaat. | Vrije tekst. |
| `postal_code` | Standaard postcode voor platformen die dit vereisen. | Nederlandse postcode (`1234AB`). |

> **Tip:** Platform-specifieke kolommen overschrijven enkel de corresponderende waarde voor dat platform. Laat een veld leeg als de algemene kolom volstaat.

## Marktplaats kolommen (`marktplaats_` prefix)
| Kolom | Gebruik | Ondersteunde waarden |
| --- | --- | --- |
| `marktplaats_category` | Zoekterm voor de categorie-selector. | Voorbeelden: `Schoenen > Heren`, `Kleding > Dames`, `Elektronica > Televisies`. Volledige categorieboom van Marktplaats wordt ondersteund. |
| `marktplaats_condition` | Selectie in de conditielijst. | `Nieuw`, `Zo goed als nieuw`, `Gebruikt`, `Nieuw met kaartje`, `Nieuw zonder kaartje`. |
| `marktplaats_postal_code` | Postcodeveld in het formulier. | Geldige NL-postcode (bv. `1011AB`). |

## 2dehands kolommen (`tweedehands_` prefix)
| Kolom | Gebruik | Ondersteunde waarden |
| --- | --- | --- |
| `tweedehands_category` | Zoekterm voor de categorie-selector. | Voorbeelden: `Kleding en Schoenen > Herenkleding`, `Multimedia > Audio`, `Huis en Tuin > Meubels`. Volledige 2dehands-categorielijst wordt ondersteund. |
| `tweedehands_condition` | Conditielijst op 2dehands. | `Nieuw`, `Zo goed als nieuw`, `Goed`, `Redelijk`, `Voor onderdelen`. |
| `tweedehands_location` | Plaatsnaam voor locatieveld. | Belgische plaatsnamen (bv. `Antwerpen`, `Gent`, `Brussel`). |

## Facebook Marketplace kolommen (`facebook_` prefix)
| Kolom | Gebruik | Ondersteunde waarden |
| --- | --- | --- |
| `facebook_category` | Zoekterm voor de categoriezoeker. | Voorbeelden: `Men's shoes`, `Electronics`, `Home goods`. Alle categorieën van Marketplace kunnen via zoekterm ingegeven worden. |
| `facebook_condition` | Dropdown "Condition". | `New`, `Used - like new`, `Used - good`, `Used - fair`, `Used - poor`. |
| `facebook_location` | Stad/regio voor de locatiezoeker. | Formaat: `Plaats, Regio` (bv. `Amsterdam, North Holland`). |

## Vinted kolommen (`vinted_` prefix)
| Kolom | Gebruik | Ondersteunde waarden |
| --- | --- | --- |
| `vinted_category` | Zoekterm voor de categoriezoeker. | Voorbeelden: `Heren > Schoenen`, `Heren > Jeans`, `Dames > Jurken`. Volledige categorieboom is beschikbaar via zoeken. |
| `vinted_condition` | Conditielijst van Vinted. | `Nieuw met label`, `Nieuw zonder label`, `Uitstekend`, `Goed`, `Redelijk`, `Slecht`. |
| `vinted_brand` | Zoekveld "Merk". | Vrije tekst; Vinted toont suggesties. |
| `vinted_size` | Zoekveld "Maat". | Gebruik officiële maatnotatie (bv. `EU 42`, `W32/L32`, `M`). |

### Verzenden op Vinted
Vinted gebruikt dezelfde `shipping`-kolom als de algemene kolom. Gebruik `TRUE` om verzendopties aan te zetten en `FALSE` voor enkel afhalen.

## Voorbeeldworkflow
1. Vul alle algemene kolommen in (titel, beschrijving, prijs, afbeeldingen, algemene categorie/conditie/location/postcode).
2. Pas per platform de kolommen met de juiste prefix aan als een platform afwijkende termen verwacht (zoals Engelstalige categorieën op Facebook of specifieke condities op Vinted).
3. Bewaar het CSV-bestand en voer `python -m crosslister.main ...` uit; elke advertentie gebruikt automatisch de juiste waardes voor elk platform.

Met deze legende hoef je zelf geen aanvullende aanpassingen in de code te doen: kies simpelweg de gewenste waardes uit bovenstaande tabellen voor iedere advertentie.
