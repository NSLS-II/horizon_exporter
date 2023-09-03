import json
import requests
import os
import xmltodict


class horizon_uag:
    def __init__(self, url=None):
        if url is None:
            self._url = os.environ['HORIZON_API_GATEWAY_URL']
        else:
            self._url = url

        username = os.environ['HORIZON_API_GATEWAY_USERNAME']
        password = os.environ['HORIZON_API_GATEWAY_PASSWORD']

        self._session = requests.Session()
        self._session.auth = (username, password)

    def _get_xml(self, endpoint):
        response = self._session.get(f"{self._url}{endpoint}")
        data = xmltodict.parse(response.content)
        return data

    def get_monitor(self):
        self._get_xml("/rest/v1/monitor/stats")


class horizon_connection_server:
    def __init__(self, url=None):
        if url is None:
            self._url = os.environ['HORIZON_API_CONNECTION_URL']
        else:
            self._url = url

        self._auth_data = {
            "domain": os.environ['HORIZON_API_CONNECTION_DOMAIN'],
            "username": os.environ['HORIZON_API_CONNECTION_USERNAME'],
            "password": os.environ['HORIZON_API_CONNECTION_PASSWORD'],
        }

        self._access_token = None
        self._refresh_token = None
        self._headers = {
            "accept": "*/*",
            "Content-Type": "application/json",
        }

        self._session = requests.Session()
        self._session.headers.update(self._headers)
        self._session.hooks["response"].append(self.reauthenticate)

    def authenticate(self):
        response = self._session.post(
            f"{self._url}/rest/login", data=json.dumps(self._auth_data)
        )
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._session.headers.update(
            {"Authorization": f"Bearer {self._access_token}"}
        )

    def reauthenticate(self, r, *args, **kwargs):
        if r.status_code == 401:
            if self._refresh_token is not None:
                auth_data = {"refresh_token": self._refresh_token}
                response = self._session.post(
                    f"{self._url}/rest/refresh", data=json.dumps(auth_data)
                )
                data = response.json()
                self._access_token = data["access_token"]
                self._session.headers.update(
                    {"Authorization": f"Bearer {self._access_token}"}
                )
            else:
                self.authenticate()

            r.request.headers["Authorization"] = self._session.headers[
                "Authorization"]
            return self._session.send(r.request)

    def _get(self, endpoint):
        response = self._session.get(f"{self._url}{endpoint}")
        data = response.json()
        return data

    def get_monitor_gateways(self):
        return self._get("/rest/monitor/v3/gateways")

    def get_monitor_connection_servers(self):
        return self._get("/rest/monitor/v3/connection-servers")
