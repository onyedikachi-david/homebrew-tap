cask "oars" do
  version "0.5.0"
  sha256 "d3336ef398a8d0f9a7f0ecc94822916f98e2dd0545508bc6aa2ce1c2b247fa3b"

  url "https://github.com/onyedikachi-david/oars/releases/download/v#{version}/oars-v#{version}-macos.zip"
  name "Oars"
  desc "Server management over SSH"
  homepage "https://getoars.app/"

  depends_on arch: :arm64
  depends_on macos: :big_sur

  app "oars-#{version}-macos-ReleaseFast.app", target: "Oars.app"

  caveats <<~EOS
    Oars is currently unsigned and not notarized.
    If macOS blocks it, follow Apple's instructions for opening an app
    from an unidentified developer:
      https://support.apple.com/guide/mac-help/mh40616/mac
  EOS
end
