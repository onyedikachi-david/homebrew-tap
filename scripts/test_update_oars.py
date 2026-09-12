import hashlib
import io
import plistlib
import struct
import unittest
import zipfile

from update_oars import release_version, updated_cask, verify_archive


class ReleaseValidationTests(unittest.TestCase):
    def release(self, version="0.6.0"):
        return {"tag_name": f"v{version}", "draft": False, "prerelease": False,
                "assets": [{"name": name, "state": "uploaded"} for name in
                           (f"oars-v{version}-macos.zip", "SHA256SUMS")]}

    def archive(self, identity="app.getoars", cpu=0x0100000C, minimum="11.0"):
        output = io.BytesIO()
        bundle = "oars-0.6.0-macos-ReleaseFast.app/Contents/"
        with zipfile.ZipFile(output, "w") as package:
            package.writestr(bundle + "Info.plist", plistlib.dumps({
                "CFBundleIdentifier": identity, "CFBundleShortVersionString": "0.6.0",
                "CFBundleExecutable": "oars", "LSMinimumSystemVersion": minimum}))
            package.writestr(bundle + "MacOS/oars", b"\xcf\xfa\xed\xfe" + struct.pack("<I", cpu))
        archive = output.getvalue()
        digest = hashlib.sha256(archive).hexdigest()
        return archive, digest + "  oars-v0.6.0-macos.zip\n"

    def test_complete_stable_release_is_eligible(self):
        self.assertEqual(release_version(self.release(), "0.5.0"), "0.6.0")

    def test_waits_for_uploads_and_skips_prereleases(self):
        for field in ("draft", "prerelease"):
            release = self.release()
            release[field] = True
            self.assertIsNone(release_version(release, "0.5.0"))
        release = self.release()
        release["assets"].pop()
        self.assertIsNone(release_version(release, "0.5.0"))
        release = self.release()
        release["assets"][0]["state"] = "new"
        self.assertIsNone(release_version(release, "0.5.0"))

    def test_rejects_downgrade_and_invalid_tag(self):
        for version in ("0.4.0", "0.6.0-preview", '#{system("false")}'):
            with self.assertRaises(ValueError):
                release_version(self.release(version), "0.5.0")

    def test_accepts_verified_archive(self):
        archive, sums = self.archive()
        self.assertEqual(verify_archive("0.6.0", archive, sums), hashlib.sha256(archive).hexdigest())

    def test_rejects_corrupt_or_missing_checksum(self):
        archive, sums = self.archive()
        for content, checksums in ((archive + b"changed", sums), (archive, ""), (archive, sums + sums)):
            with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
                verify_archive("0.6.0", content, checksums)

    def test_rejects_changed_identity_or_platform(self):
        for options in ({"identity": "app.other"}, {"cpu": 0x01000007}, {"minimum": "15.0"}):
            archive, sums = self.archive(**options)
            with self.assertRaises(ValueError):
                verify_archive("0.6.0", archive, sums)

    def test_idempotence_and_replaced_release(self):
        current = '  version "0.5.0"\n  sha256 "' + "a" * 64 + '"\n'
        self.assertEqual(updated_cask(current, "0.5.0", "a" * 64), current)
        with self.assertRaisesRegex(ValueError, "manual review"):
            updated_cask(current, "0.5.0", "b" * 64)
        next_cask = updated_cask(current, "0.6.0", "b" * 64)
        self.assertIn('version "0.6.0"', next_cask)
        self.assertIn('sha256 "' + "b" * 64 + '"', next_cask)


if __name__ == "__main__":
    unittest.main()
