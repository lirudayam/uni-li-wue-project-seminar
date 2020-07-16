import logging
import os

import hvac
from hvac.exceptions import InvalidPath

logging.basicConfig(filename='output.log', level=logging.ERROR)


class HashiVaultCredentialStorage:
    class __HashiVaultCredentialStorage:
        def __init__(self):
            self.client = hvac.Client(url='http://132.187.226.20:8200',
                                      token=os.environ['VAULT_TOKEN'])
            print(self.client.is_authenticated())

    instance = None

    def __init__(self):
        if not HashiVaultCredentialStorage.instance:
            HashiVaultCredentialStorage.instance = HashiVaultCredentialStorage.__HashiVaultCredentialStorage()

    def get_status(self):
        return self.instance.client.is_authenticated()

    def get_credentials(self, path, key):
        if self.get_status():
            try:
                read_response = self.instance.client.secrets.kv.v2.read_secret_version(mount_point='kv', path=path)
                return read_response['data']['data'][key],
            except InvalidPath as e:
                print("Couldn't read path", e)
                return None
