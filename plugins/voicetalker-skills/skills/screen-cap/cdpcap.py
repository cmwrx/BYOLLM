#!/usr/bin/env python3
"""cdpcap.py - helper for the screen-cap skill (v3.2.7).

Drives a separate Google Chrome over the DevTools protocol, using only the Python
standard library plus Pillow (for cropping). It never types a password and never
reads cookies: the person signs in by hand in the Chrome window this opens.

Library use (from a script in the session scratch folder):
    import sys; sys.path.insert(0, "<folder of this file>")
    from cdpcap import *

Command line:
    python3 cdpcap.py launch <profile_dir> <url> [port]     open Chrome with a throwaway profile
    python3 cdpcap.py check  <scribe.json> [--min-distinct N]  check every file:... screen shot in a Scribe
    python3 cdpcap.py close  <profile_dir> [port] [--delete-profile]  close the capture Chrome and its debug session
    python3 cdpcap.py shoot  <manifest> <entryId> <out.png> [--match host] [--port N]
                             one capture entry of a vt-image-manifest.v2: finds every mustShow phrase on the live page,
                             saves a 1920x1080 tight crop only if every phrase is inside it, prints the result as JSON
    python3 cdpcap.py mark   <manifest> <entryId> approved|retake|skipped [file]   record the person's answer for that shot
    python3 cdpcap.py status <manifest>           every capture entry and where it stands
    python3 cdpcap.py queue  <manifest> [ids]     the entries to shoot now (not approved, or file gone); with ids, exactly those
    python3 cdpcap.py retake <manifest> <ids>     put the named shots back in the queue (their file is forgotten, never deleted)
    python3 cdpcap.py checkplan <manifest>        every approved capture exists, is 1920x1080, not blank, not a repeat
"""
import base64, hashlib, io, json, os, re, socket, struct, subprocess, sys, time, urllib.request


def need_pillow():
    """Pillow is the Python picture library these scripts use to open, crop and save pictures.
    It is not part of Python itself; say plainly how to install it instead of failing with a traceback."""
    try:
        from PIL import Image
    except ImportError:
        sys.exit("FAIL Pillow is not installed. Pillow is the Python picture library this script uses "
                 "to crop and save pictures. Install it with: python3 -m pip install Pillow "
                 "(then check with: python3 -c \"import PIL; print(PIL.__version__)\")")
    return Image

PORT = 9333
W, H = 1920, 1080          # output size and CSS viewport
DPR = 3                    # capture density; crops are scaled down to 1920x1080 from this
CHROME = {
    "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "linux": "google-chrome",
    "win32": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}


# ---------------------------------------------------------------- minimal websocket client
class WS:
    def __init__(self, url):
        m = re.match(r"ws://([^:/]+):(\d+)(/.*)", url)
        host, port, path = m.group(1), int(m.group(2)), m.group(3)
        self.s = socket.create_connection((host, port), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
                        f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        if b" 101 " not in buf.split(b"\r\n")[0]:
            raise RuntimeError("websocket handshake failed")
        self.extra = buf.split(b"\r\n\r\n", 1)[1]

    def _read(self, n):
        while len(self.extra) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise ConnectionError("closed")
            self.extra += chunk
        out, self.extra = self.extra[:n], self.extra[n:]
        return out

    def send(self, text):
        data = text.encode()
        head = bytearray([0x81])
        n = len(data)
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        self.s.sendall(bytes(head) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b""
        while True:
            b1, b2 = self._read(2)
            op, n = b1 & 0x0F, b2 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            if op == 8:
                raise ConnectionError("closed")
            if op in (9, 10):
                continue
            msg += payload
            if b1 & 0x80:
                return msg.decode()


# ---------------------------------------------------------------- page
def targets(port=PORT):
    return json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=10))


