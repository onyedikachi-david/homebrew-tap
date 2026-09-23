cask "oars" do
  arch arm: "macos", intel: "macos-x86_64"

  version "0.7.0"
  sha256 arm:          "418bb8c66fa04d1cdd1c997d7961a10856a7e613a66b2a27e6007cfb2a55c41e",
         intel:        "2c37b5e4b22930d7a58674db48ae967038f51796108ee3c5ff147bc645e677b2",
         x86_64_linux: "a239dd0da6f3d91c7743d5c869321d7772ad6d055bd3ae0e12048a46343b7895"

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
