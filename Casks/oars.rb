cask "oars" do
  arch arm: "macos", intel: "macos-x86_64"

  version "0.8.0"
  sha256 arm:          "c6571269f0bdefffcdd82e174f77c7fb7344307ed18dbd93c953e23b2fbbecd4",
         intel:        "01cec6770daeb582843d48e3f0ad23b56a3500b5ddc22748266ac4c25515a312",
         x86_64_linux: "81551cbd5a110ef48e51164949e5498ce9c1889dbc5652a2a332f7cd5e8984cc"

  on_macos do
    url "https://github.com/onyedikachi-david/oars/releases/download/v#{version}/oars-v#{version}-#{arch}.zip"

    depends_on macos: :big_sur

    app "oars-#{version}-macos-ReleaseFast.app", target: "Oars.app"

    caveats <<~EOS
      Oars is currently unsigned and not notarized.
      If macOS blocks it, follow Apple's instructions for opening an app
      from an unidentified developer:
        https://support.apple.com/guide/mac-help/mh40616/mac
    EOS
  end
  on_linux do
    url "https://github.com/onyedikachi-david/oars/releases/download/v#{version}/oars-v#{version}-linux-x86_64.tar.gz"

    depends_on arch: :x86_64

    binary "oars-#{version}-linux-ReleaseFast/bin/oars"
    artifact "oars-#{version}-linux-ReleaseFast/share/applications/oars.desktop",
             target: "~/.local/share/applications/app.getoars.desktop"
    artifact "oars-#{version}-linux-ReleaseFast/share/icons/hicolor/256x256/apps/app-icon.png",
             target: "~/.local/share/icons/hicolor/256x256/apps/app.getoars.png"
    artifact "oars.apparmor", target: "~/.local/share/oars/oars.apparmor"

    preflight_steps do
      write_file "oars.apparmor", <<~EOS
        abi <abi/4.0>,
        include <tunables/global>
        profile oars-homebrew "{{HOMEBREW_PREFIX}}/Caskroom/oars/*/oars-*-linux-ReleaseFast/bin/oars" flags=(unconfined) {
          userns,
        }
      EOS
      inreplace "oars-#{version}-linux-ReleaseFast/share/applications/oars.desktop",
                'Exec="oars"', 'Exec="{{HOMEBREW_PREFIX}}/bin/oars"'
      inreplace "oars-#{version}-linux-ReleaseFast/share/applications/oars.desktop",
                "Icon=app-icon", "Icon=app.getoars"
    end

    caveats <<~EOS
      Oars requires a graphical desktop, GTK4, and WebKitGTK 6.0.
      On Ubuntu 24.04, install the runtime libraries:
        sudo apt install libgtk-4-1 libwebkitgtk-6.0-4
      If AppArmor restricts unprivileged user namespaces, install the Oars profile:
        sudo install -m 644 ~/.local/share/oars/oars.apparmor /etc/apparmor.d/oars-homebrew
        sudo apparmor_parser -r /etc/apparmor.d/oars-homebrew
      Then launch Oars from the application menu or run:
        oars
      Other Linux distributions need compatible system libraries.
    EOS
  end

  name "Oars"
  desc "Server management over SSH"
  homepage "https://getoars.app/"
end
