# Installing the u1kit GUI

Releases are built on tag via GitHub Actions and published as unsigned
bundles for Windows, macOS, and Linux. Signing and notarization are
deferred to Phase 4 — these MVP bundles will trip the "unknown
publisher" warnings on every OS. The workarounds below are one-time.

## Windows

1. Download `u1kit-x86_64-pc-windows-msvc` from the release page — it
   contains `u1kit_0.1.0_x64_en-US.msi`.
2. Run the MSI. SmartScreen may block it: click **More info** →
   **Run anyway**.
3. The installer places the app in `%LocalAppData%\Programs\u1kit`.
4. Uninstall via Settings → Apps.

## macOS

1. Download the artifact for your architecture (`aarch64-apple-darwin`
   for Apple Silicon; add `x86_64-apple-darwin` when released).
2. Open the `.dmg`, drag `u1kit.app` to `/Applications`.
3. First launch: **right-click** `u1kit.app` → **Open** (a plain
   double-click shows "can't be opened because Apple cannot check it
   for malicious software" — Gatekeeper blocking unsigned apps). The
   right-click-Open path shows a confirmation dialog; accept it once.
   Subsequent launches work normally.
4. Uninstall: drag from `/Applications` to Trash.

## Linux

Two formats are produced — pick whichever your distro handles better.

### AppImage (universal)

```bash
chmod +x u1kit-*.AppImage
./u1kit-*.AppImage
```

The AppImage is self-contained; it does not install anywhere. You may
want to put it in `~/.local/bin` or a desktop-entry file.

### Debian package

```bash
sudo apt install ./u1kit_0.1.0_amd64.deb
```

Installs to `/usr/bin/u1kit` and adds a desktop entry. Uninstall with
`sudo apt remove u1kit`.

## Minimum OS versions

- Windows 10 1809 (Build 17763) or later.
- macOS 12 Monterey or later.
- Linux glibc 2.31+ (Ubuntu 20.04 equivalent).

These match Tauri 2 defaults (DECISIONS item 37).

## Building from source

Requires Rust 1.75+, Node 22+, pnpm 10+, and Python 3.10+.

```bash
# One-off: build the sidecar binary
pip install -e ".[release]"
python scripts/build_sidecar.py
cp dist/sidecar/<target-triple>/u1kit* gui/src-tauri/resources/sidecar/

# Then build the GUI
cd gui
pnpm install
pnpm tauri build
```

The resulting bundle lands in `gui/src-tauri/target/release/bundle/`.
