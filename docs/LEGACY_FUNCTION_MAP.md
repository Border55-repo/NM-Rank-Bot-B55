# Funksjonskart fra opplastet originalkode

Filen `NordicMafia_rankingBot-master.zip` er datert 21. november 2019. Den er
brukt som funksjonsreferanse for moderniseringen.

| Original funksjon | Ny løsning |
| --- | --- |
| Kriminalitet | HTML/DOM-gjenkjenning og status i kontrollpanelet |
| Fight Club | HTML/DOM-gjenkjenning og cooldown-status |
| Biltyveri | HTML/DOM-gjenkjenning og cooldown-status |
| Utpressing | HTML/DOM-gjenkjenning og cooldown-status |
| Bilsalg | Registreres i selector- og observasjonsdata |
| Bankinnsetting | Penge-/bankelementer registreres i HTML-leseren |
| Fengselskontroll | Automatisk statusvarsling og pause |
| Faste cooldowns | Erstattet av cooldown som leses fra HTML når den finnes |
| Flere kontoer | Ikke aktivert; innlogging og cookies holdes i én lokal profil |

Programmet automatiserer ikke spillhandlinger og inneholder ikke funksjoner for
å skjule bruk for anti-cheat. Mobil- og Windows-utgaven bruker de samme lokale,
rensede statusdataene.
