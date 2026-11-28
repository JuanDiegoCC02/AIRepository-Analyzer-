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
DIMENSIONS = {
    "popularity", "activity", "documentation",
    "maintainability", "code_quality", "community",
}


def call(payload, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        URL, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.load(error)
        except ValueError:
            return error.code, {}


results = []


def check(name, condition, detail=""):
    results.append(bool(condition))
    print(f"[{'OK' if condition else 'FALLO'}] {name} {detail}")


username = input("Usuario existente: ").strip()
token = str(AccessToken.for_user(get_user_model().objects.get(username=username)))

one = ["https://github.com/facebook/react"]
check("1. Sin token -> 401", call({"repository_urls": one})[0] == 401)

status, _ = call({"repository_urls": one}, token)
check("2. Una sola URL -> 400", status == 400, f"(status {status})")

same = ["https://github.com/facebook/react", "https://github.com/Facebook/React"]
status, _ = call({"repository_urls": same}, token)
check("3. URLs repetidas -> 400", status == 400, f"(status {status})")

bad = ["https://github.com/facebook/react", "http://github.com/vuejs/vue"]
status, body = call({"repository_urls": bad}, token)
check("4. URL no https -> 400 con 'Repository 2'", status == 400 and "Repository 2" in json.dumps(body), f"(status {status})")

missing = [
    "https://github.com/facebook/react",
    "https://github.com/no-existe-xyz-123/repo-inexistente-456",
]
status, body = call({"repository_urls": missing}, token)
check(
    "5. Repo inexistente -> 404 con repository_url",
    status == 404 and body.get("error", {}).get("repository_url") == missing[1],
    f"(status {status})",
)

real = ["https://github.com/pallets/flask", "https://github.com/django/django"]
status, body = call({"repository_urls": real}, token)
ok = (
    status == 200
    and set(body.get("dimensions", {})) == DIMENSIONS
    and len(body.get("repositories", [])) == 2
    and "summary" in body
)
check("6. Comparacion real -> 200 con estructura completa", ok, f"(status {status})")
if status == 200:
    print("   mejor general:", body["summary"]["best_overall"])
    for line in body.get("highlights", []):
        print("   -", line)
    for line in body.get("warnings", []):
        print("   ! aviso:", line)
elif status == 503:
    print("   GitHub limito las peticiones: espera o configura GITHUB_TOKEN.")

print(f"\n{sum(results)}/{len(results)} comprobaciones correctas")
sys.exit(0 if all(results) else 1)
