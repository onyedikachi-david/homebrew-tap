# Homebrew tap

Install [Oars](https://getoars.app/) on macOS (Apple Silicon or Intel) or Linux x86_64:

```sh
brew install --cask onyedikachi-david/tap/oars
```

The cask selects the package for your operating system and CPU. On macOS it installs `Oars.app`. On Linux it adds the `oars` command and a user application-menu entry.

## Linux runtime

Oars needs a graphical desktop, GTK4, and WebKitGTK 6.0. On Ubuntu 24.04, install these system libraries before launching the app:

```sh
sudo apt install libgtk-4-1 libwebkitgtk-6.0-4
```

Ubuntu can also restrict the user namespaces that WebKitGTK needs for its sandbox. If `/proc/sys/kernel/apparmor_restrict_unprivileged_userns` contains `1`, load the Oars-specific profile supplied by this cask:

```sh
sudo install -m 644 ~/.local/share/oars/oars.apparmor /etc/apparmor.d/oars-homebrew
sudo apparmor_parser -r /etc/apparmor.d/oars-homebrew
```

This allows Oars to create its sandbox without disabling AppArmor or WebKit's sandbox globally. Then open Oars from your application menu or run `oars`. Installation and launch are tested on Ubuntu 24.04 x86_64. Other distributions need compatible system libraries. Linux ARM packages are not available.

Homebrew's `webkitgtk` formula currently uses GTK3, so it does not supply the WebKitGTK 6.0 library this app needs.

## macOS security

Oars is currently unsigned and not notarized. Homebrew preserves macOS security checks. If macOS blocks the app, follow [Apple's instructions for opening an unidentified app](https://support.apple.com/guide/mac-help/mh40616/mac).

## Update or remove

```sh
brew update
brew upgrade --cask onyedikachi-david/tap/oars
brew uninstall --cask onyedikachi-david/tap/oars
```

Uninstalling removes the app, command, and menu entry installed by this cask. It does not delete your Oars settings or server data. If you installed the system AppArmor profile above, remove it separately when you no longer need Oars:

```sh
sudo apparmor_parser -R /etc/apparmor.d/oars-homebrew
sudo rm /etc/apparmor.d/oars-homebrew
```

## Release updates

The **Update Oars** workflow checks the latest stable GitHub release hourly, at minute 17. It waits until all three versioned archives and `SHA256SUMS` are uploaded. Before changing the cask, it verifies every archive checksum, app identity, version, CPU architecture, and packaged frontend. It also checks the macOS minimum version and Linux menu entry. It refuses a downgrade or a changed archive for an existing version.

`templates/oars.rb` defines the installation rules. The updater renders the cask only after every package passes validation, so an incomplete release cannot leave some platforms on broken download links.

The workflow commits only `Casks/oars.rb`, using this repository's `GITHUB_TOKEN`. No cross-repository token or additional secret is needed. You can also run it from the Actions tab or with:

```sh
gh workflow run update-oars.yml --repo onyedikachi-david/homebrew-tap
```

Scheduled runs can be delayed by GitHub. GitHub disables schedules in public repositories after 60 days without repository activity; re-enable the workflow in Actions if this occurs. If the app's packaging or platform support changes, update the template and validation script together.

## Validation

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
brew audit --cask onyedikachi-david/tap/oars
brew style Casks/oars.rb
```

CI installs, launches, and removes the cask on Apple Silicon macOS, Intel macOS, and Ubuntu x86_64. Launch checks use a fresh data directory and require an app window and a webview-load event outside the source checkout.
