import requests

class BaseOAuth():
    TOKEN_URL = ""
    USER_INFO_URL = ""
    AUTH_URL = ""
    USER_EMAILS_URL = ""

    @classmethod
    def post(cls, url, data, headers=None):
        try:
            response = requests.post(
                url=url,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            return {"error": f"{cls.__name__} POST error: {str(e)}"}

    @classmethod  
    def get(cls, url, params=None, headers=None):
        try:
            response = requests.get(
                url=url,
                params=params,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            return {"error": f"{cls.__name__} GET error: {str(e)}"}