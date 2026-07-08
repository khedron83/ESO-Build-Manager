import type { Character, ServerConfig } from '../types';
import { replaceAllCharacters } from './characterStorage';

// Read-only: character data always originates from the desktop app (synced
// from the game addon), so this only ever downloads -- no upload, no merge.
// Same GET-only constraint as utils/sync.ts (no PROPFIND/MKCOL on Android),
// so the desktop side maintains an _index.json manifest we just GET.
const MANIFEST_NAME = '_index.json';

async function davRequest(config: ServerConfig, path: string): Promise<Response> {
  const url = config.url.replace(/\/$/, '') + '/remote.php/dav/files/' + config.username + '/ESO-Characters/' + path;
  const creds = btoa(`${config.username}:${config.password}`);
  return fetch(url, { method: 'GET', headers: { Authorization: `Basic ${creds}` } });
}

export interface CharacterSyncResult {
  downloaded: number;
  errors: string[];
}

export async function syncCharacters(config: ServerConfig): Promise<CharacterSyncResult> {
  const result: CharacterSyncResult = { downloaded: 0, errors: [] };

  let manifest: Record<string, string>;
  try {
    const res = await davRequest(config, MANIFEST_NAME);
    if (!res.ok) {
      result.errors.push(`Manifest fetch failed (${res.status})`);
      return result;
    }
    manifest = await res.json();
  } catch (e) {
    result.errors.push('Manifest fetch error');
    return result;
  }

  const chars: Character[] = [];
  for (const slug of Object.keys(manifest)) {
    try {
      const res = await davRequest(config, `${slug}.json`);
      if (!res.ok) {
        result.errors.push(`Download failed: ${slug} (${res.status})`);
        continue;
      }
      chars.push(await res.json());
      result.downloaded++;
    } catch (e) {
      result.errors.push(`Download error: ${slug}`);
    }
  }

  await replaceAllCharacters(chars);
  return result;
}
