# FlowScroll Stable Release Checklist

This checklist defines the release gate for promoting FlowScroll from Beta to Stable.

## 1. Feature Freeze

- [ ] Freeze user-facing features for at least 2 weeks before the stable release.
- [ ] Accept only bug fixes, tests, documentation, packaging, and security changes.
- [ ] Require a regression test for every P0/P1 fix where automation is practical.
- [ ] Keep Windows as the stable target, macOS as supported, and Linux X11 as Preview.
- [ ] Do not claim Wayland support while global input hooks remain unavailable there.

## 2. Automated Gates

- [ ] `uv sync --frozen --extra dev` succeeds.
- [ ] `uv run python .github/scripts/check_version_consistency.py --expected vX.Y.Z` succeeds.
- [ ] `uv run pre-commit run --all-files` succeeds without skipped hooks.
- [ ] `uv run python -m pytest -q` succeeds.
- [ ] GitHub Actions test jobs succeed on Windows, macOS, and Ubuntu.
- [ ] CI packaging succeeds for `.exe`, `.dmg`, and `.AppImage` artifacts.
- [ ] `CHANGELOG.md` contains the exact release tag section.

## 3. Release Artifact Validation

Test downloaded workflow artifacts or release assets, not a source checkout.

### Windows

- [ ] Start normally and with `--silent`.
- [ ] Verify click-toggle, hold-to-scroll, and delayed middle-click modes.
- [ ] Verify a short delayed middle-click opens/closes browser tabs normally.
- [ ] Verify left/right click exits active scrolling without swallowing the click.
- [ ] Verify tray restore, preset switching, autostart, and clean exit.
- [ ] Run idle for at least 2 hours and active scrolling for at least 30 minutes.
- [ ] Record idle/active CPU usage and confirm input hooks remain responsive.
- [ ] Verify the executable signature with `Get-AuthenticodeSignature`.

### macOS

- [ ] Verify the app launches after installation from the DMG.
- [ ] Verify Accessibility permission onboarding and behavior after permission changes.
- [ ] Verify click-toggle, hold-to-scroll, tray/menu behavior, and launchd autostart.
- [ ] Restart macOS and confirm `--silent` autostart works.
- [ ] Verify Developer ID signing, notarization, and stapling with `codesign`, `spctl`, and `stapler`.

### Linux X11

- [ ] Launch the AppImage on at least one supported X11 distribution.
- [ ] Verify global mouse/keyboard hooks, tray behavior, scrolling, and autostart.
- [ ] Confirm Wayland sessions display the documented unsupported/degraded state.

## 4. Configuration And Upgrade Safety

- [ ] Upgrade from the previous two stable releases without losing presets.
- [ ] Verify malformed local config is backed up as `.invalid-*.bak` and replaced safely.
- [ ] Verify an unwritable custom config path is rejected without changing the active path.
- [ ] Verify WebDAV rejects malformed or unsafe remote configuration without partial updates.
- [ ] Verify WebDAV passwords never appear in the JSON config, logs, or sync payload.

## 5. Signing Prerequisites

Stable promotion is blocked until signing credentials are provisioned outside the repository.

- [ ] Windows code-signing certificate and private key are available to the release workflow.
- [ ] Apple Developer ID Application certificate is available to the release workflow.
- [ ] Apple notarization credentials are stored as GitHub Actions secrets.
- [ ] Workflow logs do not print certificate material, passwords, or notarization credentials.
- [ ] Unsigned artifacts are clearly marked as Beta/Preview and are not promoted as Stable.

## 6. Observation Window

- [ ] Publish the release as Beta or release candidate first.
- [ ] Observe it for 2-4 weeks without adding features.
- [ ] No unresolved P0/P1 regression remains.
- [ ] No repeatable startup, autostart, input-hook, config-loss, or runaway-CPU defect remains.
- [ ] All supported-platform issues have reproduction steps or an explicit documented limitation.

## 7. Stable Promotion

- [ ] Update the package classifier from `Development Status :: 4 - Beta` to Stable.
- [ ] Confirm README platform wording matches the tested support matrix.
- [ ] Create the signed tag only after all required checks pass.
- [ ] Download release assets and repeat signature/hash verification.
- [ ] Confirm the website download buttons point to the new release assets.

## 8. Rollback

- [ ] Keep the previous release assets available.
- [ ] If a P0/P1 regression is confirmed, stop promoting the affected release immediately.
- [ ] Document the affected versions and workaround in the release notes.
- [ ] Ship a patch release from the last known-good tag plus the minimal tested fix.
- [ ] Never rewrite or move an existing public release tag.
