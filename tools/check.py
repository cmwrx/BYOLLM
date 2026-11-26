#!/usr/bin/env python3
"""Checks for the BYOLLM repository. Standard library only. Prints RESULT PASS or RESULT FAIL."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "plugins", "voicetalker-skills")
fail = []

def need(cond, msg):
    if not cond:
        fail.append(msg)

def load(path):
    try:
        return json.load(open(os.path.join(ROOT, path), encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        fail.append("%s: %s" % (path, e))
        return {}

mk = load(".claude-plugin/marketplace.json")
pj = load("plugins/voicetalker-skills/plugin.json")
cj = load("plugins/voicetalker-skills/.claude-plugin/plugin.json")
xj = load("plugins/voicetalker-skills/.codex-plugin/plugin.json")
V = pj.get("version")
for name, j in (("claude", cj), ("codex", xj)):
    need(j.get("name") == pj.get("name"), "%s manifest name differs" % name)
    need(j.get("version") == V, "%s manifest version differs" % name)
for key in ("name", "owner", "plugins"):
    need(key in mk, "marketplace.json has no " + key)
entries = {e.get("name"): e for e in mk.get("plugins", [])}
e = entries.get(pj.get("name"), {})
need(bool(e), "marketplace entry name differs from plugin.json name")
need(e.get("source") == "./plugins/voicetalker-skills", "marketplace source path is wrong")
need(e.get("version") == V, "marketplace version differs from plugin.json")
cx = load(".agents/plugins/marketplace.json")
ce = {x.get("name"): x for x in cx.get("plugins", [])}.get(pj.get("name"), {})
need(bool(ce), "Codex marketplace entry name differs from plugin.json name")
need(ce.get("source", {}).get("path") == "./plugins/voicetalker-skills", "Codex marketplace source path is wrong")

skills_dir = os.path.join(P, "skills")
names = []
for d in sorted(os.listdir(skills_dir)):
    f = os.path.join(skills_dir, d, "SKILL.md")
    if not os.path.isfile(f):
        continue
    names.append(d)
    t = open(f, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---", t, re.S)
    need(m is not None, d + ": no front matter")
    if m:
        need(re.search(r"^name:\s*%s\s*$" % re.escape(d), m.group(1), re.M) is not None, d + ": name differs from its folder")
        vm = re.search(r'version:\s*"?([0-9.]+)', m.group(1))
        need(vm is not None and vm.group(1) == V, d + ": version is not " + str(V))
need("menu" in names, "no menu skill")

for where in ("docs", "plugins/voicetalker-skills/app"):
    need(os.path.isfile(os.path.join(ROOT, where, "index.html")), where + "/index.html missing")
    data = load(where + "/agent-skills.json")
    need(data.get("meta", {}).get("version") == V, where + ": app version differs from the plugin")
    for k, s in data.get("skills", {}).items():
        need(s.get("name") in names, where + ": app skill not in skills/: " + str(s.get("name")))
    html = open(os.path.join(ROOT, where, "index.html"), encoding="utf-8").read() if os.path.isfile(os.path.join(ROOT, where, "index.html")) else ""
    for a in set(re.findall(r"assets/[A-Za-z0-9_./-]+\.(?:png|jpg|svg)", html)):
        need(os.path.isfile(os.path.join(ROOT, where, a)), where + ": missing " + a)
need(os.path.isfile(os.path.join(ROOT, "LICENSE.txt")), "LICENSE.txt missing")

for dp, _, fs in os.walk(ROOT):
    if "/.git" in dp:
        continue
    for fn in fs:
        if os.path.abspath(os.path.join(dp, fn)) == os.path.abspath(__file__):
            continue
        if fn.endswith((".md", ".txt", ".json", ".html", ".py", ".yml")):
            t = open(os.path.join(dp, fn), encoding="utf-8", errors="ignore").read()
            need("/Users/" not in t, "private path in " + os.path.relpath(os.path.join(dp, fn), ROOT))

if fail:
    for f in fail:
        print("FAIL", f)
    print("RESULT FAIL")
    sys.exit(1)
print("%d skills, version %s" % (len(names), V))
print("RESULT PASS")
