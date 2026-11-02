# Copyright (c) 2026 Sam James. Licensed under the Open Software License version 3.0.
# SPDX-License-Identifier: OSL-3.0
#
# bin/ingest-adobe-patches.py against a fixture registry, offline.
#
#   python3 -I -m unittest discover -s tests -p 'test_*.py'

import contextlib, hashlib, importlib.util, io, json, shutil, sys, tempfile, unittest, urllib.error, zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "bin" / "ingest-adobe-patches.py"
spec = importlib.util.spec_from_file_location("ingest", SCRIPT)
ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest)


def diff(*paths):
    return "".join(f"diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n@@ -1 +1 @@\n-a\n+b\n" for p in paths).encode()


JUL = diff("vendor/magento/module-a/A.php", "vendor/bin/patch-status")
AUG = diff("vendor/magento/module-b/B.php", "vendor/bin/patch-status")
SEP = diff("vendor/magento/module-c/C.php", "vendor/magento/module-email/Preview.php", "pub/index.php")
VULN = diff("vendor/magento/module-email/Preview.php")


class IngestTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        iso, emg = self.root / "patches" / "isolated", self.root / "patches" / "emergency"
        for month, raw in (("2026-07-001", JUL), ("2026-08-001", AUG)):
            (iso / month).mkdir(parents=True)
            (iso / month / "2.4.9-CE.patch").write_bytes(raw)
        (iso / "patches.json").write_text(json.dumps({"lines": {"2.4.9": {
            "base": {"magento/magento2-base": "2.4.9"}, "cumulative": True,
            "patches": [self.entry("2026-07-001"), self.entry("2026-08-001")],
        }}}))
        (emg / "VULN-39341").mkdir(parents=True)
        (emg / "VULN-39341" / "2.4.9.patch").write_bytes(VULN)
        (emg / "patches.json").write_text(json.dumps({"patches": [], "lines": {"2.4.9": {
            "base": {"magento/magento2-base": "2.4.9"},
            "patches": [{"id": "APSB26-146", "source": "VULN-39341/2.4.9.patch"}],
        }}}))

        self.registry, self.files = {}, {}
        self.add("249-2026-07-001-CE", JUL, released="2026-07-14")
        self.add("249-2026-08-001-CE", AUG, released="2026-08-11", requires=["249-2026-07-001-CE"])
        self.add("249-VULN-39341-CE", VULN, released="2026-09-07")

        for name, value in (("ROOT", self.root), ("ISOLATED", iso), ("EMERGENCY", emg), ("get", self.get)):
            original = getattr(ingest, name)
            setattr(ingest, name, value)
            self.addCleanup(setattr, ingest, name, original)

    @staticmethod
    def entry(month):
        return {"id": month, "source": f"{month}/2.4.9-CE.patch", "label": ingest.label(month), "description": ingest.description(month)}

    def add(self, pid, raw, released="2026-09-08", requires=(), applies_to=("2.4.9",), area="CE", **extra):
        file_name = f"{pid}.diff"
        self.registry[pid] = {
            "applies_to": list(applies_to), "area": area, "requires": list(requires), "cves": ["CVE-2026-1"],
            "released": released, "file_name": file_name, "sha256": hashlib.sha256(raw).hexdigest(), **extra,
        }
        self.files[file_name] = raw
        return self.registry[pid]

    def get(self, url):
        if url == ingest.REGISTRY:
            return json.dumps({"patches": self.registry}).encode()
        found = self.files.get(url.removeprefix(ingest.PATCH_URL))
        if isinstance(found, int) or found is None:
            raise urllib.error.HTTPError(url, found or 404, "fixture", {}, io.BytesIO())
        return found

    def run_ingest(self, *args):
        out = io.StringIO()
        argv = sys.argv
        sys.argv = ["ingest", *args]
        try:
            with contextlib.redirect_stdout(out):
                ingest.main()
        finally:
            sys.argv = argv
        return json.loads(out.getvalue())

    def manifest(self):
        return json.loads((self.root / "patches/isolated/patches.json").read_text())["lines"]["2.4.9"]["patches"]

    def september(self, **kw):
        kw.setdefault("requires", ["249-2026-07-001-CE", "249-2026-08-001-CE"])
        return self.add("249-2026-09-001-CE", SEP, **kw)

    # Nothing to do

    def test_nothing_new(self):
        report = self.run_ingest()
        self.assertEqual(report, {"dry_run": False, "added": [], "decisions": [], "malformed_registry_entries": []})

    # Adding a month

    def test_adds_a_month_unmodified(self):
        self.september()
        report = self.run_ingest()
        self.assertEqual([a["registry_id"] for a in report["added"]], ["249-2026-09-001-CE"])
        self.assertEqual((self.root / "patches/isolated/2026-09-001/2.4.9-CE.patch").read_bytes(), SEP)
        self.assertEqual(self.manifest()[-1], {
            "id": "2026-09-001", "source": "2026-09-001/2.4.9-CE.patch",
            "label": "September Isolated", "description": "Adobe isolated security patch for September 2026 (Community Edition).",
        })
        self.assertEqual(report["decisions"], [])

    def test_accepts_requires_naming_only_the_month_before(self):
        self.september(requires=["249-2026-08-001-CE"])
        self.assertEqual(len(self.run_ingest()["added"]), 1)

    def test_adds_several_months_in_order(self):
        self.september()
        self.add("249-2026-10-001-CE", diff("vendor/magento/module-d/D.php"), released="2026-10-13",
                 requires=["249-2026-07-001-CE", "249-2026-08-001-CE", "249-2026-09-001-CE"])
        self.add("249-2026-10-002-CE", diff("vendor/magento/module-e/E.php"), released="2026-10-13",
                 requires=["249-2026-07-001-CE", "249-2026-08-001-CE", "249-2026-09-001-CE", "249-2026-10-001-CE"])
        self.run_ingest()
        self.assertEqual([p["id"] for p in self.manifest()], ["2026-07-001", "2026-08-001", "2026-09-001", "2026-10-001", "2026-10-002"])
        self.assertEqual(self.manifest()[-1]["label"], "October Isolated 2")

    def test_reports_what_a_month_touches(self):
        self.september()
        added = self.run_ingest()["added"][0]
        self.assertEqual(added["rewrites_earlier_months"], [])
        self.assertEqual(added["overlaps_emergency_patches"], ["vendor/magento/module-email/Preview.php"])
        self.assertEqual(added["root_or_vendor_bin"], ["pub/index.php"])

    def test_reports_rewrites_of_earlier_months(self):
        self.september()
        self.files["249-2026-09-001-CE.diff"] = raw = diff("vendor/bin/patch-status")
        self.registry["249-2026-09-001-CE"]["sha256"] = hashlib.sha256(raw).hexdigest()
        self.assertEqual(self.run_ingest()["added"][0]["rewrites_earlier_months"], ["vendor/bin/patch-status"])

    def test_falls_back_to_the_monthly_zip(self):
        self.september()
        del self.files["249-2026-09-001-CE.diff"]
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, "w") as z:
            z.writestr("2.4.9/249-2026-09-001-CE.patch", SEP)
        self.files["2-4-9-sep-2026.zip"] = bundle.getvalue()
        self.assertEqual(len(self.run_ingest()["added"]), 1)
        self.assertEqual((self.root / "patches/isolated/2026-09-001/2.4.9-CE.patch").read_bytes(), SEP)

    def test_missing_zip_is_a_decision(self):
        self.september()
        del self.files["249-2026-09-001-CE.diff"]
        report = self.run_ingest()
        self.assertEqual(report["added"], [])
        self.assertEqual(report["decisions"], ["249-2026-09-001-CE.diff: HTTP 404 from repo.magento.com. Not added."])

    def test_zip_without_the_file_fails(self):
        self.september()
        del self.files["249-2026-09-001-CE.diff"]
        bundle = io.BytesIO()
        with zipfile.ZipFile(bundle, "w") as z:
            z.writestr("2.4.9/something-else.patch", SEP)
        self.files["2-4-9-sep-2026.zip"] = bundle.getvalue()
        with self.assertRaisesRegex(RuntimeError, "is not at its URL or in 2-4-9-sep-2026.zip"):
            self.run_ingest()

    def test_dry_run_writes_nothing(self):
        self.september()
        before = (self.root / "patches/isolated/patches.json").read_text()
        report = self.run_ingest("--dry-run")
        self.assertEqual(len(report["added"]), 1)
        self.assertEqual((self.root / "patches/isolated/patches.json").read_text(), before)
        self.assertFalse((self.root / "patches/isolated/2026-09-001").exists())

    def test_ignores_other_areas(self):
        self.add("249-2026-09-001-EE", b"commerce", requires=["249-2026-07-001-CE", "249-2026-08-001-CE"], area="EE")
        self.assertEqual(self.run_ingest()["added"], [])
        self.registry["249-2026-09-001-EE"]["area"] = "CE"
        self.assertEqual(len(self.run_ingest("--dry-run")["added"]), 1, "control: the same entry as CE is added")

    # Stops for a decision

    def test_requires_mismatch_stops_the_line(self):
        self.september(requires=["249-2026-07-001-CE"])
        self.add("249-2026-10-001-CE", diff("x"), released="2026-10-13", requires=["249-2026-09-001-CE"])
        report = self.run_ingest()
        self.assertEqual(report["added"], [])
        self.assertEqual(len(report["decisions"]), 1)
        self.assertTrue(report["decisions"][0].startswith("249-2026-09-001-CE requires"))

    def test_gated_month_stops_the_line(self):
        self.september(entitlements=["ee"])
        self.files["249-2026-09-001-CE.diff"] = 401
        self.add("249-2026-10-001-CE", diff("x"), released="2026-10-13",
                 requires=["249-2026-07-001-CE", "249-2026-08-001-CE", "249-2026-09-001-CE"])
        report = self.run_ingest()
        self.assertEqual(report["added"], [])
        self.assertEqual(report["decisions"], [
            "249-2026-09-001-CE.diff: HTTP 401 from repo.magento.com. Adobe gates it to Commerce customers (entitlement 'ee'). Not added.",
        ])

    def test_commerce_only_but_downloadable_is_added_and_reported(self):
        self.september(entitlements=["ee"])
        report = self.run_ingest()
        self.assertEqual(len(report["added"]), 1)
        self.assertEqual(report["decisions"], ["249-2026-09-001-CE: Adobe lists 2.4.9 as Commerce-only (entitlement 'ee') from 2026-09-001."])

    def test_never_overwrites_a_different_file(self):
        self.september()
        (self.root / "patches/isolated/2026-09-001").mkdir()
        (self.root / "patches/isolated/2026-09-001/2.4.9-CE.patch").write_bytes(b"edited")
        report = self.run_ingest()
        self.assertEqual(report["added"], [])
        self.assertIn("exists with different content", report["decisions"][0])
        self.assertEqual((self.root / "patches/isolated/2026-09-001/2.4.9-CE.patch").read_bytes(), b"edited")

    def test_new_patch_level_needs_a_line(self):
        self.add("249p1-2026-09-001-CE", SEP, applies_to=["2.4.9-p1"])
        self.assertIn("Adobe now publishes isolated patches for 2.4.9-p1, newer than the 2.4.9 line. Needs a new line.",
                      self.run_ingest()["decisions"])

    def test_new_release_line_needs_a_line(self):
        self.add("251-2026-09-001-CE", SEP, applies_to=["2.5.1"])
        self.assertIn("Adobe publishes isolated patches for a new release line, 2.5.1. Needs a new line.",
                      self.run_ingest()["decisions"])

    def test_older_patch_level_is_not_reported(self):
        self.add("248p5-2026-09-001-CE", SEP, applies_to=["2.4.8-p5"])
        self.assertEqual(self.run_ingest()["decisions"], [])

    def test_unknown_hotfix_is_reported(self):
        self.add("249-VULN-40000-CE", VULN)
        decisions = self.run_ingest()["decisions"]
        self.assertEqual(len(decisions), 1)
        self.assertTrue(decisions[0].startswith("Out-of-band VULN-40000 ("))

    def test_hotfix_whose_id_is_a_prefix_of_a_known_one_is_reported(self):
        self.add("249-VULN-3934-CE", VULN)
        self.assertEqual(len(self.run_ingest()["decisions"]), 1)

    def test_hotfix_for_an_uncovered_version_is_not_reported(self):
        self.add("247p5-VULN-40000-CE", VULN, applies_to=["2.4.7-p5"])
        self.assertEqual(self.run_ingest()["decisions"], [])

    # Bad input

    def test_sha256_mismatch_fails_and_writes_nothing(self):
        self.september()
        self.files["249-2026-09-001-CE.diff"] = b"tampered"
        before = (self.root / "patches/isolated/patches.json").read_text()
        with self.assertRaisesRegex(RuntimeError, "sha256 mismatch"):
            self.run_ingest()
        self.assertEqual((self.root / "patches/isolated/patches.json").read_text(), before)
        self.assertFalse((self.root / "patches/isolated/2026-09-001").exists())

    def test_malformed_entries_are_named_and_ignored(self):
        bad = {
            "249-2026-09-001-CE": {"sha256": "not-a-sha"},
            "249-2026-10-001-CE": {"released": "2026-99-99"},
            "249-2026-13-001-CE": {},
            "249-2026-11-001-CE": {"file_name": "../../etc/passwd"},
            "249-2026-12-001-CE": {"applies_to": ["2.4.9; rm -rf /"]},
        }
        for pid, override in bad.items():
            self.add(pid, SEP).update(override)
        self.registry["../evil"] = dict(self.registry["249-2026-08-001-CE"])
        report = self.run_ingest()
        self.assertEqual(sorted(report["malformed_registry_entries"]), sorted([*bad, "<malformed id>"]))
        self.assertEqual(report["added"], [])
        self.assertEqual(report["decisions"], [])

    # Manifest shapes

    def test_line_with_no_patches_yet(self):
        path = self.root / "patches/isolated/patches.json"
        data = json.loads(path.read_text())
        data["lines"]["2.4.9-p1"] = {"base": {"magento/magento2-base": "2.4.9-p1"}, "cumulative": True, "patches": []}
        path.write_text(json.dumps(data))
        self.add("249p1-2026-09-001-CE", SEP, applies_to=["2.4.9-p1"], requires=["249p1-2026-08-001-CE"])
        report = self.run_ingest()
        self.assertEqual(report["added"], [])
        self.assertTrue(report["decisions"][0].startswith("249p1-2026-09-001-CE requires"))

    def move_hotfix_into_chain(self):
        iso, emg = self.root / "patches/isolated/patches.json", self.root / "patches/emergency/patches.json"
        data = json.loads(iso.read_text())
        data["lines"]["2.4.9"]["patches"].append({"id": "APSB26-146", "source": "../emergency/VULN-39341/2.4.9.patch"})
        iso.write_text(json.dumps(data))
        data = json.loads(emg.read_text())
        data["lines"]["2.4.9"]["patches"] = []
        emg.write_text(json.dumps(data))

    def test_month_after_a_hotfix_moved_into_the_chain_is_added(self):
        self.move_hotfix_into_chain()
        self.september()
        report = self.run_ingest()
        self.assertEqual([a["id"] for a in report["added"]], ["2026-09-001"])
        self.assertEqual(report["decisions"], [], "the moved hotfix still counts as known")
        self.assertEqual([p["id"] for p in self.manifest()], ["2026-07-001", "2026-08-001", "APSB26-146", "2026-09-001"])

    def test_month_requiring_a_hotfix_stops_for_a_decision(self):
        self.move_hotfix_into_chain()
        self.september(requires=["249-2026-07-001-CE", "249-2026-08-001-CE", "249-VULN-39341-CE"])
        report = self.run_ingest()
        self.assertEqual(report["added"], [])
        self.assertEqual(report["decisions"], [
            "249-2026-09-001-CE requires ['249-2026-07-001-CE', '249-2026-08-001-CE', '249-VULN-39341-CE'], "
            "but the 2.4.9 chain ends at 2026-08-001 (249-2026-08-001-CE). Not added.",
        ])


if __name__ == "__main__":
    unittest.main()
