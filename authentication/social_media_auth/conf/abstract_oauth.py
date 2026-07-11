# oauth_contract.py

from abc import ABC, abstractmethod

class OAuthContract(ABC):

    @classmethod
    @abstractmethod
    def get_auth_url(cls):
        pass

    @classmethod
    @abstractmethod
    def exchange_code(cls, code):
        pass

    @classmethod
    @abstractmethod
    def get_user_info(cls, access_token):
        pass