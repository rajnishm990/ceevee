import base64
import os
import secrets

print(f"SECRET_KEY={secrets.token_urlsafe(48)}")
print(f"PDF_ENCRYPTION_KEY={base64.b64encode(os.urandom(32)).decode()}")
