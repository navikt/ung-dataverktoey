from ung_dbverktoey.hemmeligheter import Tilgangskontroll
from msal import ConfidentialClientApplication
import httpx
import io

class SharepointConnector:

    def __init__(self) -> None:
        self.tilgang = Tilgangskontroll()
        self.autentiserings_token = self.autentiser_mot_servicebruker(
            self.tilgang.knada_hemeligheter['sharepoint_ung_client_id'],
            self.tilgang.knada_hemeligheter['sharepoint_ung_tenant_id'],
            self.tilgang.knada_hemeligheter['sharepoint_ung_client_secret']
        )

    def autentiser_mot_servicebruker(self, client_id, tenant_id, client_secret):
        """
        Autentiser med klientkredenter (application permissions).
        """
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return result["access_token"]

    def hent_omraade_id(self, omraade_url, autentiserings_token=None):
        """
        Hent områdeid for spesifisert Sharepoint-side
        """
        if autentiserings_token is None:
            autentiserings_token = self.autentiserings_token

        headers = {
            'Authorization': f'Bearer {autentiserings_token}'
        }
        site_url = f'https://graph.microsoft.com/v1.0/sites/navno.sharepoint.com:/sites/{omraade_url}'
        response = httpx.get(site_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            site = response.json()
            return site['id']
        else:
            raise Exception(f"Error fetching site ID: {response.status_code} - {response.text}")

    def hent_data_fra_sharepoint(self, omraade_url, filsti, autentiserings_token=None):
        """
        Hent innhold fra spesifisert fil fra Sharepoint-område ved å bruke område-URL.
        """
        if autentiserings_token is None:
            autentiserings_token = self.autentiserings_token

        omraade_id = self.hent_omraade_id(omraade_url, autentiserings_token)

        headers = {
            'Authorization': f'Bearer {autentiserings_token}'
        }
        file_url = f'https://graph.microsoft.com/v1.0/sites/{omraade_id}/drive/root:/{filsti}:/content'
        response = httpx.get(file_url, headers=headers, follow_redirects=True)
        if response.status_code == 200:
            data = response.content
            file_stream = io.BytesIO(data)
            return file_stream
        else:
            raise Exception(f"Feil ved henting av fil: {response.status_code} - {response.text}")


    def send_email_med_servicekonto(self, subject, body, mottakere, avsender_epost, cc_mottakere=None, autentiserings_token=None):
        """
        Send an email using Microsoft Graph API.
        """
        if autentiserings_token is None:
            autentiserings_token = self.autentiserings_token

        headers = {
            'Authorization': f'Bearer {autentiserings_token}',
            'Content-Type': 'application/json'
        }

        email_data = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": mottaker}} for mottaker in mottakere
                ],
                "ccRecipients": [
                    {"emailAddress": {"address": recipient}} for recipient in cc_mottakere
                ] if cc_mottakere else [],
                "from": {
                    "emailAddress": {"address": avsender_epost}
                }
            },
            "saveToSentItems": "false"
        }

        user_id = avsender_epost 
        send_mail_url = f'https://graph.microsoft.com/v1.0/users/{user_id}/sendMail'
        response = httpx.post(send_mail_url, headers=headers, json=email_data)

        if response.status_code == 202:
            print("Email sent successfully.")
        else:
            raise Exception(f"Error sending email: {response.status_code} - {response.text}")



if __name__ == "__main__":
    sharepoint = SharepointConnector()
