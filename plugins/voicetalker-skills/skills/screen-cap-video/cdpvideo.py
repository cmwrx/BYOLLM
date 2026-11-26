#!/usr/bin/env python3
"""cdpvideo.py - helper for the screen-cap-video skill (v3.2.7).

Records a running web app as MP4 video, frame by frame, with a virtual camera (zoom and pan) and
highlight effects (border, glow, spotlight, marker, arrow, underline, ripple). Standard library plus
Pillow and ffmpeg/ffprobe. It reuses the browser driver of the sibling skill screen-cap
(cdpcap.py): install both skills.

    import sys; sys.path.insert(0, "<folder of this file>")
    from cdpvideo import *            # also gives Page, launch, close, ... from cdpcap

Command line:
    python3 cdpvideo.py durations <scribe.json> [--completed f.json] [--transcript f.txt] [--wpm N]
    python3 cdpvideo.py check     <video.mp4> <expected_seconds> [WxH]
    python3 cdpvideo.py sheet     <video.mp4> <out.png> [frames]
    python3 cdpvideo.py manifest  <scribe.json> <video-folder> <out-manifest.md> [--mode scene|clip|single]
        writes the video cut sheet (vt-video-manifest.v1) that the merge-media skill reads
"""
import io, json, math, os, re, shutil, subprocess, sys, time

# ---- reuse the browser driver (never copy it)
_here = os.path.dirname(os.path.abspath(__file__))
for _d in (os.path.join(os.path.dirname(_here), "screen-cap"),
           os.path.expanduser("~/.claude/skills/screen-cap"),
           os.path.expanduser("~/.agents/skills/screen-cap")):
    if os.path.exists(os.path.join(_d, "cdpcap.py")):
        sys.path.insert(0, _d)
        break
else:
    sys.exit("cdpvideo.py needs the screen-cap skill (cdpcap.py) installed next to it")
from cdpcap import *  # noqa: E402,F401  (Page, WS, launch, close, targets, W, H, ...)
from cdpcap import need_pillow  # noqa: E402  (the Pillow check)

STYLES = ("border", "glow", "spotlight", "marker", "arrow", "underline", "ripple")


def ffbin(name):
    p = shutil.which(name) or next((x for x in (f"/usr/local/bin/{name}", f"/opt/homebrew/bin/{name}") if os.path.exists(x)), None)
    if not p:
        sys.exit(f"{name} not found; install ffmpeg (for example: brew install ffmpeg)")
    return p


# ============================================================ durations (real, then estimated)
def _secs(v):
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    m = re.match(r"^(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)$", str(v).strip())
    return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def _norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def _all_clips(scribe):
    return [(s["ordinal"], c) for s in scribe["scenes"] for c in s["clips"]]


def durations(scribe_path, completed=None, transcript=None, wpm=None, pause=0.5):
    """{clipId: (seconds, source)} with source 'real' or 'estimate'.
    Order of trust: a completed Scribe/run JSON, then a transcript .txt ("[a --> b] Speaker: text"), then
    words / wpm + pause. wpm defaults to the pace written in the clips' style, else the Scribe's default."""
    scribe = json.load(open(scribe_path, encoding="utf-8"))
    clips = _all_clips(scribe)
    out = {}
    if completed:
        done = json.load(open(completed, encoding="utf-8"))
        flat = [c for s in done.get("scenes", []) for c in s.get("clips", [])]
        byid = {c.get("clipId"): c for c in flat}
        for i, (_, c) in enumerate(clips):
            d = byid.get(c["clipId"]) or (flat[i] if len(flat) == len(clips) else None)
            if not d:
                continue
            sec = d.get("durationSeconds") or None
            if not sec:
                a, b = _secs(d.get("startTimestamp")), _secs(d.get("endTimestamp"))
                sec = (b - a) if a is not None and b is not None and b > a else None
            if sec and sec > 0:
                out[c["clipId"]] = (float(sec), "real")
    if transcript:
        rx = re.compile(r"^\[(\d+):(\d+):(\d+(?:\.\d+)?) --> (\d+):(\d+):(\d+(?:\.\d+)?)\]\s*[^:]+:\s*(.*)$")
        rows = []
        for line in open(transcript, encoding="utf-8"):
            m = rx.match(line.strip())
            if m:
                a = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
                b = int(m[4]) * 3600 + int(m[5]) * 60 + float(m[6])
                rows.append((a, b, _norm(m[7])[:30]))
        j = 0
        for _, c in clips:
            key = _norm(re.sub(r";p[\d.]+", "", c["text"]))[:30]
            if c["clipId"] in out:
                continue
            for k in range(j, min(j + 3, len(rows))):
                if rows[k][2] == key:
                    out[c["clipId"]] = (rows[k][1] - rows[k][0], "real")
                    j = k + 1
                    break
    if not wpm:
        m = re.search(r"(\d+)\s*wpm", json.dumps(clips[0][1].get("ttsStyle", {})) if clips else "")
        wpm = int(m.group(1)) if m else scribe.get("settings", {}).get("defaultScrollWpm", 145)
    for _, c in clips:
        if c["clipId"] not in out:
            words = len(re.sub(r";p[\d.]+", "", c["text"]).split())
            out[c["clipId"]] = (words / (wpm / 60.0) + pause, "estimate")
    return out


