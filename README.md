# Security Assessment (20 yh-poäng) – kursmaterial

Öppna `index.html` för att komma åt allt material. Den fungerar med dubbelklick i vilken webbläsare som helst.

## Struktur

Varje lektion har samma fyra mappar:

```
<lektion>/
  1. Multimedia/                     podcast (.m4a) och video (.mp4)
  2. PowerPoint med quiz/            presentationen som .pptx och .pdf (sista bilden är quiz)
  3. HTML med interaktiva uppgifter/ workshopen – en fil, tre flikar
  4. Mini projekt/                   kod, skript och exempel att köra själv
```

### 3. HTML med interaktiva uppgifter

Varje workshop har exakt tre flikar:

1. **Individuellt arbete** – snabbövning, kunskapskontroll och labb A (individuellt).
2. **Grupparbete** – gruppövning med roller/register och labb B (grupp).
3. **Facit** – fullständiga svar, rapportgenerator och begreppslista.

Varje sida börjar med en **dra-och-släpp-uppgift** (kort som dras eller klickas till rätt låda, med facit och belöning) och en **stegvisare** där du klickar dig genom momenten i stället för att mötas av en textvägg.

Filerna är helt fristående: all CSS och JavaScript ligger i filen, det finns inga externa resurser och inget behov av server eller internet – de fungerar med dubbelklick från vilken mapp som helst, även om studenten kopierar dem. Svar sparas i `localStorage` när webbläsaren tillåter det.

### 4. Mini projekt

| Lektion | Innehåll |
|---|---|
| 1 | `README.md` – uppdragsavtalet (rules of engagement) |
| 2 | `ICA-banken_phishing_exempel/` – falsk inloggning, dosa och enkätformulär |
| 3 | `README.md` – labbmiljön (VM, snapshot, återställning) |
| 4 | `HTTP/` – Flask-demot `demo.py`, `cookie_demo.py`, `dual_demo.py` |
| 5 | `SQL-injection_and_XSS.py`, `Folkhälsomyndigheten/` (sårbar och fixad portal + databaser) |
| 6 | `DDoS-skript/` – `simple_ddos_lab.py`, `attack.py`, `final_working_hard.py` |
| 7 | `dataförgiftning/` – `cv_ai_attack.py`, `cv_ai_defense.py` |
| 8 | `fientliga_exempel/` – `bank_ai_attack.py`, `bank_ai_defense.py` |

Kör mini-projekten från sin egen mapp, till exempel:

```
cd "4. Natverksanalys med Wireshark/4. Mini projekt/HTTP"
python demo.py            # http://127.0.0.1:8080
python dual_demo.py       # HTTP 8080 + HTTPS 8443
```

```
cd "5. .../4. Mini projekt/Folkhälsomyndigheten"
python folkhalsoportalenFake_XSS_SQLinjection.py   # http://127.0.0.1:5000
```

Krav: Python 3 med `flask` och `requests`. Lektion 7–8 kräver dessutom `pandas`, `scikit-learn`, `matplotlib`, `joblib` (7) samt `scipy` och `seaborn` (8).

DDoS-skripten får bara köras mot egen dator eller egen labb-VM.

## Kursplan

`0. Kursplan/kursplanen (Kursplan Security Assessment 20p).xlsx` innehåller fliken **Förbered inför lektion** (vad som görs före varje lektion, i tabellform) samt plan, examination, teori och uppgifter per lektion.