class Page:
    """One tab. The viewport override lasts only while this connection is open,
    so every script calls Page.open() and gets 1920x1080 at DPR 3 again."""

    def __init__(self, port=PORT, match="", width=W, height=H, dpr=DPR):
        t = [x for x in targets(port) if x["type"] == "page" and match in x["url"]][0]
        self.ws, self.i, self.url = WS(t["webSocketDebuggerUrl"]), 0, t["url"]
        self.vw, self.vh = width, height
        self.send("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=dpr, mobile=False)
        self.js("window.scrollTo(0,0)")

    def send(self, method, **params):
        self.i += 1
        n = self.i
        self.ws.send(json.dumps({"id": n, "method": method, "params": params}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == n:
                if "error" in r:
                    raise RuntimeError(r["error"])
                return r["result"]

    def js(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        return r["result"].get("value")

    def goto(self, url, wait=5):
        self.send("Page.navigate", url=url)
        time.sleep(wait)

    def type_text(self, text):
        self.send("Input.insertText", text=text)

    def hover(self, x, y):
        self.send("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)

    def box(self, js_elements):
        """Union rectangle [x, y, w, h] in CSS pixels of the elements an expression returns (an array)."""
        r = self.js("JSON.stringify((()=>{const rs=(" + js_elements + ");let a=1e9,b=1e9,c=-1e9,d=-1e9;"
                    "for(const e of rs){const r=e.getBoundingClientRect();a=Math.min(a,r.left);b=Math.min(b,r.top);"
                    "c=Math.max(c,r.right);d=Math.max(d,r.bottom)}return [a,b,c-a,d-b]})())")
        return json.loads(r)

    # ---- clutter hiding: show only chosen parts, everything else invisible (nothing is changed or sent)
    def isolate(self, selectors_or_js):
        self.js("(()=>{const s=document.getElementById('vt-iso');if(s)s.remove();"
                "document.querySelectorAll('[data-keep]').forEach(e=>e.removeAttribute('data-keep'))})()")
        css = ("body *{visibility:hidden!important}[data-keep],[data-keep] *{visibility:visible!important}"
               "html::-webkit-scrollbar,body::-webkit-scrollbar{display:none}html,body{background:#fff!important}")
        self.js("(()=>{const s=document.createElement('style');s.id='vt-iso';s.textContent=%s;document.head.appendChild(s)})()" % json.dumps(css))
        for q in selectors_or_js:
            self.js("(()=>{const r=(%s);(Array.isArray(r)?r:r instanceof NodeList?[...r]:[r]).forEach(e=>e&&e.setAttribute('data-keep',''))})()" % q)
        time.sleep(0.3)

    def unisolate(self):
        self.js("(()=>{const s=document.getElementById('vt-iso');if(s)s.remove();"
                "document.querySelectorAll('[data-keep]').forEach(e=>e.removeAttribute('data-keep'))})()")

    # ---- highlight ring: a rectangle drawn over the page for the capture only (nothing is clicked, changed or saved), removed right after
    def ring(self, boxes, color="#ffb000", pad=6):
        self.unring()
        for b in boxes:
            self.js("(()=>{const d=document.createElement('div');d.setAttribute('data-vt-ring','1');d.style.cssText='position:fixed;pointer-events:none;z-index:2147483647;border:3px solid %s;border-radius:10px;box-shadow:0 0 14px 2px %s;left:%spx;top:%spx;width:%spx;height:%spx';document.body.appendChild(d)})()" % (color, color, b[0] - pad, b[1] - pad, b[2] + 2 * pad, b[3] + 2 * pad))
        time.sleep(0.25)

    def unring(self):
        self.js("document.querySelectorAll('[data-vt-ring]').forEach(e=>e.remove())")

    def fullscreen(self):
        """Put the capture window into full screen (the green button), so the window matches how the Runner is recorded."""
        w = self.send("Browser.getWindowForTarget")
        self.send("Browser.setWindowBounds", windowId=w["windowId"], bounds={"windowState": "fullscreen"})
        time.sleep(1.5)

    # ---- capture
    def full(self):
        Image = need_pillow()
        r = self.send("Page.captureScreenshot", format="png")
        return Image.open(io.BytesIO(base64.b64decode(r["data"]))).convert("RGB")

    # ---- labels on the live page (v2): what the page itself calls its parts
    def candidates(self):
        """Every visible part of the page that has a name: [{tag, role, names[], box[x,y,w,h]}], in CSS pixels."""
        r = self.js(CANDIDATES_JS)
        return json.loads(r)

    def grab(self, out_path, rect, pad=40, minw=700, im=None):
        """Crop a 16:9 window around rect=[x,y,w,h] (CSS px), at least minw wide, clamped inside the
        viewport, and save it as exactly 1920x1080. Returns the crop (x, y, w) and the zoom factor."""
        Image = need_pillow()
        im = im or self.full()
        k = im.size[0] / W
        x, y, w, h = rect
        w2 = min(max(w + 2 * pad, (h + 2 * pad) * 16 / 9, minw), W)
        h2 = w2 * 9 / 16
        x0 = min(max(x + w / 2 - w2 / 2, 0), W - w2)
        y0 = min(max(y + h / 2 - h2 / 2, 0), H - h2)
        c = im.crop((round(x0 * k), round(y0 * k), round((x0 + w2) * k), round((y0 + h2) * k)))
        c.resize((1920, 1080), Image.LANCZOS).save(out_path)
        return (round(x0), round(y0), round(w2)), 1920 / w2


# ---------------------------------------------------------------- v2: match the words of a clip to the live page
CANDIDATES_JS = """JSON.stringify((()=>{
  const out=[], seen=new Set();
  const sel='button,a,[role],input,select,textarea,h1,h2,h3,h4,h5,label,summary,nav,aside,header,footer,section,[aria-label],[title],[data-testid],[id]';
  for(const e of document.querySelectorAll(sel)){
    const r=e.getBoundingClientRect(), cs=getComputedStyle(e);
    if(r.width<4||r.height<4||cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0) continue;
    if(r.right<=0||r.bottom<=0||r.left>=innerWidth||r.top>=innerHeight) continue;
    const vL=Math.max(0,r.left),vT=Math.max(0,r.top),vR=Math.min(innerWidth,r.right),vB=Math.min(innerHeight,r.bottom); // the visible part of the box
    const cx=Math.min(innerWidth-1,(vL+vR)/2), cy=Math.min(innerHeight-1,(vT+vB)/2), hit=document.elementFromPoint(cx,cy);
    if(!hit||!e.contains(hit)) continue; // covered, or scrolled out of a panel that clips it: not visible, so not capturable
    const t=(e.innerText||'').replace(/\\s+/g,' ').trim();
    const names=[e.getAttribute('aria-label'),e.getAttribute('title'),e.getAttribute('placeholder'),
      t&&t.length<=120?t:'',e.id,e.getAttribute('data-testid'),e.getAttribute('role'),
      typeof e.className==='string'?e.className:''].filter(Boolean);
    if(!names.length) continue;
    const key=[Math.round(r.left),Math.round(r.top),Math.round(r.width),Math.round(r.height),names[0]].join('|');
    if(seen.has(key)) continue; seen.add(key);
    const L=Math.max(0,r.left),T=Math.max(0,r.top),R=Math.min(innerWidth,r.right),B=Math.min(innerHeight,r.bottom); // only the visible part can be captured
    out.push({tag:e.tagName.toLowerCase(),role:e.getAttribute('role')||'',names,box:[L,T,R-L,B-T]});
  }
  return out;})())"""


def norm(s):
    """Lowercase words only: '&' reads as 'and', punctuation and case ignored."""
    s = s.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def _tier(names, phrase):
    """0 = a name is exactly the phrase, 1 = the phrase is a whole-word part of a short name, 2 = it is in an id, test id, role or class."""
    p = norm(phrase)
    best = 9
    for i, n in enumerate(names):
        nn = norm(n)
        if not nn:
            continue
        if nn == p:
            best = min(best, 0)
        elif (" " + p + " ") in (" " + nn + " ") and len(nn.split()) <= len(p.split()) + 3:
            best = min(best, 1)
        elif (" " + p + " ") in (" " + nn.replace("-", " ") + " "):
            best = min(best, 2)
    return best


def _center(b):
    return (b[0] + b[2] / 2, b[1] + b[3] / 2)


def resolve(cands, phrases):
    """Find each phrase on the page. Same page and phrases always give the same result.
    Returns (found {phrase: box}, missing [phrase], ambiguous {phrase: [boxes]})."""
    options = {}
    for ph in phrases:
        scored = [(_tier(c["names"], ph), c) for c in cands]
        scored = [(t, c) for t, c in scored if t < 9]
        if not scored:
            options[ph] = []
            continue
        top = min(t for t, _ in scored)
        best = [c["box"] for t, c in scored if t == top]
        best.sort(key=lambda b: (b[2] * b[3], b[1], b[0]))        # most specific (smallest) first, then top-left
        if len(best) > 1 and top >= 1:                              # a part named by its id or class ("rail"): its container, when one box holds all the others
            holder = [b for b in best if all(o[0] >= b[0] - 1 and o[1] >= b[1] - 1 and o[0] + o[2] <= b[0] + b[2] + 1 and o[1] + o[3] <= b[1] + b[3] + 1 for o in best)]
            if holder:
                best = [max(holder, key=lambda b: b[2] * b[3])]
        if len(best) > 1 and top == 0:                              # drop a box that only wraps a smaller exact match
            keep = []
            for b in best:
                if not any(o is not b and o[0] >= b[0] - 1 and o[1] >= b[1] - 1 and o[0] + o[2] <= b[0] + b[2] + 1 and o[1] + o[3] <= b[1] + b[3] + 1 for o in best):
                    keep.append(b)
            best = keep or best
        options[ph] = best
    missing = [ph for ph in phrases if not options[ph]]
    found = {ph: o[0] for ph, o in options.items() if len(o) == 1}
    amb = {ph: o for ph, o in options.items() if len(o) > 1}
    if amb and found:                                               # pick the one nearest the unambiguous parts
        cx = sum(_center(b)[0] for b in found.values()) / len(found)
        cy = sum(_center(b)[1] for b in found.values()) / len(found)
        for ph in list(amb):
            o = sorted(amb[ph], key=lambda b: (_center(b)[0] - cx) ** 2 + (_center(b)[1] - cy) ** 2)
            if len(o) == 1 or ((_center(o[0])[0] - cx) ** 2 + (_center(o[0])[1] - cy) ** 2) * 2 < ((_center(o[1])[0] - cx) ** 2 + (_center(o[1])[1] - cy) ** 2):
                found[ph] = o[0]
                del amb[ph]
    return found, missing, amb


def union(boxes):
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
    return [x0, y0, x1 - x0, y1 - y0]


def inside(crop, box, tol=2):
    """crop = (x0, y0, w) as grab() returns it (height is w * 9 / 16); box = [x, y, w, h]. True only if the whole box is in the crop."""
    x0, y0, w = crop
    h = w * 9 / 16
    return box[0] >= x0 - tol and box[1] >= y0 - tol and box[0] + box[2] <= x0 + w + tol and box[1] + box[3] <= y0 + h + tol


def _center_group(im, rect, group_width=1500, pad=22, bg_xy=(1700, 1060)):
    """The real pixels of the named parts (rings included), cut out alone and placed in the middle of a plain 1920 x 1080 picture whose
    colour is the page's own background. Used when a part sits where the captions will run (the bottom of the screen)."""
    Image = need_pillow()
    k = im.size[0] / W
    x0, y0, w, h = rect
    box = [max(0, round((x0 - pad) * k)), max(0, round((y0 - pad) * k)), min(im.size[0], round((x0 + w + pad) * k)), min(im.size[1], round((y0 + h + pad) * k))]
    group = im.crop(tuple(box))
    scale = min(group_width / group.size[0], 1.9 * k / 1.0) if group.size[0] else 1
    group = group.resize((max(1, round(group.size[0] * scale)), max(1, round(group.size[1] * scale))), Image.LANCZOS)
    bg = im.getpixel((round(bg_xy[0] * k), round(bg_xy[1] * k)))
    canvas = Image.new("RGB", (1920, 1080), bg)
    canvas.paste(group, ((1920 - group.size[0]) // 2, (1080 - group.size[1]) // 2))
    return canvas


def _measure(p, entry):
    # alsoShow: page parts that must be in the picture although the clip's words do not name them (for example the box beside a named avatar)
    found, missing, amb = resolve(p.candidates(), list(entry["mustShow"]) + [x for x in entry.get("alsoShow", []) if x not in entry["mustShow"]])
    for ph, rule in (entry.get("prefer") or {}).items():          # the person said which of several matches to use: "largest" or "smallest" box
        if ph in amb:
            o = sorted(amb.pop(ph), key=lambda b: b[2] * b[3])        # smallest area first
            pos = {"top": lambda b: (b[1], b[0]), "bottom": lambda b: (-b[1], b[0]), "left": lambda b: (b[0], b[1]), "right": lambda b: (-b[0], b[1])}
            found[ph] = min(o, key=pos[rule]) if rule in pos else (o[rule] if isinstance(rule, int) else (o[-1] if rule == "largest" else o[0]))
    return found, missing, amb


def shoot(p, entry, out_path, pad=40):
    """Take the screen shot for one plan entry and PROVE it shows every phrase of entry['mustShow'].
    The parts are measured, the picture taken, and the parts measured AGAIN: if the page moved in between (a scroll still gliding, an
    animation) the shot is taken again, so the proof always describes the picture that was saved.
    Returns {ok, ...}: ok False names the missing or ambiguous phrases (the person is asked); it never saves a picture that fails."""
    start = int(entry.get("frame", {}).get("minCropWidth", 560))
    for attempt in range(4):
        found, missing, amb = _measure(p, entry)
        if missing or amb:
            return {"ok": False, "missing": missing, "ambiguous": amb}
        r = entry.get("ring")                                       # true: ring every named part; a list of phrases: only those
        rings = [found[k] for k in found if r is True or (r and k in r)]
        for ph in entry.get("ringExtra", []):                       # a part the page calls something else than the words do (it is ringed, not proven)
            f2, _, a2 = resolve(p.candidates(), [ph])
            if ph in f2:
                rings.append(f2[ph])
            elif a2.get(ph):
                rings.append(sorted(a2[ph], key=lambda b: b[2] * b[3])[0])
        if rings:
            p.ring(rings)
        im = p.full()
        p.unring()
        again, _, _ = _measure(p, entry)
        if again.keys() != found.keys() or any(abs(a - b) > 2 for k in found for a, b in zip(found[k], again[k])):
            time.sleep(0.7)                                         # the page was still moving; wait and measure again
            continue
        rect = union(list(found.values()))
        if entry.get("frame", {}).get("mode") == "center":          # the named parts (and their rings) alone, in the middle of a plain 16:9 picture
            crop_im = _center_group(im, rect, entry.get("frame", {}).get("groupWidth", 1500), bg_xy=entry.get("frame", {}).get("bgPoint", (1700, 1060)))
            crop_im.save(out_path)
            return {"ok": True, "file": out_path, "crop": "centered group", "zoom": 1.0, "boxes": found}
        for minw in [start, 800, 1100, 1500, W]:
            crop, zoom = p.grab(out_path, rect, pad=pad, minw=max(start, minw), im=im)
            if all(inside(crop, b) for b in found.values()):
                return {"ok": True, "file": out_path, "crop": crop, "zoom": round(zoom, 2), "boxes": found}
        if os.path.exists(out_path):
            os.remove(out_path)
        return {"ok": False, "missing": [], "ambiguous": {}, "reason": "the named parts are too far apart to fit one 16:9 picture", "boxes": found}
    return {"ok": False, "missing": [], "ambiguous": {}, "reason": "the page kept moving; wait for it to settle and try again"}


# ---------------------------------------------------------------- v2: the manifest the plan lives in
FENCE = chr(96) * 3


def load_manifest(path):
    text = open(path, encoding="utf-8").read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    blocks = re.findall(FENCE + r"json\n(.*?)" + FENCE, text, re.S)
    if not blocks:
        raise SystemExit("FAIL the manifest has no json block")
    return json.loads(blocks[-1])


def save_manifest(path, m):
    body = json.dumps(m, indent=2, ensure_ascii=False)
    if path.lower().endswith(".json"):
        open(path, "w", encoding="utf-8").write(body + "\n")
        return
    text = open(path, encoding="utf-8").read()
    a = text.rfind(FENCE + "json\n")
    b = text.find(FENCE, a + 8)
    open(path, "w", encoding="utf-8").write(text[:a] + FENCE + "json\n" + body + "\n" + text[b:])


def mark(manifest_path, entry_id, status, file=None):
    """Record the person's answer for one shot: approved, retake or skipped. A file is kept only when approved."""
    m = load_manifest(manifest_path)
    e = next(x for x in m["plan"] if x["entryId"] == entry_id)
    e["status"] = status
    if file and status == "approved":
        e["file"] = file
    elif status != "approved":
        e.pop("file", None)
    save_manifest(manifest_path, m)


def queue(manifest_path, only=None):
    """The capture entries still to do, in plan order: those not approved, or approved but their file is gone.
    With only=[entryIds] exactly those (a single repair). Approved shots are never in the queue unless named."""
    m = load_manifest(manifest_path)
    base = os.path.dirname(os.path.abspath(manifest_path))
    out = []
    for e in m["plan"]:
        if e.get("kind") != "capture":
            continue
        gone = e.get("status") == "approved" and not os.path.isfile(e["file"] if os.path.isabs(e.get("file", "")) else os.path.join(base, e.get("file", "")))
        if (only and e["entryId"] in only) or (not only and (e.get("status") != "approved" or gone)):
            out.append(e)
    return out


def status(manifest_path):
    m = load_manifest(manifest_path)
    n = {}
    for e in m["plan"]:
        if e.get("kind") == "capture":
            n[e.get("status", "not taken")] = n.get(e.get("status", "not taken"), 0) + 1
            print("%-5s %-9s %s" % (e["entryId"], e.get("status", "not taken"), ", ".join(e["mustShow"])))
    print("capture entries:", ", ".join("%s %d" % kv for kv in sorted(n.items())) or "none")


def check_plan_shots(manifest_path):
    """Every approved capture: the file exists, is 1920x1080, is not blank, and is not the same picture as another."""
    Image = need_pillow()
    m = load_manifest(manifest_path)
    base = os.path.dirname(os.path.abspath(manifest_path))
    ok, seen, n = True, {}, 0
    for e in m["plan"]:
        if e.get("kind") != "capture":      # screen videos are made and checked by screen-cap-video
            continue
        n += 1
        if e.get("status") != "approved":
            print("PENDING", e["entryId"], e.get("status", "not taken"))
            ok = False
            continue
        f = e["file"] if os.path.isabs(e["file"]) else os.path.join(base, e["file"])
        if not os.path.isfile(f):
            print("FAIL missing:", f); ok = False; continue
        if f.lower().endswith(".png"):
            im = Image.open(f)
            if im.size != (W, H):
                print("FAIL size", im.size, f); ok = False
            ext = im.convert("L").getextrema()
            if ext[1] - ext[0] < 8:
                print("FAIL blank picture:", f); ok = False
            h = hashlib.sha1(im.tobytes()).hexdigest()
            if h in seen:
                print("FAIL same picture as", seen[h], ":", e["entryId"]); ok = False
            seen[h] = e["entryId"]
    print("capture shots", n, "| approved", sum(1 for e in m["plan"] if e.get("kind") == "capture" and e.get("status") == "approved"))
    print("RESULT", "PASS" if ok else "FAIL")
    return ok


# ---------------------------------------------------------------- launch and check
def launch(profile_dir, url, port=PORT):
    exe = CHROME.get(sys.platform, "google-chrome")
    subprocess.Popen([exe, f"--user-data-dir={profile_dir}", f"--remote-debugging-port={port}",
                      f"--window-size={W},{H}", "--no-first-run", "--no-default-browser-check", url],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(90):
        if _port_open(port):
            return True
        time.sleep(1)
    return False


def _port_open(port):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2)
        return True
    except Exception:
        return False


def _profile_pids(profile_dir):
    """Process ids whose command line names this throwaway profile (never any other Chrome)."""
    if not profile_dir:
        return []
    out = subprocess.run(["pgrep", "-f", "--", "--user-data-dir=" + profile_dir], capture_output=True, text=True).stdout
    return [int(x) for x in out.split() if x.strip().isdigit() and int(x) != os.getpid()]


def close(profile_dir=None, port=PORT, delete_profile=False):
    """Close the capture Chrome and its debug session. Asks Chrome to quit over the protocol, waits,
    then ends any process still using this throwaway profile. Returns True only when the debug port
    is closed and no process of the profile is left. Deletes the profile folder only if asked."""
    try:
        ws_url = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3))["webSocketDebuggerUrl"]
        w = WS(ws_url)
        w.send(json.dumps({"id": 1, "method": "Browser.close"}))
    except Exception:
        pass
    for _ in range(15):
        if not _port_open(port) and not _profile_pids(profile_dir):
            break
        time.sleep(1)
    for sig in ("-TERM", "-KILL"):
        left = _profile_pids(profile_dir)
        if not left:
            break
        subprocess.run(["kill", sig] + [str(p) for p in left], capture_output=True)
        time.sleep(2)
    done = not _port_open(port) and not _profile_pids(profile_dir)
    if done and delete_profile and profile_dir and os.path.isdir(profile_dir):
        import shutil
        shutil.rmtree(profile_dir, ignore_errors=True)
    return done


def scribe_shots(scribe):
    """[(scene_ordinal, clip_ordinal, path)] for every clip whose backgroundImageId is file:<path>."""
    out = []
    for s in scribe["scenes"]:
        for c in s["clips"]:
            b = c.get("backgroundImageId", "")
            if b.startswith("file:"):
                out.append((s["ordinal"], c["ordinal"], b[5:]))
    return out


def check(scribe_path, min_distinct=1):
    Image = need_pillow()
    ok = True
    shots = scribe_shots(json.load(open(scribe_path, encoding="utf-8")))
    paths = sorted({p for _, _, p in shots})
    hashes = {}
    for p in paths:
        if not os.path.exists(p):
            print("FAIL missing:", p); ok = False; continue
        im = Image.open(p)
        if im.size != (W, H):
            print("FAIL size", im.size, p); ok = False
        ext = im.convert("L").getextrema()
        if ext[1] - ext[0] < 8:
            print("FAIL blank picture:", p); ok = False
        h = hashlib.sha1(im.tobytes()).hexdigest()
        if h in hashes:
            print("FAIL same picture as", os.path.basename(hashes[h]), ":", os.path.basename(p)); ok = False
        hashes[h] = p
    print("clips with a screen shot", len(shots), "| distinct files", len(paths))
    if len(paths) < min_distinct:
        print("FAIL fewer distinct files than", min_distinct); ok = False
    print("RESULT", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["launch"]:
        print("launched" if launch(a[1], a[2], int(a[3]) if len(a) > 3 else PORT) else "FAIL: Chrome did not start")
    elif a[:1] == ["close"]:
        ok = close(a[1], int(a[2]) if len(a) > 2 and a[2].isdigit() else PORT, "--delete-profile" in a)
        print("closed: debug port shut and no Chrome process left for this profile" if ok else "FAIL: Chrome or its debug port is still running")
        sys.exit(0 if ok else 1)
    elif a[:1] == ["check"]:
        md = int(a[a.index("--min-distinct") + 1]) if "--min-distinct" in a else 1
        sys.exit(0 if check(a[1], md) else 1)
    elif a[:1] == ["shoot"]:        # shoot <manifest> <entryId> <out.png> [--match host] [--port N]
        m = load_manifest(a[1])
        e = next(x for x in m["plan"] if x["entryId"] == a[2])
        match = a[a.index("--match") + 1] if "--match" in a else ""
        port = int(a[a.index("--port") + 1]) if "--port" in a else PORT
        r = shoot(Page(port=port, match=match), e, a[3])
        print(json.dumps(r, ensure_ascii=False))
        sys.exit(0 if r["ok"] else 1)
    elif a[:1] == ["mark"]:         # mark <manifest> <entryId> approved|retake|skipped [file]
        mark(a[1], a[2], a[3], a[4] if len(a) > 4 else None)
        print("marked", a[2], a[3])
    elif a[:1] == ["fullscreen"]:    # fullscreen [--match host] [--port N]  the capture window to full screen
        Page(port=int(a[a.index("--port") + 1]) if "--port" in a else PORT, match=a[a.index("--match") + 1] if "--match" in a else "").fullscreen()
        print("full screen")
    elif a[:1] == ["status"]:       # status <manifest>
        status(a[1])
    elif a[:1] == ["queue"]:        # queue <manifest> [entryId ...]  the entries to shoot now, in order (named ids = a repair)
        q = queue(a[1], a[2:] or None)
        print(" ".join(e["entryId"] for e in q) or "nothing to do")
    elif a[:1] == ["retake"]:       # retake <manifest> <entryId> [entryId ...]  put shots back in the queue
        for x in a[2:]:
            mark(a[1], x, "retake")
        print("queued for retake:", " ".join(a[2:]))
    elif a[:1] == ["checkplan"]:    # checkplan <manifest>
        sys.exit(0 if check_plan_shots(a[1]) else 1)
    else:
        print(__doc__)
