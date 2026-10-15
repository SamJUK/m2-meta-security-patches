#!/usr/bin/env python3
"""Pull Adobe's newest isolated CE patches into this repo, unmodified.

  python3 -I bin/ingest-adobe-patches.py [--dry-run]

Appends each new month to its base line in patches/isolated/patches.json, but only
when Adobe's own `requires` says it follows the month already there. Anything that
needs a decision (a new patch level, an out-of-band VULN patch, a line Adobe has
moved to Commerce-only) is reported, never added. JSON on stdout.
"""
import datetime, hashlib, io, json, re, sys, urllib.error, urllib.request, zipfile
from pathlib import Path

REGISTRY = "https://repo.magento.com/patch/patch-registry.json"
PATCH_URL = "https://repo.magento.com/patch/"
ROOT = Path(__file__).resolve().parents[1]
ISOLATED = ROOT / "patches" / "isolated"
EMERGENCY = ROOT / "patches" / "emergency"

ID = re.compile(r"(\d{3}(?:p\d+)?)-(\d{4}-\d{2}-\d{3}|VULN-\d+)-([A-Za-z0-9]{1,20})")
MONTH = re.compile(r"\d{4}-\d{2}-\d{3}")
VERSION = re.compile(r"\d+\.\d+\.\d+(?:-p\d+)?")
SHA = re.compile(r"[0-9a-f]{64}")
DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,120}")
TARGET = re.compile(r"^(?:\+\+\+ b/|diff --git a/)(\S+)", re.M)


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "m2-meta-security-patches"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def registry():
    """Registry entries, every field validated. A malformed entry is named, never used."""
    good, malformed = {}, []
    for pid, e in json.loads(get(REGISTRY))["patches"].items():
        ok = (
            isinstance(e, dict) and ID.fullmatch(str(pid))
            and SHA.fullmatch(str(e.get("sha256", ""))) and NAME.fullmatch(str(e.get("file_name", "")))
            and DATE.fullmatch(str(e.get("released", ""))) and re.fullmatch(r"[A-Za-z0-9]{1,20}", str(e.get("area", "")))
            and isinstance(e.get("applies_to"), list) and all(VERSION.fullmatch(str(v)) for v in e["applies_to"])
            and isinstance(e.get("requires", []), list) and all(ID.fullmatch(str(r)) for r in e.get("requires", []))
        )
        if not ok:
            malformed.append(str(pid) if ID.fullmatch(str(pid)) else "<malformed id>")
            continue
        good[pid] = {
            "applies_to": e["applies_to"], "sha256": e["sha256"], "file_name": e["file_name"],
            "released": e["released"], "requires": e.get("requires", []), "area": e["area"],
            "ee_only": "ee" in (e.get("entitlements") or []), "cves": len(e.get("cves") or []),
        }
    return good, malformed


def download(entry):
    """Flat URL first; monthly patches also ship in one zip per patch level per month."""
    try:
        raw = get(PATCH_URL + entry["file_name"])
    except urllib.error.HTTPError as err:
        if err.code != 404:
            raise
        released = datetime.date.fromisoformat(entry["released"])
        bundle = f"{entry['applies_to'][0].replace('.', '-')}-{released.strftime('%b').lower()}-{released.year}.zip"
        stem = entry["file_name"].rsplit(".", 1)[0]
        with zipfile.ZipFile(io.BytesIO(get(PATCH_URL + bundle))) as z:
            match = [n for n in z.namelist() if n.rsplit("/", 1)[-1].rsplit(".", 1)[0] == stem]
            if not match:
                raise RuntimeError(f"{entry['file_name']} is not at its URL or in {bundle}")
            raw = z.read(match[0])
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise RuntimeError(f"sha256 mismatch for {entry['file_name']}")
    return raw


def targets(text):
    """Files a patch touches, with magento2-base's copy and the root copy as one file."""
    return {t.removeprefix("vendor/magento/magento2-base/") for t in TARGET.findall(text) if t != "/dev/null"}


def ver_key(version):
    return tuple(int(x or 0) for x in re.match(r"(\d+)\.(\d+)\.(\d+)(?:-p(\d+))?", version).groups())


def label(month):
    name = datetime.date.fromisoformat(month[:7] + "-01").strftime("%B")
    return name if month.endswith("-001") else f"{name} ({month[-3:]})"


