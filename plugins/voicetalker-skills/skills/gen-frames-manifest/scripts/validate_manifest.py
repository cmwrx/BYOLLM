import json
import sys
from pathlib import Path

RATIOS = {"16:9": (16, 9), "9:16": (9, 16), "1:1": (1, 1)}


def check(path, source_path=None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    errors = []
    warnings = []
    scene_ids = set()
    clip_ids = set()
    frame_ids = set()
    frame_count = 0
    clip_count = 0
    if not isinstance(scenes, list):
        return {"errors": ["scenes must be a list"], "warnings": [], "scenes": 0, "clips": 0, "frames": 0}
    for si, scene in enumerate(scenes, 1):
        sid = scene.get("sceneId")
        if not sid or sid in scene_ids:
            errors.append(f"scene {si}: missing or duplicate sceneId {sid}")
        scene_ids.add(sid)
        for ci, clip in enumerate(scene.get("clips", []), 1):
            clip_count += 1
            cid = clip.get("clipId")
            label = f"S{si}C{ci}"
            if not cid or cid in clip_ids:
                errors.append(f"{label}: missing or duplicate clipId {cid}")
            clip_ids.add(cid)
            frames = clip.get("frames", [])
            if not isinstance(frames, list):
                errors.append(f"{label}: frames must be a list")
                continue
            policy = clip.get("flipbookPolicy", {})
            expected = policy.get("frameCount", data.get("imagesPerClip", 3))
            if len(frames) != expected:
                errors.append(f"{label}: expected {expected} frames; found {len(frames)}")
            master = policy.get("masterCompositionId") or (f"{cid}-master" if cid else None)
            if not policy:
                warnings.append(f"{label}: flipbookPolicy missing")
            elif not policy.get("cameraLockedAcrossFrames", False):
                errors.append(f"{label}: cameraLockedAcrossFrames not true")
            if policy and not policy.get("stationaryGeometryLockedAcrossFrames", False):
                errors.append(f"{label}: stationaryGeometryLockedAcrossFrames not true")
            ratios_in_clip = set()
            resolutions_in_clip = set()
            for fi, frame in enumerate(frames, 1):
                frame_count += 1
                at = f"{label}F{fi}"
                fid = frame.get("frameId")
                if not fid or fid in frame_ids:
                    errors.append(f"{at}: missing or duplicate frameId {fid}")
                frame_ids.add(fid)
                ratio = frame.get("aspectRatio", data.get("aspectRatio", "16:9"))
                ratios_in_clip.add(ratio)
                if ratio not in RATIOS:
                    errors.append(f"{at}: invalid ratio {ratio}")
                res = frame.get("targetResolution")
                if res:
                    try:
                        width, height = [int(v) for v in res.lower().split("x")]
                        resolutions_in_clip.add((width, height))
                        if ratio in RATIOS:
                            rw, rh = RATIOS[ratio]
                            if width * rh != height * rw:
                                errors.append(f"{at}: {res} incompatible with {ratio}")
                    except (ValueError, AttributeError):
                        errors.append(f"{at}: invalid resolution {res}")
                if not frame.get("prompt") and not frame.get("imagePrompt"):
                    errors.append(f"{at}: missing prompt/imagePrompt")
                if not frame.get("imageId") and not frame.get("fileName"):
                    errors.append(f"{at}: missing image reference")
                cont = frame.get("continuity", {})
                if cont.get("masterCompositionId") != master:
                    errors.append(f"{at}: masterCompositionId differs from clip master")
                if cont.get("stationaryObjectsLocked") is False:
                    errors.append(f"{at}: stationaryObjectsLocked false")
                if cont.get("incrementalChangesOnly") is False:
                    errors.append(f"{at}: incrementalChangesOnly false")
                for field in ("mouthCoordinates", "speechBubbleCoordinates"):
                    value = frame.get(field)
                    if isinstance(value, dict):
                        x, y = value.get("x"), value.get("y")
                        if (x is None) != (y is None):
                            errors.append(f"{at}: {field} incomplete coordinate pair")
                        elif x is not None and not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and 0 <= x <= 1 and 0 <= y <= 1):
                            errors.append(f"{at}: {field} normalized x/y out of bounds")
                mouth = frame.get("mouth")
                if isinstance(mouth, dict):
                    coords = mouth.get("normalized", mouth)
                    if isinstance(coords, dict):
                        x, y = coords.get("x"), coords.get("y")
                        if (x is None) != (y is None):
                            errors.append(f"{at}: mouth normalized coordinates incomplete")
                        if x is not None and not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and 0 <= x <= 1 and 0 <= y <= 1):
                            errors.append(f"{at}: mouth normalized coordinates out of bounds")
                bubble = frame.get("speechBubble")
                if isinstance(bubble, dict):
                    pos = bubble.get("position")
                    if isinstance(pos, dict):
                        x, y = pos.get("x"), pos.get("y")
                        if (x is None) != (y is None):
                            errors.append(f"{at}: speechBubble.position incomplete")
                        if x is not None and not (isinstance(x,(int,float)) and isinstance(y,(int,float)) and 0<=x<=1 and 0<=y<=1):
                            errors.append(f"{at}: speechBubble.position out of bounds")
                if frame.get("imageStatus") in ("generated", "approved") and frame.get("alignmentStatus") in (None, "unverified", "prompt_aligned"):
                    warnings.append(f"{at}: image generated/approved but alignment lacks measured verification")
            if len(ratios_in_clip) > 1 or len(resolutions_in_clip) > 1:
                errors.append(f"{label}: frames do not share aspect ratio and resolution")
    if data.get("clipCount") is not None and data["clipCount"] != clip_count:
        errors.append("clipCount does not match actual count")
    if data.get("imageCount") is not None and data["imageCount"] != frame_count:
        errors.append("imageCount does not match actual count")
    if source_path:
        src = json.loads(Path(source_path).read_text(encoding="utf-8"))
        source_scenes = src.get("scenes", [])
        if len(source_scenes) != len(scenes):
            errors.append("source preservation: scene count changed")
        for si, (a, b) in enumerate(zip(source_scenes, scenes), 1):
            if a.get("sceneId") != b.get("sceneId"):
                errors.append(f"S{si}: sceneId changed")
            if a.get("title") != b.get("title"):
                errors.append(f"S{si}: title changed")
            ac = a.get("clips", [])
            bc = b.get("clips", [])
            if len(ac) != len(bc):
                errors.append(f"S{si}: clip count changed")
            for ci, (ca, cb) in enumerate(zip(ac, bc), 1):
                if ca.get("clipId") != cb.get("clipId"):
                    errors.append(f"S{si}C{ci}: clipId changed")
                for key in ("speaker", "text", "dialogue", "ttsProvider", "ttsVoice", "ttsInstructions", "ttsStyle", "ttsEnabled", "translations", "backgroundImageId"):
                    if key in ca and ca.get(key) != cb.get(key):
                        errors.append(f"S{si}C{ci}: source field changed: {key}")
        # A detailed deep-diff of all unrelated fields is recommended in production and must not be claimed here.
    return {"scenes": len(scenes), "clips": clip_count, "frames": frame_count,
            "errors": errors, "warnings": warnings, "imagePixelQcPerformed": False,
            "speakerMouthMeasured": False, "runtimePlaybackVerified": False}


if __name__ == "__main__":
    if len(sys.argv) not in (2,3):
        print("Usage: python3 validate_manifest.py manifest.json [source_scribe_or_manifest.json]", file=sys.stderr)
        sys.exit(2)
    result = check(sys.argv[1], sys.argv[2] if len(sys.argv) == 3 else None)
    print(json.dumps(result, indent=2))
    sys.exit(1 if result["errors"] else 0)
