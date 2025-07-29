# Routemeister Converter Tool

Een Streamlit web-applicatie voor het converteren van Meditec SLK-bestanden naar Routemeister Excel-formaat.

## 🚀 Features

- **SLK naar Excel conversie**: Converteert Meditec SLK-bestanden naar Routemeister-formaat
- **Meertalige interface**: Nederlands, Duits en Engels
- **Automatische data cleaning**: Verwijdert ongeldige tekens
- **Telefoonnummer splitsing**: Automatische splitsing op komma's
- **Data validatie**: Markeert problematische cellen
- **Gebruiksvriendelijke interface**: Upload, preview en download functionaliteit

## 📋 Vereisten

- Python 3.8+
- pip (Python package manager)

## 🛠️ Installatie

1. **Clone de repository:**
   ```bash
   git clone https://github.com/jouw-username/meditec-converter.git
   cd meditec-converter
   ```

2. **Installeer dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start de applicatie:**
   ```bash
   streamlit run simple_app.py
   ```

4. **Open in browser:**
   ```
   http://localhost:8501
   ```

## 📖 Gebruik

1. **Upload SLK bestand**: Sleep of selecteer een `.slk` bestand
2. **Configureer mapping** (optioneel): Pas kolom mapping aan indien nodig
3. **Preview data**: Bekijk de geconverteerde data
4. **Download Excel**: Download het resultaat als Excel-bestand

## 🔧 Configuratie

### Kolom Mapping
De app converteert automatisch naar dit formaat:
- `patient ID` (van `fallnummer`)
- `Name` (van `name`)
- `vorname` (van `vorname`)
- `strasse+nr` (van `strasse`)
- `ort` (van `ort`)
- `PLZ` (van `plz`)
- `landcode` (standaard 'D')
- `1telefon` en `2telefon` (van `telefon`)
- `datum von farht` (van R2C1 in SLK)
- `erster_termin` en `letzter_termin`

### Talen
- 🇳🇱 Nederlands
- 🇩🇪 Deutsch  
- 🇬🇧 English

## 📁 Bestandsstructuur

```
meditec-converter/
├── simple_app.py              # Hoofdapplicatie
├── requirements.txt           # Python dependencies
├── .streamlit/config.toml    # Streamlit configuratie
├── README.md                 # Deze documentatie
├── reha bonn.slk            # Voorbeeld SLK bestand
├── Sample Meditec for Routemeister.xlsx  # Voorbeeld output
└── Routemeister_Logo_White_BG_Larger.png # Logo
```

## 🐛 Troubleshooting

**Probleem**: `IllegalCharacterError` bij Excel export
**Oplossing**: De app markeert automatisch problematische cellen in rood. Controleer het SLK-bestand.

**Probleem**: App laadt niet
**Oplossing**: Controleer of alle dependencies geïnstalleerd zijn met `pip install -r requirements.txt`

## 🤝 Bijdragen

1. Fork de repository
2. Maak een feature branch
3. Commit je wijzigingen
4. Push naar de branch
5. Open een Pull Request

## 📄 Licentie

Dit project is gemaakt voor Meditec data conversie.

## 📞 Contact

Voor vragen of ondersteuning, neem contact op via de repository issues. 