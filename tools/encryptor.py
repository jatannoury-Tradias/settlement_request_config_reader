import base64

import boto3
import pandas as pd
import pyAesCrypt
from os import stat
import io
import json

import requests


s3 = boto3.client('s3')
# encryption/decryption buffer size - 64K
BUFFER = 64 * 1024


# encrypt
class CryptoFilesReader:
    def __init__(self, password: str):
        self.password = password

    def get_decrypted_values(self, encrypted_file_path: str) -> bytes:
        file_size = stat(encrypted_file_path).st_size
        decrypted_stream = io.BytesIO()
        with open(encrypted_file_path, "rb") as in_file:
            pyAesCrypt.decryptStream(in_file, decrypted_stream, self.password, BUFFER, file_size)
        return decrypted_stream.getvalue()


    def get_decrypted_json(self, encrypted_file_path: str) -> dict:
        as_text = self.get_decrypted_values(encrypted_file_path)
        return json.loads(str(as_text, "utf-8"))

    def get_decrypted_values_from_bytesio(self, encrypted_data: io.BytesIO) -> bytes:
        file_size = encrypted_data.getbuffer().nbytes  # Get the size of the BytesIO object
        decrypted_stream = io.BytesIO()
        encrypted_data.seek(0)  # Ensure the BytesIO is at the beginning
        pyAesCrypt.decryptStream(encrypted_data, decrypted_stream, self.password, BUFFER, file_size)
        return decrypted_stream.getvalue()

    def get_encrypted_file(self,env:str):
        base64_encoded_file = requests.get(f'https://6ka3mfupmsjhfwrp6rvyl73khu0jigbm.lambda-url.eu-central-1.on.aws/?util_type=encrypted_file&environment={env.lower()}').text
        decoded_file = base64.b64decode(base64_encoded_file)
        encrypted_stream = io.BytesIO(decoded_file)
        decrypted_stream = io.BytesIO()
        pyAesCrypt.decryptStream(encrypted_stream, decrypted_stream, self.password, BUFFER, encrypted_stream.getbuffer().nbytes)
        decrypted_binary_data = decrypted_stream.getvalue()
        return json.loads(decrypted_binary_data)

if __name__ == "__main__":
    password = requests.get(
        f'https://6ka3mfupmsjhfwrp6rvyl73khu0jigbm.lambda-url.eu-central-1.on.aws/?util_type=encryption_password&environment=preprod')
    password = password.json()[
        'password']

    crypto_file_reader_instance = CryptoFilesReader(password=password)
    data = crypto_file_reader_instance.get_encrypted_file(env='preprod')
    pass