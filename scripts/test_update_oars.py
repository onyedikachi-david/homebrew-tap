import hashlib
import io
import plistlib
import struct
import tarfile
import unittest
import zipfile

from update_oars import ASSETS, release_version, render_cask, updated_cask, verify_archive


class ReleaseValidationTests(unittest.TestCase):
    def release(self, version="0.6.0"):
        return {"tag_name": f"v{version}", "draft": False, "prerelease": False,
                "assets": [{"name": name, "state": "uploaded"} for name in
                           [f"oars-v{version}-{suffix}" for suffix in ASSETS.values()] + ["SHA256SUMS"]]}

    def archive(self, platform, identity="app.getoars", wrong_cpu=False, minimum="11.0", frontend=True):
        output = io.BytesIO()
        if platform.startswith("macos_"):
            bundle = "oars-0.6.0-macos-ReleaseFast.app/Contents/"
            with zipfile.ZipFile(output, "w") as package:
                package.writestr(bundle + "Info.plist", plistlib.dumps({
                    "CFBundleIdentifier": identity, "CFBundleShortVersionString": "0.6.0",
                    "CFBundleExecutable": "oars", "LSMinimumSystemVersion": minimum}))
                cpu = 0x0100000C if platform == "macos_arm64" else 0x01000007
                package.writestr(bundle + "MacOS/oars", b"\xcf\xfa\xed\xfe" + struct.pack("<I", 0 if wrong_cpu else cpu))
                package.writestr(bundle + "Resources/frontend/dist/index.html", b"app" if frontend else b"")
        else:
            executable = bytearray(20)
            executable[:6] = b"\x7fELF\x02\x01"
            struct.pack_into("<H", executable, 18, 183 if wrong_cpu else 62)
            files = {"bin/oars": bytes(executable),
                     "package-manifest.zon": f'.{{ .version = "0.6.0", .app_id = "{identity}", .target = "linux", .executable = "oars" }}'.encode(),
                     "share/applications/oars.desktop": b'Exec="oars"\nIcon=app-icon\n',
                     "share/icons/hicolor/256x256/apps/app-icon.png": b"icon",
                     "resources/frontend/dist/index.html": b"app" if frontend else b""}
            with tarfile.open(fileobj=output, mode="w:gz") as package:
                for name, data in files.items():
                    member = tarfile.TarInfo("./oars-0.6.0-linux-ReleaseFast/" + name)
                    member.size = len(data)
                    package.addfile(member, io.BytesIO(data))
        archive = output.getvalue()
        digest = hashlib.sha256(archive).hexdigest()
        return archive, digest + f"  oars-v0.6.0-{ASSETS[platform]}\n"

    def test_complete_stable_release_is_eligible(self):
        self.assertEqual(release_version(self.release(), "0.5.0"), "0.6.0")

    def test_waits_for_every_platform_and_checksum(self):
        for index in range(4):
            release = self.release()
            release["assets"].pop(index)
            self.assertIsNone(release_version(release, "0.5.0"))
            release = self.release()
            release["assets"][index]["state"] = "new"
            self.assertIsNone(release_version(release, "0.5.0"))

    def test_skips_drafts_and_prereleases(self):
        for field in ("draft", "prerelease"):
            release = self.release()
            release[field] = True
            self.assertIsNone(release_version(release, "0.5.0"))

    def test_rejects_downgrade_and_invalid_tag(self):
        for version in ("0.4.0", "0.6.0-preview", '#{system("false")}'):
            with self.assertRaises(ValueError):
                release_version(self.release(version), "0.5.0")

    def test_accepts_verified_archives(self):
        for platform in ASSETS:
            with self.subTest(platform=platform):
                archive, sums = self.archive(platform)
                self.assertEqual(verify_archive("0.6.0", platform, archive, sums), hashlib.sha256(archive).hexdigest())

    def test_rejects_corrupt_missing_or_duplicate_checksum(self):
        for platform in ASSETS:
            archive, sums = self.archive(platform)
            for content, checksums in ((archive + b"changed", sums), (archive, ""), (archive, sums + sums)):
                with self.assertRaisesRegex(ValueError, "SHA256SUMS"):
                    verify_archive("0.6.0", platform, content, checksums)

    def test_rejects_changed_identity_architecture_or_missing_frontend(self):
        for platform in ASSETS:
            for options in ({"identity": "app.other"}, {"wrong_cpu": True}, {"frontend": False}):
                archive, sums = self.archive(platform, **options)
                with self.assertRaises(ValueError):
                    verify_archive("0.6.0", platform, archive, sums)
        for platform in ("macos_arm64", "macos_x86_64"):
            archive, sums = self.archive(platform, minimum="15.0")
            with self.assertRaisesRegex(ValueError, "macOS requirement"):
                verify_archive("0.6.0", platform, archive, sums)

    def test_idempotence_and_replaced_release_on_each_platform(self):
        digests = {platform: str(index) * 64 for index, platform in enumerate(ASSETS)}
        current = render_cask("0.5.0", digests)
        self.assertEqual(updated_cask(current, "0.5.0", digests), current)
        for platform in ASSETS:
            with self.assertRaisesRegex(ValueError, "manual review"):
                updated_cask(current, "0.5.0", dict(digests, **{platform: "a" * 64}))
        self.assertIn('version "0.6.0"', updated_cask(current, "0.6.0", digests))
        with self.assertRaisesRegex(ValueError, "All three"):
            render_cask("0.6.0", {"macos_arm64": "a" * 64})


if __name__ == "__main__":
    unittest.main()
