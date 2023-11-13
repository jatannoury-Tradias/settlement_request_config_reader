import requests
from tools.encryptor import CryptoFilesReader

def get_client_tokens(env):
    password = requests.get(
        f'https://6ka3mfupmsjhfwrp6rvyl73khu0jigbm.lambda-url.eu-central-1.on.aws/?util_type=encryption_password&environment={env.lower()}')
    password = password.json()[
        'password']

    crypto_file_reader_instance = CryptoFilesReader(password=password)
    return crypto_file_reader_instance.get_encrypted_file(env=env)