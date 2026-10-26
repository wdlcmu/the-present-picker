#!/usr/bin/env python3
"""Deploy present-picker site files to wdlcmu/the-present-picker via GitHub Git Data API.
Usage: deploy.py <commit message>
Uploads the 13 sitemap pages (homepage + 6 recipient + 4 budget + 2 occasion) plus sitemap.xml, privacy.html, mcp.html, and 404.html from this folder in a single commit.
Auth: stored custom.github credential via dynamic_credentials surrogate (hsurr only, api.github.com only).
Created 2026-10-22 for the Cloudflare Web Analytics beacon ship, modeled on builds/pick-my-resolution/deploy.py.
"""
import sys, os, json, base64, urllib.request, urllib.error

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import dynamic_credential_entry

REPO = "wdlcmu/the-present-picker"
FILES = ["index.html", "gifts-for-dad.html", "gifts-for-mom.html", "gifts-for-partner.html",
         "gifts-for-grandparent.html", "gifts-for-friend.html", "gifts-for-kids.html",
         "gifts-under-25.html", "gifts-25-to-50.html", "gifts-50-to-100.html", "gifts-over-100.html",
         "christmas-gifts.html", "birthday-gifts.html", "og-card.png", "sitemap.xml",
         "privacy.html", "terms.html", "mcp.html", "404.html",
         "img/gift-cooking.jpg", "img/gift-outdoors.jpg", "img/gift-tech.jpg",
         "img/gift-books.jpg", "img/gift-fitness.jpg", "img/gift-cozy.jpg",
         "img/gift-music.jpg", "img/gift-games.jpg", "img/gift-science.jpg",
         "img/gift-gardening.jpg", "img/gift-travel.jpg", "img/gift-keepsake.jpg",
         "img/gift-experience.jpg", "img/gift-kids.jpg", "img/gift-everyday.jpg",
         "img/gift-gift.jpg"]
HERE = os.path.dirname(os.path.abspath(__file__))
SURR = dynamic_credential_entry("custom.github", "access_token")["surrogate"]


def api(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request("https://api.github.com" + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + SURR)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "hatch-agent")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:400]}")


def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "Update site"
    tree_items = []
    for name in FILES:
        with open(os.path.join(HERE, name), "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = api("POST", f"/repos/{REPO}/git/blobs", {"content": content, "encoding": "base64"})
        print(f"blob {name}: {blob['sha']}")
        tree_items.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    ref = api("GET", f"/repos/{REPO}/git/refs/heads/main")
    main_sha = ref["object"]["sha"]
    base_tree = api("GET", f"/repos/{REPO}/git/commits/{main_sha}")["tree"]["sha"]
    tree = api("POST", f"/repos/{REPO}/git/trees", {"base_tree": base_tree, "tree": tree_items})
    commit = api("POST", f"/repos/{REPO}/git/commits",
                 {"message": msg, "tree": tree["sha"], "parents": [main_sha]})
    print(f"commit: {commit['sha']}")
    api("PATCH", f"/repos/{REPO}/git/refs/heads/main", {"sha": commit["sha"], "force": False})
    print(f"https://github.com/{REPO}/commit/{commit['sha']}")


if __name__ == "__main__":
    main()