def main():
    dry = "--dry-run" in sys.argv[1:]
    manifest_path = ISOLATED / "patches.json"
    manifest = json.loads(manifest_path.read_text())
    emergency = json.loads((EMERGENCY / "patches.json").read_text())
    entries, malformed = registry()
    report = {"dry_run": dry, "added": [], "decisions": [], "malformed_registry_entries": malformed}
    pending = {}

    def text_of(path):
        return pending[path].decode("utf-8", errors="replace") if path in pending else path.read_text()

    monthly = {}
    for pid, e in entries.items():
        m = ID.fullmatch(pid)
        if e["area"] == "CE" and MONTH.fullmatch(m.group(2)):
            for version in e["applies_to"]:
                monthly.setdefault(version, {})[m.group(2)] = (pid, e)

    for version, line in manifest["lines"].items():
        have = [p["id"] for p in line["patches"]]
        months = monthly.get(version, {})
        last = months.get(have[-1], (None, None))[0]

        for month in sorted(mo for mo in months if mo > have[-1]):
            pid, e = months[month]
            # Adobe lists either the month before or, from October 2026, the whole chain.
            chain = [months[m][0] for m in have if m in months]
            if last is None or e["requires"] not in ([last], chain):
                report["decisions"].append(
                    f"{pid} requires {e['requires']}, but the {version} chain ends at {have[-1]} ({last}). Not added."
                )
                break

            # No credentials, deliberately. A file Adobe gates to Commerce
            # customers is a question of whether this public package may ship
            # it, not a download problem to work around.
            try:
                raw = download(e)
            except urllib.error.HTTPError as err:
                gated = " Adobe gates it to Commerce customers (entitlement 'ee')." if e["ee_only"] else ""
                report["decisions"].append(f"{e['file_name']}: HTTP {err.code} from repo.magento.com.{gated} Not added.")
                break

            path = ISOLATED / month / f"{version}-CE.patch"
            if path.exists() and path.read_bytes() != raw:
                report["decisions"].append(f"{path.relative_to(ROOT)} exists with different content. Not overwritten.")
                break

            text = raw.decode("utf-8", errors="replace")
            earlier = set().union(*(targets(text_of(ISOLATED / p["source"])) for p in line["patches"]))
            beside = set().union(*(
                targets((EMERGENCY / p["source"]).read_text())
                for p in emergency.get("lines", {}).get(version, {}).get("patches", [])
            ))
            new = targets(text)

            report["added"].append({
                "line": version, "id": month, "registry_id": pid, "file": str(path.relative_to(ROOT)),
                "sha256": e["sha256"], "released": e["released"], "cves": e["cves"], "files": len(new),
                "root_or_vendor_bin": sorted(t for t in new if not t.startswith("vendor/") or t.startswith("vendor/bin/")),
                # Supported by magento-patch-installer >= 0.2.1: the earlier month is checked beneath this one.
                "rewrites_earlier_months": sorted(new & earlier),
                # Not built on each other, so an overlap here is a real clash.
                "overlaps_emergency_patches": sorted(new & beside),
            })
            if e["ee_only"]:
                report["decisions"].append(f"{pid}: Adobe lists {version} as Commerce-only (entitlement 'ee') from {month}.")

            pending[path] = raw
            line["patches"].append({
                "id": month,
                "source": f"{month}/{version}-CE.patch",
                "label": f"{label(month)} Isolated",
                "description": f"Adobe isolated security patch for {label(month)} {month[:4]} (Community Edition).",
            })
            have.append(month)
            last = pid

    covered = list(manifest["lines"])
    newest = max(covered, key=ver_key)
    for version in sorted(monthly, key=ver_key):
        same_branch = [c for c in covered if ver_key(c)[:3] == ver_key(version)[:3]]
        if version in covered:
            continue
        if same_branch and ver_key(version) > ver_key(same_branch[0]):
            report["decisions"].append(f"Adobe now publishes isolated patches for {version}, newer than the {same_branch[0]} line. Needs a new line.")
        elif not same_branch and ver_key(version) > ver_key(newest):
            report["decisions"].append(f"Adobe publishes isolated patches for a new release line, {version}. Needs a new line.")

    known = (EMERGENCY / "patches.json").read_text()
    for pid, e in sorted(entries.items()):
        m = ID.fullmatch(pid)
        if e["area"] == "CE" and m.group(2).startswith("VULN-") and m.group(2) not in known:
            hit = sorted(set(e["applies_to"]) & set(covered))
            if hit:
                report["decisions"].append(
                    f"Out-of-band {m.group(2)} ({e['file_name']}, sha256 {e['sha256']}, released {e['released']}) "
                    f"covers {', '.join(hit)} and is not in patches/emergency."
                )

    # Written together, last: a failure part way leaves the tree as it was.
    if not dry and pending:
        for path, raw in pending.items():
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(raw)
        manifest_path.write_text(json.dumps(manifest, indent=4) + "\n")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