# ============================================================ beats and camera
class Beat:
    """One stretch of video, normally one clip.
    dur       seconds (from durations())
    targets   JS expression returning an array of elements the camera frames and the effects mark; None = whole page
    setup     JS statements run once at the start (open a menu, type text that is never sent, hover...)
    teardown  JS statements run at the end (close what you opened, clear the text)
    effects   effect names from STYLES, for example ["spotlight", "border"]; [] = none
    color     effect colour (CSS), None = the render default
    pad       camera margin around the targets, in CSS pixels
    minw      narrowest camera window, in CSS pixels (a small icon needs about 480; a column 700; a wide bar 1400)
    zoom      False keeps the camera on the whole page (effects only)
    hold      True keeps the previous camera and shows no effect (a clip with nothing to show)
    """
    def __init__(self, dur, targets=None, setup=(), teardown=(), effects=(), color=None, pad=60, minw=560,
                 zoom=True, hold=False, label=""):
        self.dur, self.targets, self.setup, self.teardown = dur, targets, list(setup), list(teardown)
        self.effects, self.color, self.pad, self.minw, self.zoom, self.hold, self.label = list(effects), color, pad, minw, zoom, hold, label


def _ease(k):
    k = max(0.0, min(1.0, k))
    return 4 * k ** 3 if k < 0.5 else 1 - (-2 * k + 2) ** 3 / 2


