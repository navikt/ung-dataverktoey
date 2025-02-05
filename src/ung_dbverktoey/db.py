from ung_dbverktoey.hemmeligheter import Tilgangskontroll
import timeit
from google.cloud import bigquery
from google.oauth2 import service_account
import oracledb
import warnings
import pandas as pd

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="pandas only supports SQLAlchemy connectable",
)


class DatabaseConnector:
    config = {
        "host_dvh": "dm08-scan.adeo.no:1521/dwh_ha",
    }

    def koble_til_database(self, kilde):
        kilde = kilde.lower()
        if kilde == "bq":
            self.tilgang = Tilgangskontroll()
            if self.tilgang.sjekk_om_kjoerelokasjon_er_lokal():
                connection = bigquery.Client(self.tilgang.prosjektnavn)
            else:
                kredentiteter = service_account.Credentials.from_service_account_info(
                    self.tilgang.knada_hemeligheter["service_account_key"]
                )
                connection = bigquery.Client(
                    self.tilgang.prosjektnavn, credentials=kredentiteter
                )
        if kilde == "dvh":
            self.tilgang = Tilgangskontroll(hemmelighet_eier="PERSONLIG")
            if self.tilgang.sjekk_om_kjoerelokasjon_er_lokal():
                connection = oracledb.connect(
                    user=self.tilgang.knada_hemeligheter["dvh_brukernavn"],
                    password=self.tilgang.knada_hemeligheter["dvh_passord"],
                    dsn=self.config["host_dvh"],
                )

        return connection


def kjoer_spoerring(sql, database, time=False, args=None):
    db_connector = DatabaseConnector()
    timer_start = timeit.default_timer()
    database = database.lower()
    if database == "bq":
        connection = db_connector.koble_til_database("BQ")
        df = connection.query(sql).to_dataframe()
    if database == "dvh":
        connection = db_connector.koble_til_database("DVH")
        df = pd.read_sql(sql, connection)
    timer_stop = timeit.default_timer()
    if time:
        print(f"Spørring tok {(timer_stop - timer_start):.3f} sekunder")
    try:
        df.columns = df.columns.str.lower()
    except AttributeError:
        pass
    return df
