# NM-verktøy B55 v0.4.2

GitHub-repo: `NM-Rank-Bot-B55`

Windows-verktøy med kontinuerlig HTML/DOM-avlesning, cooldown-leser, Learning
Mode og mobilvennlig kontrollpanel på det lokale nettverket. Handlinger utføres
manuelt i spillvinduet.

## Start på Windows

1. Installer Python 3 dersom det ikke allerede er installert.
2. Dobbeltklikk `START_NM_TOOL.bat`.
3. Trykk **Start nettleser** og logg inn manuelt i Chrome.
4. Trykk **Aktiver Work Mode** for kontinuerlig overvåkning.

Chrome-profilen lagres lokalt i `chrome-profile`, slik at vanlig innlogging kan
beholdes. Passord lagres ikke av verktøyet.

## Mobil

PC og telefon må være på samme nett. Trykk **Åpne mobilpanel** og bruk adressen
som vises i loggen på telefonen. Selenium og Chrome kjører fortsatt på PC-en;
telefonen er et responsivt kontrollpanel.

## Sikkerhet og CAPTCHA

Ved CAPTCHA pauses Work Mode automatisk. CAPTCHA må løses manuelt i nettleseren.
Verktøyet prøver ikke å omgå eller løse den automatisk.

## Learning Mode

Kjente selektorer prøves først. Når nettsiden har endret seg, kan verktøyet finne
synlige knapper etter navn. Treff lagres i `data/selectors.json` og prioriteres
ved senere kjøringer. Dersom en aktivitet fortsatt ikke finnes, blir siden bare
observert og det utføres ingen tilfeldig handling.

Programmet inneholder ikke anti-cheat-omgåelse eller automatisk klikking.

## Data for videreutvikling

Verktøyet fører en lokal, renset hendelseslogg i `data/observations.jsonl`.
Spørringsparametre, passord, cookies, sessiondata og hele sideinnhold lagres ikke.
Knappen **Eksporter diagnostikk** samler status, observasjoner og selector-treff i
en ZIP. Send denne ZIP-en i ChatGPT når verktøyet skal tilpasses etter endringer
på Nordic Mafia. Ingenting sendes automatisk fra PC-en.
