import os
import time
import yaml
from typing import Dict
from ung_dbverktoey.hemmeligheter import Tilgangskontroll


def get_inputs() -> Dict[str, str]:
    """
    Henter input fra en yaml-fil. Hvis filen ikke eksisterer, returnerer den en tom ordbok.

    Returns:
        dict: En ordbok med inputtene.
    """
    inputs_file = "oppdater_datafortelling_siste_inputt.yaml"
    if os.path.exists(inputs_file):
        with open(inputs_file, "r") as file:
            return yaml.safe_load(file)
    else:
        return {}


def save_inputs(inputs: Dict[str, str]) -> None:
    """
    Lagrer inputtene til en yaml-fil.

    Args:
        inputs (dict): En ordbok med inputtene som skal lagres.
    """
    inputs_file = "oppdater_datafortelling_siste_inputt.yaml"
    with open(inputs_file, "w") as file:
        yaml.dump(inputs, file)


def main() -> None:
    """
    Hovedfunksjonen som kjører programmet. Den henter inputtene fra brukeren eller fra en fil,
    og deretter utfører den kommandoer basert på inputtene.
    """
    inputs: Dict[str, str] = get_inputs()
    if inputs is None:
        inputs = {}

    siste_input: str = ""
    while siste_input.lower() not in ["y", "yes", "no", "n"]:
        siste_input = input(
            f"Bruke input fra siste oppdatering? ({inputs.get('datafortelling', '')}) y/N: "
        )
    if siste_input.lower() in ["y", "yes"]:
        pass
    else:
        dashboard: str = ""
        while dashboard.lower() not in ["f", "d"]:
            dashboard = input(
                "Enter 'f' for oppdatering av fortelling eller 'd' for dashboard: "
            )
            if dashboard.lower() not in ["f", "d"]:
                print("Ugyldig inputt. Inputt må være 'f' eller 'd'.")
        if dashboard.lower() == "f":
            type = "datafortellinger"
        if dashboard.lower() == "d":
            type = "dashboards"

        env: str = ""
        while env.lower() not in ["prod", "dev"]:
            env = input(f"Oppgi hvilket miljø det skal lastes opp {type} (prod/dev): ")
            if env.lower() not in ["prod", "dev"]:
                print("Ugyldig inputt. Inputt må være 'prod' eller 'dev'.")

        datafortelling: str = input("Navn på fortelling/dashboard: ")
        token: str = input("Datafortelling-/dashboardtoken: ")

        inputs["dashboard"] = dashboard
        inputs["type"] = type
        inputs["env"] = env
        inputs["datafortelling"] = datafortelling
        inputs["token"] = token

        save_inputs(inputs)

    os.chdir(f"{inputs['datafortelling']}")
    os.environ["TZ"] = "Europe/Oslo"
    time.tzset()

    if inputs["type"] == "datafortellinger":
        os.system(
            """quarto render \
            datafortelling.qmd \
            --to html \
            --execute \
            --output index.html \
            -M self-contained:True
            """
        )
    if inputs["type"] == "dashboards":
        os.system(
            """quarto render \
            dashboard.qmd \
            --execute \
            --output index.html \
            -M self-contained:True
            """
        )

    if inputs["env"] == "prod":
        teamtoken: str = Tilgangskontroll().hent_datamarkedsplassen_team_token("PROD")
        os.system(
            f"""
        curl \
        -X PUT \
        -F index.html=@index.html \
        -H "Authorization:Bearer {teamtoken}" \
        https://datamarkedsplassen.intern.nav.no/quarto/update/{inputs['token']}
        """
        )
    if inputs["env"] == "dev":
        teamtoken: str = Tilgangskontroll().hent_datamarkedsplassen_team_token("DEV")
        os.system(
            f"""
        curl \
        -X PUT \
        -F index.html=@index.html \
        -H "Authorization:Bearer {teamtoken}" \
        https://datamarkedsplassen.intern.dev.nav.no/quarto/update/{inputs['token']}
        """
        )


if __name__ == "__main__":
    main()
