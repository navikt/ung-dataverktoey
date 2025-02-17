import os
import json
from google.cloud import secretmanager
import gcloud_config_helper
from typing import Optional, Dict
import configparser
import subprocess
from airflow.models import Variable


class Tilgangskontroll:
    """
    En klasse brukt til å håndtere tilgangskontroll.

    Metoder
    -------
    sjekk_om_kjoerelokasjon_er_lokal() -> bool:
        Sjekker om kjøreløkasjonen er lokal.
    hent_datamarkedsplassen_team_token(dev_env: str) -> str:
        Henter team token for datamarkedsplassen.
    hent_prosjektnavn() -> str:
        Henter prosjektnavnet.
    """

    def __init__(self, **kwargs):
        """
        Konstruktør for Tilgangskontroll klassen.
        """
        self.config = configparser.ConfigParser()
        try:
            config_path = os.path.join(self.finn_git_root(), "config.ini")
            self.config.read(config_path)
            if not self.config.sections():
                raise FileNotFoundError(f"No valid sections found in {config_path}, falling back to Airflow variables.")

        except (FileNotFoundError, configparser.Error) as e:
            print(f"Error reading config.ini: {e}. Falling back to Airflow variables.")
            
            self.config["DEFAULT"] = {
                "lokasjon_hemmeligheter": Variable.get("lokasjon_hemmeligheter"),
                "prosjektnavn": Variable.get("prosjektnavn"),
            }
        try:
            self.brukernavn = self._hent_brukernavn()
        except NameError as e:
            print(
                "Error: Failed to authenticate with gcloud. Please run 'gcloud auth login --update-adc'."
            )
            raise RuntimeError("Failed to authenticate with gcloud.") from e
        self.knada_hemeligheter = self._hent_hemmeligheter(
            kwargs.get("hemmelighet_eier", "KNADA")
        )
        self.prosjektnavn = self._hent_prosjektnavn()
        # self.gcp_hemmeligheter = self._hent_hemmeligheter("GCP")

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
            print(f"Error while getting Git root: {e.output.decode('utf-8')}")
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

    def _hent_brukernavn(self) -> str:
        """
        Henter brukernavnet basert på kjøreløkasjonen.

        Returns
        -------
        str
            Brukernavnet.
        """
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
            if "DEFAULT" in self.config and "prosjektnavn" in self.config["DEFAULT"]:
                prosjektnavn = self.config["DEFAULT"]["prosjektnavn"]
            else:
                prosjektnavn = input("Sett prosjektnavnet fra GCP: ")
                self.config["DEFAULT"]["prosjektnavn"] = prosjektnavn
                self._lagre_config()
        else:
            prosjektnavn = self._hent_knada_prosjektnavn()
        return prosjektnavn

    def _hent_knada_prosjektnavn(self) -> str:
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
            Kilden til hemmeligheten.

        Returns
        -------
        Optional[Dict[str, str]]
            Hemmelighetene, eller None hvis ingen hemmeligheter ble funnet.
        """
        if kilde not in self.config:
            self.config[kilde] = {}
            self.config[kilde]["lokasjon_hemmeligheter"] = input(
                f"Legg inn lokasjon for hemmeligheter for {kilde}: "
            )
            self._lagre_config()

        if kilde == "GCP":
            lokasjon_hemmeligheter = f"projects/{self.prosjektnavn}/secrets/knorten_{self.brukernavn}/versions/latest"
        elif kilde == "KNADA" and "KNADA_TEAM_SECRET" in os.environ:
            lokasjon_hemmeligheter = (
                f"{os.environ['KNADA_TEAM_SECRET']}/versions/latest"
            )
        elif kilde == "KNADA" and self.sjekk_om_kjoerelokasjon_er_lokal():
            if (
                "DEFAULT" in self.config
                and "lokasjon_hemmeligheter" in self.config["DEFAULT"]
            ):
                lokasjon_hemmeligheter = self.config["DEFAULT"][
                    "lokasjon_hemmeligheter"
                ]
            else:
                lokasjon_hemmeligheter = input(
                    "Legg inn lokasjon for hemmeligheter e.g. projects/[identifikator]/secrets/[prosjekt]/versions/latest: "
                )
                self.config["DEFAULT"]["lokasjon_hemmeligheter"] = (
                    lokasjon_hemmeligheter
                )
                self._lagre_config()
        elif kilde == "PERSONLIG":
            if (
                "PERSONLIG" in self.config
                and "lokasjon_hemmeligheter" in self.config["PERSONLIG"]
            ):
                lokasjon_hemmeligheter = self.config["PERSONLIG"][
                    "lokasjon_hemmeligheter"
                ]
            else:
                lokasjon_hemmeligheter = input(
                    "Legg inn lokasjon for hemmeligheter e.g. projects/[identifikator]/secrets/[gcp-prosjekt]/versions/latest: "
                )
                self.config["PERSONLIG"]["lokasjon_hemmeligheter"] = (
                    lokasjon_hemmeligheter
                )
                self._lagre_config()
        else:
            return None
        secrets_instans = (
            secretmanager.SecretManagerServiceClient().access_secret_version(
                name=lokasjon_hemmeligheter
            )
        )
        hemmeligheter = json.loads(secrets_instans.payload.data.decode("UTF-8"))
        return hemmeligheter

    def _lagre_config(self):
        """
        Lagrer konfigurasjonen til config.ini-filen og legger til config.ini i .gitignore hvis ønsket.
        """
        while True:
            save_config = (
                input("Vil du lagre konfigurasjonen til config.ini? (ja/nei): ")
                .strip()
                .lower()
            )
            if save_config in ["ja", "nei"]:
                break
            else:
                print("Ugyldig input. Vennligst skriv 'ja' eller 'nei'.")

        if save_config == "ja":
            with open(
                os.path.join(self.finn_git_root(), "config.ini"), "w"
            ) as configfile:
                self.config.write(configfile)
            print("Konfigurasjonen er lagret til config.ini.")

            gitignore_path = os.path.join(self.finn_git_root(), ".gitignore")
            with open(gitignore_path, "r") as gitignore_file:
                gitignore_content = gitignore_file.read()

            if "config.ini" not in gitignore_content:
                while True:
                    add_to_gitignore = (
                        input("Vil du legge til config.ini i .gitignore? (ja/nei): ")
                        .strip()
                        .lower()
                    )
                    if add_to_gitignore in ["ja", "nei"]:
                        break
                    else:
                        print("Ugyldig input. Vennligst skriv 'ja' eller 'nei'.")

                if add_to_gitignore == "ja":
                    with open(gitignore_path, "a") as gitignore_file:
                        gitignore_file.write("\nconfig.ini\n")
                    print("config.ini er lagt til i .gitignore.")
                else:
                    print("config.ini ble ikke lagt til i .gitignore.")
            else:
                pass
        else:
            print("Konfigurasjonen ble ikke lagret.")

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
        team_token = self.knada_hemeligheter[env]
        return team_token
