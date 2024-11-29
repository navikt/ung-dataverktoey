# ung-dataverktoey
Pakke for å hente hemmeligheter og snakke med databaser. Generelle dataverktøy.

## Hemmeligheter
Settes opp via Knorten.

Adressen til hemmelighetene hentes fra google console via link i Knorten. Skal se slik ut:
```
projects/<xxxxxxxx>/secrets/<team-navn>/versions/latest
```

## Spørringer
Gjør spørringer til ønsket google-prosjekt. 
Prosjektnavn:
```
<team-navn-prod-xxxx>
```

## Datafortellinger
Last opp og gjør endringer på eksisterende datafortellinger. Legg til hemmelighet i secret manager via Knorten.
Skal se slik ut:
```
{"team_token_dmp": "xxxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxxxx",
etc..}
```