OVERLAY_JS = r"""
window.__vt = {
  clear(){ const r=document.getElementById('vt-hl'); if(r) r.remove(); this.items=[]; },
  set(rects, styles, color, appear){
    this.clear(); this.styles=styles; this.color=color; this.appear=appear; this.rects=rects;
    const root=document.createElement('div'); root.id='vt-hl';
    root.style.cssText='position:fixed;left:0;top:0;width:100vw;height:100vh;pointer-events:none;z-index:2147483647;overflow:hidden';
    document.body.appendChild(root); this.root=root; this.items=[];
    for(const r of rects){
      const it={r:r};
      if(styles.some(s=>['border','glow','spotlight'].includes(s))){ it.box=document.createElement('div'); root.appendChild(it.box); }
      if(styles.includes('marker')){ it.marker=document.createElement('div'); root.appendChild(it.marker); }
      if(styles.includes('underline')){ it.under=document.createElement('div'); root.appendChild(it.under); }
      if(styles.includes('ripple')){ it.rip=document.createElement('div'); root.appendChild(it.rip); }
      if(styles.includes('arrow') && this.items.length==0){
        const x1=Math.min(...rects.map(q=>q[0])), y1=Math.min(...rects.map(q=>q[1])), x2=Math.max(...rects.map(q=>q[0]+q[2])), y2=Math.max(...rects.map(q=>q[1]+q[3]));
        it.rU=[x1,y1,x2-x1,y2-y1];
        it.arrow=document.createElementNS('http://www.w3.org/2000/svg','svg');
        it.arrow.setAttribute('width','100%'); it.arrow.setAttribute('height','100%');
        it.arrow.style.cssText='position:absolute;left:0;top:0;overflow:visible';
        root.appendChild(it.arrow);
      }
      this.items.push(it);
    }
  },
  frame(t, dur){
    if(!this.root) return;
    const a=Math.max(0,Math.min(1,(t-this.appear)/0.3))*Math.max(0,Math.min(1,(dur-t)/0.3));
    const p=0.5+0.5*Math.sin(2*Math.PI*t/1.4), c=this.color, s=this.styles;
    for(const it of this.items){
      const r=it.r, g=8;
      if(it.box){
        const b=it.box.style;
        b.position='absolute'; b.left=(r[0]-g)+'px'; b.top=(r[1]-g)+'px'; b.width=(r[2]+2*g)+'px'; b.height=(r[3]+2*g)+'px';
        b.borderRadius='12px'; b.opacity=a; b.boxSizing='border-box';
        b.border=s.includes('border')?'4px solid '+c:'0';
        const sh=[];
        if(s.includes('glow')) sh.push('0 0 '+(22+14*p)+'px '+(5+5*p)+'px '+c);
        if(s.includes('spotlight')) sh.push('0 0 0 5000px rgba(0,0,0,'+(0.58*a)+')');
        b.boxShadow=sh.join(',');
        if(s.includes('spotlight')) b.opacity=1;
      }
      if(it.marker){
        const m=it.marker.style; m.position='absolute'; m.left=(r[0]-4)+'px'; m.top=(r[1]-2)+'px';
        m.width=(r[2]+8)+'px'; m.height=(r[3]+4)+'px'; m.borderRadius='6px'; m.background=c; m.opacity=0.38*a; m.mixBlendMode='multiply';
      }
      if(it.under){
        const u=it.under.style, k=Math.max(0,Math.min(1,(t-this.appear)/0.5));
        u.position='absolute'; u.left=(r[0]-4)+'px'; u.top=(r[1]+r[3]+g)+'px'; u.width=((r[2]+8)*k)+'px'; u.height='5px';
        u.borderRadius='3px'; u.background=c; u.opacity=Math.max(0,Math.min(1,(dur-t)/0.3));
      }
      if(it.rip){
        const q=Math.max(0,(t-this.appear)%1.6)/0.9, rr=18+70*Math.min(q,1), w=it.rip.style;
        w.position='absolute'; w.left=(r[0]+r[2]/2-rr)+'px'; w.top=(r[1]+r[3]/2-rr)+'px'; w.width=(2*rr)+'px'; w.height=(2*rr)+'px';
        w.borderRadius='50%'; w.border='4px solid '+c; w.boxSizing='border-box'; w.opacity=(q<1?1-q:0)*Math.max(0,Math.min(1,(dur-t)/0.3));
      }
      if(it.arrow){
        const R=it.rU, vw=innerWidth, vh=innerHeight, cx=R[0]+R[2]/2, cy=R[1]+R[3]/2;
        const room={l:R[0],r:vw-(R[0]+R[2]),t:R[1],b:vh-(R[1]+R[3])};
        const side=Object.keys(room).reduce((x,y)=>room[x]>=room[y]?x:y);
        const len=70, off=14+10*p, sx=side=='l'?-1:side=='r'?1:0, sy=side=='t'?-1:side=='b'?1:0;
        const tx=cx+sx*(R[2]/2+off), ty=cy+sy*(R[3]/2+off), bx=tx+sx*len, by=ty+sy*len;
        const ang=Math.atan2(ty-by,tx-bx), h=16;
        const hx1=tx-h*Math.cos(ang-0.5), hy1=ty-h*Math.sin(ang-0.5), hx2=tx-h*Math.cos(ang+0.5), hy2=ty-h*Math.sin(ang+0.5);
        it.arrow.style.opacity=a;
        it.arrow.innerHTML='<g stroke="'+c+'" stroke-width="6" stroke-linecap="round" fill="none" style="filter:drop-shadow(0 0 4px rgba(0,0,0,.6))"><line x1="'+bx+'" y1="'+by+'" x2="'+tx+'" y2="'+ty+'"/><polyline points="'+hx1+','+hy1+' '+tx+','+ty+' '+hx2+','+hy2+'"/></g>';
      }
    }
  }
};
"""


def _camera(box, aspect, vw, vh, pad, minw):
    x, y, w, h = box
    cw = min(max(w + 2 * pad, (h + 2 * pad) * aspect, minw), vw)
    ch = cw / aspect
    if ch > vh:
        ch, cw = vh, vh * aspect
    cx = min(max(x + w / 2 - cw / 2, 0), vw - cw)
    cy = min(max(y + h / 2 - ch / 2, 0), vh - ch)
    return (cx, cy, cw)


