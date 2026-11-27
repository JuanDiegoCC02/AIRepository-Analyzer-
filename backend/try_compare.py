"""Prueba del endpoint POST /api/compare/.

1. Terminal A:  python manage.py runserver
2. Terminal B:  python try_compare.py

El token JWT se obtiene sin necesidad de una ruta de login: el script
pide el nombre de un usuario existente y genera el token con simplejwt.
Debe ejecutarse desde la carpeta backend (donde esta manage.py).
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from rest_framework_simplejwt.tokens import AccessToken  # noqa: E402

URL = "http://127.0.0.1:8000/api/compare/"
REPOS = [
    "https://github.com/facebook/react",
    "https://github.com/vuejs/vue",
]

username = input("Usuario existente: ").strip()
user = get_user_model().objects.get(username=username)
token = str(AccessToken.for_user(user))

request = urllib.request.Request(
    URL,
    data=json.dumps({"repository_urls": REPOS}).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=300) as response:
        status, body = response.status, json.load(response)
except urllib.error.HTTPError as error:
    status, body = error.code, json.load(error)

print("status:", status)
print(json.dumps(body, indent=2, ensure_ascii=False))
