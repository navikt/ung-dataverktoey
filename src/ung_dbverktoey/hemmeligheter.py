import os
import json
from google.cloud import secretmanager
from typing import Optional, Dict
import subprocess


class Tilgangskontroll:
    """
    En klasse brukt til å håndtere tilgangskontroll.

    """
    def __init__(self, **kwargs):
        """
        Konstruktør for Tilgangskontroll klassen.
        """

        self.hemmeligheter = self._hent_hemmeligheter(
            kwargs.get("kilde", "team")
        )
        self.prosjektnavn = self._hent_knada_prosjektnavn()

    def finn_git_root(self, path=".") -> str:
        """
        Finner rotkatalogen til git-repositoriet.

        Parameters
        ----------
        path : str, optional
            Startkatalogen for å finne git-roten (default er ".").

        Returns
        -------
        str
            Stien til git-roten.
        """
        try:
            git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], stderr=subprocess.STDOUT)
            return git_root.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            print(f"Feil ved uthenting av Git-root: {e.output.decode('utf-8')}")
            return os.getcwd() 

    def sjekk_om_kjoerelokasjon_er_lokal(self) -> bool:
        """
        Sjekker om kjøreløkasjonen er lokal.

        Returns
        -------
        bool
            True hvis kjøreløkasjonen er lokal, False ellers.
        """
        return "LOGNAME" in os.environ

    def _hent_knada_prosjektnavn(self) -> str:
        """
        Henter prosjektnavnet fra KNADA hemmeligheter.

        Returns
        -------
        str
            Prosjektnavnet.
        """
        prosjektnavn = self.hemmeligheter.get("prosjektnavn")
        if prosjektnavn is None:
            raise ValueError("Hemmeligheten 'prosjektnavn' finnes ikke. Legg til i hemmelighet på knada.")
        return prosjektnavn
    
    
    def _hent_hemmeligheter(self, kilde: str) -> Optional[Dict[str, str]]:
        """
        Henter hemmeligheter fra en gitt kilde.

        Parameters
        ----------
        kilde : str
            Kilden til hemmeligheten.

        Returns
        -------
        Optional[Dict[str, str]]
            Hemmelighetene, eller None hvis ingen hemmeligheter ble funnet.
        """


        kilde = kilde.lower()
        kilde_alternativer = ["personlig", "team"]
        if kilde not in kilde_alternativer:
            raise ValueError(f"Kilde må være i en av disse verdiene: {kilde_alternativer}")

        if kilde == "team":
            knada_team_secret_lokasjon = os.getenv('KNADA_TEAM_SECRET')
            if knada_team_secret_lokasjon is None:
                raise EnvironmentError("Env-variablen 'KNADA_TEAM_SECRET' finnes ikke. Legg til env-variablen. Eksempel: export KNADA_TEAM_SECRET='projects/XXXXXXXXXXXX/secrets/project-name'")
            secret_lokasjon = f"{knada_team_secret_lokasjon}/versions/latest"

        if kilde == "personlig":
            personlig_secret_lokasjon = os.getenv('PERSONLIG_SECRET')
            if personlig_secret_lokasjon is None:
                raise EnvironmentError("Env-variablen 'PERSONLIG_SECRET' finnes ikke. Legg til env-variablen. Eksempel: export PERSONLIG_SECRET='projects/XXXXXXXXXXXX/secrets/project-name'")
            secret_lokasjon = f"{personlig_secret_lokasjon}/versions/latest"

        secrets_instans = (
            secretmanager.SecretManagerServiceClient().access_secret_version(
                name=secret_lokasjon
            )
        )
        hemmeligheter = json.loads(secrets_instans.payload.data.decode("UTF-8"))
        return hemmeligheter
    

    def hent_datamarkedsplassen_team_token(self, dev_env: str) -> str:
        """
        Henter team token for datamarkedsplassen.

        Parameters
        ----------
        dev_env : str
            Utviklingsmiljøet (f.eks. "PROD" eller "DEV").

        Returns
        -------
        str
            Team token.
        """
        if dev_env == "PROD":
            env = "team_token_dmp"
        elif dev_env == "DEV":
            env = "team_token_dev_dmp"
        team_token = self.hemmeligheter.get(env)
        return team_token
