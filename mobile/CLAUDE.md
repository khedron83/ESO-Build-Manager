# ESO Build Manager (Expo/Android)

React Native + Expo companion app for eso-build-manager. Read/edit builds on
Android, two-way sync to the same Nextcloud `ESO-Builds/` WebDAV folder the
desktop app uses. Also browses character data (bio/stats/dailies/inventory/
bank/champion points) synced read-only from `ESO-Characters/`.

## Project Layout

```
src/
├── screens/
│   ├── BuildsScreen.tsx        # List + search/filter + sync button + FAB
│   ├── BuildDetailScreen.tsx
│   ├── BuildEditorScreen.tsx
│   ├── SettingsScreen.tsx      # Nextcloud url/username/password
│   ├── CharactersScreen.tsx        # List + search/account-filter + sync button
│   └── CharacterDetailScreen.tsx   # Bio/Dailies/Stats/Currencies/CP/Inventory, sectioned
├── hooks/
│   ├── useBuilds.ts            # Local React state over storage.ts, call refresh() after any out-of-band storage write
│   ├── useSettings.ts
│   └── useCharacters.ts        # Same refresh()-after-sync caveat as useBuilds
├── utils/
│   ├── storage.ts              # AsyncStorage CRUD, same JSON shape as desktop's export_build_dict
│   ├── sync.ts                 # WebDAV GET/PUT against Nextcloud + manifest file (no PROPFIND/MKCOL, see below)
│   ├── skillData.ts
│   ├── md5.ts
│   ├── characterStorage.ts     # AsyncStorage, replace-all (not per-record merge like builds)
│   └── characterSync.ts        # Read-only GET against ESO-Characters/, see below
└── data/constants.ts
```

## Sync (`utils/sync.ts`)

Mirrors `eso-build-manager/eso_build_manager/sync/nextcloud.py` conceptually (same
`ESO-Builds/{slug}.json` layout, same `_sync_updated_at` conflict field), but **cannot use
PROPFIND or MKCOL** — Android's native `HttpURLConnection` has a hardcoded method whitelist
(`GET/POST/PUT/DELETE/HEAD/OPTIONS/TRACE/PATCH`) that doesn't include WebDAV verbs. Any
attempt throws before a `Response` even comes back, landing in a generic `catch` block that's
easy to misdiagnose as a server/auth/TLS problem (spent a whole debugging round on this
before finding the actual cause). This is a hard platform limitation, not fixable by fetch
options/headers/body — confirmed via Android's own `HttpURLConnection` source restrictions.

Instead, directory contents are tracked via a manifest file, `ESO-Builds/_index.json`
(`{filename: updatedAt}`), read/written with plain GET/PUT. The desktop app's real-PROPFIND
`list_remote_builds()` will see `_index.json` too, but it has no `"name"` key so desktop's
`if not remote_name: continue` check skips it harmlessly — no schema change needed on the
desktop side. If a device syncs to a brand-new `ESO-Builds/` folder that's never been created
(no MKCOL available), the first PUT will fail — in practice this hasn't mattered since the
desktop app (which does support MKCOL via `requests`) always creates the folder first.

**`useBuilds()` doesn't know when storage changes underneath it.** It loads once on mount;
anything that writes to `storage.ts` outside the hook's own `saveBuild`/`deleteBuild`/
`importBuild` wrappers (sync being the main case) must call `refresh()` afterward or the
screen silently shows stale data despite storage being correct. `BuildsScreen.handleSync`
does this after `sync()` resolves.

## Character sync (`utils/characterSync.ts`)

Read-only: character data always originates from the game addon (WornGear) via the desktop
app, never edited on mobile, so this is GET-only against `ESO-Characters/{slug}.json` +
`ESO-Characters/_index.json` — no upload, no merge, no conflict handling. Desktop's
`sync_characters()` (`eso_build_manager/sync/nextcloud.py`) writes the manifest and does a
full `dataclasses.asdict(Character)` dump per character, so the mobile `Character` type
(`src/types/index.ts`) intentionally keeps desktop's snake_case field names verbatim instead
of a camelCase mapping layer like `Build` has — there's no round-trip to keep in sync for a
read-only path, so the mapping layer would be pure overhead.

`characterStorage.ts` replaces the entire local cache on every sync (`replaceAllCharacters`)
rather than merging individual records — desktop always has the freshest full snapshot, so
there's nothing to merge.

## TODOs

### Server URL vs. Tailscale cert hostname mismatch
User's Nextcloud is reached over Tailscale; the TLS cert (Let's Encrypt via Tailscale HTTPS
certs) is issued for `server.vimba-luma.ts.net`, not the LAN IP `192.168.0.150`. Hitting it
by IP fails hostname verification even though the cert chain is trusted — looks identical to
a self-signed-cert failure (same generic sync error) but isn't one; no code fix, just use the
Tailscale hostname as the Server URL in Settings.

Complication: user sometimes has a different VPN active, which may not route/resolve the
`.ts.net` MagicDNS name. Need either:
- Split-DNS / hosts entry so the hostname resolves to the LAN IP when off Tailscale, or
- A fallback Server URL (Settings could hold both a Tailscale and a LAN-IP entry, tried in
  order) — but LAN IP will always fail cert verification, so this only helps if paired with
  the cert-pinning approach discussed below, or accepting sync just doesn't work off-Tailscale/VPN.

Not building anything here without the user picking a direction — see conversation for the
three options considered (cert pinning via bundled cert, true `verify=False`-style bypass via
native EAS build, or just requiring Tailscale to be connected).
