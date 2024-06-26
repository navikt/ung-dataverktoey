import os
import json
from google.cloud import secretmanager
import gcloud_config_helper
from typing import Optional, Dict
import configparser
import subprocess


class Tilgangskontroll:
    """
    En klasse brukt til å håndtere tilgangskontroll.

    ...

    Metoder
    -------
    sjekk_om_kjoerelokasjon_er_lokal():
        Sjekker om kjøreløkasjonen er lokal.
    hent_datamarkedsplassen_team_token(dev_env: str) -> str:
        Henter team token for datamarkedsplassen.
    hent_prosjektid_amplitude() -> str:
        Henter prosjektid for amplitude.
    """

    def __init__(self):
        """
        Konstruktør for Tilgangskontroll klassen.
        """
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(self.finn_git_root(), 'config.ini'))
        self.brukernavn = self._hent_brukernavn()
        self.knada_hemeligheter = self._hent_hemmeligheter("KNADA")
        self.prosjektnavn = self._hent_prosjektnavn()
        #self.gcp_hemmeligheter = self._hent_hemmeligheter("GCP")
    

    def finn_git_root(self, path='.'):
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=path)
        return git_root.decode('utf-8').strip()

    def sjekk_om_kjoerelokasjon_er_lokal(self) -> bool:
        """
        Sjekker om kjøreløkasjonen er lokal.

        Returns
        -------
        bool
            True hvis kjøreløkasjonen er lokal, False ellers.
        """
        return "LOGNAME" in os.environ   


    def _hent_brukernavn(self) -> str:
        if self.sjekk_om_kjoerelokasjon_er_lokal():
            brukernavn = (
                gcloud_config_helper.default()[0]
                .properties["core"]["account"]
                .split("@")[0]
                .replace(".", "_")
                )
        elif "JUPYTERHUB_USER" in os.environ:
            brukernavn = os.environ["JUPYTERHUB_USER"].split("@")[0].replace(".", "_")
        else:
            brukernavn = "airflow"
        return brukernavn

    def _hent_prosjektnavn(self) -> str:
        """
        Henter prosjektnavnet.

        Returns
        -------
        str
            Prosjektnavnet.
        """
        if self.sjekk_om_kjoerelokasjon_er_lokal():
            if 'DEFAULT' in self.config and 'prosjektnavn' in self.config['DEFAULT']:
                prosjektnavn = self.config['DEFAULT']['prosjektnavn']
            else:
                prosjektnavn = input("Sett prosjektnavnet fra GCP: ")
                self.config['DEFAULT']['prosjektnavn'] = prosjektnavn
                with open(os.path.join(self.finn_git_root(), 'config.ini'), 'w') as configfile:
                    self.config.write(configfile)
        else:
            prosjektnavn = self._hent_knada_prosjektnavn()
        return prosjektnavn
    

    def _hent_knada_prosjektnavn(self):
        """
        Henter prosjektnavnet fra KNADA hemmeligheter.

        Returns
        -------
        str
            Prosjektnavnet.
        """
        prosjektnavn = self.knada_hemeligheter["GCP_PAW_PROD"].get("project_id")
        return prosjektnavn


    def _hent_hemmeligheter(self, kilde: str) -> Optional[Dict[str, str]]:
        """
        Henter hemmeligheter fra en gitt kilde.

        Parameters
        ----------
        kilde : str
            Kilden til hemmelighetene.

        Returns
        -------
        dict
            Hemmelighetene.
        """
        if kilde == "GCP":
            lokasjon_hemmeligheter = f"projects/{self.prosjektnavn}/secrets/knorten_{self.brukernavn}/versions/latest"
        elif kilde == "KNADA" and "KNADA_TEAM_SECRET" in os.environ:
            lokasjon_hemmeligheter = f"{os.environ['KNADA_TEAM_SECRET']}/versions/latest"
        elif kilde == "KNADA" and self.sjekk_om_kjoerelokasjon_er_lokal():
            if 'DEFAULT' in self.config and 'lokasjon_hemmeligheter' in self.config['DEFAULT']:
                lokasjon_hemmeligheter = self.config['DEFAULT']['lokasjon_hemmeligheter']
            else:
                lokasjon_hemmeligheter = input("Legg inn lokasjon for hemmeligheter e.g. projects/[identifikator]/secrets/[gcp-prosjekt/versions/latest: ")
                self.config['DEFAULT']['lokasjon_hemmeligheter'] = lokasjon_hemmeligheter
                with open(os.path.join(self.finn_git_root(), 'config.ini'), 'w') as configfile:
                    self.config.write(configfile)
                self.config.read(os.path.join(self.finn_git_root(), 'config.ini'))
        else:
            return
        secrets_instans = secretmanager.SecretManagerServiceClient(
                            ).access_secret_version(name=lokasjon_hemmeligheter)
        hemmeligheter = json.loads(secrets_instans.payload.data.decode("UTF-8"))
        return hemmeligheter

    def hent_datamarkedsplassen_team_token(self, dev_env: str) -> str:
        """
        Henter team token for datamarkedsplassen.

        Parameters
        ----------
        dev_env : str
            Utviklingsmiljøet.

        Returns
        -------
        str
            Team token.
        """
        if dev_env == "PROD":
            env = "team_token_dmp"
        elif dev_env == "DEV":
            env = "team_token_dev_dmp"
        team_token = self.gcp_hemmeligheter[env]
        return team_token