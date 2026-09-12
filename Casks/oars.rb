cask "oars" do
  arch arm: "macos", intel: "macos-x86_64"

  version "0.6.0"
  sha256 arm:          "c9693b2aeaaeaba55f417a6a81a7556aed6dbc2392ea3909e2e12f731cb67e6a",
         intel:        "11517fdb8eca813ebef08a953731442c2a9a464cd25dc896fb410b3871e3213a",
         x86_64_linux: "f4b7815af02f2139463c9d4c2a90cc12f74c4daa194e0110c387bb3be0fd217b"

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
