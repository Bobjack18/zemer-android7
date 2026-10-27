# Zemer for Android 7.1 (API 25)

Automated signed builds of [Zemer](https://github.com/zemerteam/zemer-app) for Android 7.1 devices
(minSdk 25), rebuilt whenever upstream `main` moves.

## How it works

`.github/workflows/build.yml` runs every 6 hours and on demand:

1. Resolves upstream `zemerteam/zemer-app` `main`.
2. Stops if `state.json` already records that commit (use **Run workflow → force** to rebuild anyway).
3. Clones upstream at that commit and applies [`patches/android-7.1.patch`](patches/android-7.1.patch) —
   the whole port: `minSdk 25`, core-library desugaring, and the `Build.VERSION` guards for
   PiP / notification channels / `java.nio.file` / Shizuku / dynamic color / audio focus.
4. Builds and signs the release APK, publishes it as release `build-<run>`.
5. Rewrites `api.json` (the update feed), `changelog.json` and `state.json` on `main`.

## In-app updates

The port's updater (`NightlyUpdates.API_URL`) points at
`https://raw.githubusercontent.com/Bobjack18/zemer-android7/main/api.json`, so a running install
checks on launch, downloads the APK named there automatically, verifies its size + SHA-256 against
`api.json`, and hands it to the configured installer (Settings → Updater: Native / Root / Shizuku).

The manifest's `sha` is the commit this APK was built from, and `runNumber` is the workflow run
number — an update is offered only when both the commit differs and the run number is newer, so a
stale mirror entry can never downgrade an install.

## Updating the port

Edit the app in a checkout of upstream, then regenerate the patch from that worktree:

```bash
git diff --ignore-space-at-eol -- . ':(exclude).github' ':(exclude)app/src/test/resources' \
  ':(exclude)cipher' > patches/android-7.1.patch
```

Commit it here — the next scheduled run (or a forced dispatch) picks it up.
