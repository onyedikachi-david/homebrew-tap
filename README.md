# Homebrew tap

Install [Oars](https://getoars.app/) on an Apple Silicon Mac:

```sh
brew install --cask onyedikachi-david/tap/oars
```

This installs the released app as `Oars.app`. Intel Macs and Linux are not supported by this cask. Linux packages are available from the [Oars releases](https://github.com/onyedikachi-david/oars/releases).

Oars is currently unsigned and not notarized. Homebrew preserves macOS security checks. If macOS blocks the app, follow [Apple's instructions for opening an unidentified app](https://support.apple.com/guide/mac-help/mh40616/mac).

To update or remove the app:

```sh
brew update
brew upgrade --cask onyedikachi-david/tap/oars
brew uninstall --cask onyedikachi-david/tap/oars
```

Uninstalling the cask does not delete your Oars settings or server data.

## Release updates

The **Update Oars** workflow checks the latest stable GitHub release hourly, at minute 17. It waits until the versioned macOS ZIP and `SHA256SUMS` are uploaded. Before changing the cask, it verifies the archive checksum, app identity, version, architecture, and minimum macOS version. It refuses a downgrade or a changed archive for an existing version.

The workflow commits only `Casks/oars.rb`, using this repository's `GITHUB_TOKEN`. No cross-repository token or additional secret is needed. You can also run it from the Actions tab or with:

```sh
gh workflow run update-oars.yml --repo onyedikachi-david/homebrew-tap
```

Scheduled runs can be delayed by GitHub. GitHub disables schedules in public repositories after 60 days without repository activity; re-enable the workflow in Actions if this occurs. If the app's packaging or platform support changes, update the cask and validation script together.

## Validation

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
brew audit --cask onyedikachi-david/tap/oars
brew style Casks/oars.rb
```
