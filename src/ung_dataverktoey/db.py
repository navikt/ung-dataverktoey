from ung_dataverktoey.secrets import Tilgangskontroll
import timeit
from google.cloud import bigquery
from google.oauth2 import service_account


class DatabaseConnector:
    def __init__(self):
        self.tilgang = Tilgangskontroll()

    def koble_til_database(self, kilde):
        if kilde == "BQ":
            if self.tilgang.sjekk_om_kjoerelokasjon_er_lokal():
                connection = bigquery.Client(self.tilgang.prosjektnavn)
            else:
                kredentiteter = service_account.Credentials.from_service_account_info(
                    self.tilgang.knada_hemeligheter["service_account_key"]
                )
                connection = bigquery.Client(
                    self.tilgang.prosjektnavn, credentials=kredentiteter
                )

        return connection


def kjoer_spoerring(sql, database, time=False, args=None):
    db_connector = DatabaseConnector()
    timer_start = timeit.default_timer()
    if database == "BQ":
        connection = db_connector.koble_til_database("BQ")
        df = connection.query(sql).to_dataframe()

    timer_stop = timeit.default_timer()
    if time:
        print(f"Spørring tok {(timer_stop - timer_start):.3f} sekunder")
    try:
        df.columns = df.columns.str.lower()
    except AttributeError:
        pass
    return df