def render(page, beats, out_path, fps=30, size=(1920, 1080), color="#ffb000", move=0.9, settle=0.4,
           fade=0.0, crf=18, start_full=True, quiet=False):
    """Render the beats in order into one MP4 (no audio). The camera glides between targets in `move` seconds
    and effects appear when it lands. Returns the number of frames written."""
    ow, oh = size
    aspect = ow / oh
    vw, vh = page.vw, page.vh
    total = sum(max(1, round(b.dur * fps)) for b in beats)
    cmd = [ffbin("ffmpeg"), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
           "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(fps)]
    vf = [f"scale={ow}:{oh}:flags=lanczos"]
    if fade > 0:
        vf += [f"fade=t=in:st=0:d={fade}", f"fade=t=out:st={max(0, total / fps - fade):.3f}:d={fade}"]
    cmd += ["-vf", ",".join(vf), "-movflags", "+faststart", out_path]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    page.js(OVERLAY_JS)
    full_cam = _camera((0, 0, vw, vh), aspect, vw, vh, 0, 0)
    prev = full_cam
    n_done = 0
    t0 = time.time()
    try:
        for bi, b in enumerate(beats):
            for js in b.setup:
                page.js(js)
            time.sleep(settle)
            if b.hold:
                cam, rects = prev, []
            elif b.targets and b.zoom:
                box = page.box(b.targets)
                cam, rects = _camera(box, aspect, vw, vh, b.pad, b.minw), None
            else:
                cam, rects = (full_cam if not b.hold else prev), None
            if not b.hold and b.targets and b.effects:
                rects = json.loads(page.js("JSON.stringify((%s).map(e=>{const r=e.getBoundingClientRect();return [r.left,r.top,r.width,r.height]}))" % b.targets))
            moving = abs(cam[0] - prev[0]) + abs(cam[1] - prev[1]) + abs(cam[2] - prev[2]) > 2
            appear = (move + 0.1) if moving else 0.3
            page.js("window.__vt.set(%s,%s,%s,%s)" % (json.dumps(rects or []), json.dumps(b.effects if rects else []),
                                                     json.dumps(b.color or color), appear))
            frames = max(1, round(b.dur * fps))
            src = prev if (bi > 0 or not start_full) else full_cam
            if bi == 0 and start_full:
                src = full_cam
            for i in range(frames):
                t = i / fps
                k = _ease(t / move) if moving else 1.0
                c = tuple(src[j] + (cam[j] - src[j]) * k for j in range(3))
                page.js("window.__vt.frame(%f,%f)" % (t, b.dur))
                clip = {"x": c[0], "y": c[1], "width": c[2], "height": c[2] / aspect, "scale": ow / c[2]}
                r = page.send("Page.captureScreenshot", format="jpeg", quality=92, clip=clip)
                import base64
                ff.stdin.write(base64.b64decode(r["data"]))
                n_done += 1
            if not quiet:
                el = time.time() - t0
                print(f"  beat {bi + 1}/{len(beats)} {b.label or ''} done: {n_done}/{total} frames, {el:.0f}s", flush=True)
            page.js("window.__vt.clear()")
            for js in b.teardown:
                page.js(js)
            prev = cam
    finally:
        try:
            ff.stdin.close()
        except Exception:
            pass
        ff.wait()
    return n_done


# ============================================================ files per clip, scene or tour
def plan_files(scribe_path, beats_by_clip, mode, out_dir, fps=30, gap_seconds=None, durs=None):
    """List of (path, beats) to render.
    mode 'clip'   one MP4 per clip that has a beat   <name>-s02-c07.mp4
    mode 'scene'  one MP4 per scene that has a beat  <name>-scene-02.mp4   (clips without a beat hold the camera)
    mode 'single' one MP4 for the whole Scribe       <name>-tour.mp4       (every scene, so the timing stays the Scribe's)
    beats_by_clip maps clipId -> Beat. Every Beat's dur should come from durations()."""
    scribe = json.load(open(scribe_path, encoding="utf-8"))
    name = scribe.get("scriptName", "scribe")
    durs = durs or durations(scribe_path)
    out = []
    if mode == "clip":
        for s in scribe["scenes"]:
            for c in s["clips"]:
                if c["clipId"] in beats_by_clip:
                    out.append((os.path.join(out_dir, "%s-s%02d-c%02d.mp4" % (name, s["ordinal"], c["ordinal"])), [beats_by_clip[c["clipId"]]]))
        return out
    allb = []
    for s in scribe["scenes"]:
        bl = [beats_by_clip.get(c["clipId"]) or Beat(durs[c["clipId"]][0], hold=True) for c in s["clips"]]
        if mode == "scene" and any(c["clipId"] in beats_by_clip for c in s["clips"]):
            out.append((os.path.join(out_dir, "%s-scene-%02d.mp4" % (name, s["ordinal"])), bl))
        allb += bl          # the single file covers every scene so the timing stays the Scribe's
    if mode == "single":
        out = [(os.path.join(out_dir, "%s-tour.mp4" % name), allb)]
    return out


# ============================================================ checks and a contact sheet
def probe(path):
    r = subprocess.run([ffbin("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,nb_frames:format=duration", "-of", "json", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout or "{}")
    st = (j.get("streams") or [{}])[0]
    num, den = (st.get("r_frame_rate") or "0/1").split("/")
    return {"w": st.get("width"), "h": st.get("height"), "fps": float(num) / float(den or 1),
            "dur": float(j.get("format", {}).get("duration", 0))}


def frame_at(path, sec):
    Image = need_pillow()
    r = subprocess.run([ffbin("ffmpeg"), "-v", "error", "-ss", f"{sec:.3f}", "-i", path, "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "-"],
                       capture_output=True)
    return Image.open(io.BytesIO(r.stdout)).convert("RGB")


def check(path, expected, size=(1920, 1080), tol=0.15):
    ok = True
    if not os.path.exists(path):
        print("FAIL missing", path)
        return False
    p = probe(path)
    if (p["w"], p["h"]) != tuple(size):
        print("FAIL size", (p["w"], p["h"]), "expected", size); ok = False
    if abs(p["dur"] - expected) > tol:
        print("FAIL length %.2f s, expected %.2f s" % (p["dur"], expected)); ok = False
    for k in (0.5, p["dur"] / 2, max(0.1, p["dur"] - 0.5)):
        ex = frame_at(path, k).convert("L").getextrema()
        if ex[1] - ex[0] < 8:
            print("FAIL blank frame at %.1f s" % k); ok = False
    print("%s: %dx%d, %.2f fps, %.2f s (expected %.2f)" % (os.path.basename(path), p["w"], p["h"], p["fps"], p["dur"], expected))
    print("RESULT", "PASS" if ok else "FAIL")
    return ok


def sheet(path, out_png, frames=8):
    Image = need_pillow()
    p = probe(path)
    ims = [frame_at(path, p["dur"] * (i + 0.5) / frames).resize((480, int(480 * p["h"] / p["w"]))) for i in range(frames)]
    cols = 4
    rows = (len(ims) + cols - 1) // cols
    m = Image.new("RGB", (cols * 484, rows * (ims[0].size[1] + 4)), "white")
    for i, im in enumerate(ims):
        m.paste(im, ((i % cols) * 484, (i // cols) * (im.size[1] + 4)))
    m.save(out_png)


# ============================================================ video cut sheet (vt-video-manifest.v1)
# One entry per rendered file: where it attaches in the Scribe (global, scene or clip) and which clips it covers. The
# merge-media skill reads this file and writes `file:<path>` into backgroundImageId at that place; VoiceTalker loads the file.
def _rel_or_abs(path, base):
    rel = os.path.relpath(path, base)
    return path if rel.startswith("..") else rel


def manifest(scribe_path, video_dir, out_path, mode="scene"):
    """Write the cut sheet for the videos in video_dir (named by plan_files: <name>-scene-NN.mp4, <name>-sNN-cMM.mp4, <name>-tour.mp4).
    mode must be the one the videos were rendered with: scene -> attached to the scene (its clips inherit it), clip -> attached to
    that clip, single -> attached to the whole Scribe (the Global picture). Returns the manifest dict."""
    if mode not in ("scene", "clip", "single"):
        raise ValueError("mode must be scene, clip or single")
    scribe = json.load(open(scribe_path, encoding="utf-8"))
    name = scribe.get("scriptName", "scribe")
    base = os.path.dirname(os.path.abspath(out_path))
    cuts, unplaced = [], []

    def add(attach, ids, file, title, scene_id=None, clip_id=None):
        meta = probe(file)
        cut = {"cutId": "V%02d" % (len(cuts) + 1), "title": title, "attach": attach}
        if scene_id:
            cut["sceneId"] = scene_id
        if clip_id:
            cut["clipId"] = clip_id
        cut.update({"clipIds": ids, "file": _rel_or_abs(os.path.abspath(file), base), "fileKind": "final", "mediaType": "video",
                    "durationSeconds": round(meta["dur"], 2), "width": meta["w"], "height": meta["h"], "sizeBytes": os.path.getsize(file)})
        cuts.append(cut)

    if mode == "single":
        f = os.path.join(video_dir, "%s-tour.mp4" % name)
        if os.path.isfile(f):
            add("global", [c["clipId"] for s in scribe["scenes"] for c in s["clips"]], f, scribe.get("title", name))
        else:
            unplaced.append({"where": "whole Scribe", "reason": "no file %s-tour.mp4 in the folder" % name})
    else:
        for s in scribe["scenes"]:
            if mode == "scene":
                f = os.path.join(video_dir, "%s-scene-%02d.mp4" % (name, s["ordinal"]))
                if os.path.isfile(f):
                    add("scene", [c["clipId"] for c in s["clips"]], f, "Scene %d %s" % (s["ordinal"], s["title"]), scene_id=s["sceneId"])
                else:
                    unplaced.append({"where": "scene %d" % s["ordinal"], "reason": "no video was rendered for this scene (it has nothing to show)"})
            else:
                for c in s["clips"]:
                    f = os.path.join(video_dir, "%s-s%02d-c%02d.mp4" % (name, s["ordinal"], c["ordinal"]))
                    if os.path.isfile(f):
                        add("clip", [c["clipId"]], f, "Scene %d clip %d" % (s["ordinal"], c["ordinal"]), clip_id=c["clipId"])
    if not cuts:
        raise SystemExit("STOP: no video files for mode %r in %s" % (mode, video_dir))
    man = {
        "schema": "vt-video-manifest.v1",
        "sourceScribe": {"scriptId": scribe.get("scriptId"), "version": scribe.get("version"), "title": scribe.get("title")},
        "source": {"kind": "screen-cap-video", "folder": os.path.basename(video_dir.rstrip("/")) + "/", "mode": mode},
        "cuts": cuts,
        "unplaced": unplaced,
    }
    L = ["# Video cut sheet for %s" % (scribe.get("title") or name), "",
         "Source: screen videos of the running app (%s files), target Scribe `%s` %s." % (mode, scribe.get("scriptId"), scribe.get("version") or ""), "",
         "| Cut | Attaches to | Covers | File | Length | Size |", "|---|---|---|---|---|---|"]
    for c in cuts:
        where = "whole Scribe" if c["attach"] == "global" else "%s %s" % (c["attach"], c.get("sceneId") or c.get("clipId"))
        L.append("| %s | %s | %s | `%s` | %.1f s | %dx%d |" % (
            c["cutId"], where, c["clipIds"][0] + (" to " + c["clipIds"][-1] if len(c["clipIds"]) > 1 else ""),
            c["file"], c["durationSeconds"], c["width"], c["height"]))
    if unplaced:
        L += ["", "## No video", ""] + ["- %s: %s" % (u["where"], u["reason"]) for u in unplaced]
    L += ["", "```json", json.dumps(man, indent=2, ensure_ascii=False), "```", ""]
    open(out_path, "w", encoding="utf-8").write("\n".join(L))
    return man


if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(n):
        return a[a.index(n) + 1] if n in a else None
    if a[:1] == ["durations"]:
        d = durations(a[1], opt("--completed"), opt("--transcript"), int(opt("--wpm")) if opt("--wpm") else None)
        real = sum(1 for v in d.values() if v[1] == "real")
        print("clips", len(d), "| real", real, "| estimated", len(d) - real, "| total %.1f s" % sum(v[0] for v in d.values()))
    elif a[:1] == ["check"]:
        sz = tuple(int(x) for x in a[3].split("x")) if len(a) > 3 else (1920, 1080)
        sys.exit(0 if check(a[1], float(a[2]), sz) else 1)
    elif a[:1] == ["sheet"]:
        sheet(a[1], a[2], int(a[3]) if len(a) > 3 else 8)
    elif a[:1] == ["manifest"] and len(a) >= 4:
        m = manifest(a[1], a[2], a[3], opt("--mode") or "scene")
        print("wrote", a[3], "| cuts", len(m["cuts"]), "| no video", len(m["unplaced"]), "| total %.1f s" % sum(c["durationSeconds"] for c in m["cuts"]))
    else:
        print(__doc__)
