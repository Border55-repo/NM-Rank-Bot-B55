# Android-utgave

Dette er en lokal HTML/DOM-assistent med Nordic Mafia i en Android WebView.
Den leser synlige cooldown-, rank-, penge- og statuselementer direkte fra siden
og oppdaterer statusfeltet når HTML-en endres.

Den automatiserer ikke spillaktiviteter. Innlogging og cookies blir værende i
Android WebView på telefonen, og DOM-data sendes ikke til en ekstern tjeneste.

## Bygg

Åpne `android`-mappen i Android Studio, vent på Gradle-synkronisering og velg
**Build > Build APK(s)**. Minste støttede Android-versjon er Android 8.

