import type { Build, ServerConfig } from '../types';
import { getBuilds, importBuild } from './storage';

function slug(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'build';
}

function toExportDict(build: Build): Record<string, unknown> {
  return {
    _eso_build_manager_version: 1,
    name: build.name,
    eso_class: build.esoClass,
    subclass_1: build.subclass1,
    subclass_2: build.subclass2,
    role: build.role,
    content: build.content,
    game_patch: build.gamePatch,
    source: build.source,
    mundus_stone: build.mundusStone,
    food_buff: build.foodBuff,
    attribute_health: build.attributeHealth,
    attribute_magicka: build.attributeMagicka,
    attribute_stamina: build.attributeStamina,
    champion_points: build.championPoints,
    cp_slots: JSON.stringify(build.cpSlots),
    class_masteries: build.classMasteries,
    notes: build.notes,
    updated_at: build.updatedAt,
    _sync_updated_at: build.updatedAt,
    skills: build.skills.map(s => ({ bar: s.bar, slot: s.slot, name: s.name })),
    gear: build.gear.map(g => ({
      slot: g.slot, set_name: g.setName, weight: g.weight,
      trait: g.trait, enchant: g.enchant, quality: g.quality,
    })),
  };
}

export interface SyncResult {
  uploaded: number;
  downloaded: number;
  errors: string[];
}

// Android's native HttpURLConnection only allows GET/POST/PUT/DELETE/HEAD/OPTIONS/TRACE/PATCH —
// PROPFIND and MKCOL throw before the request is even sent. So instead of listing the
// directory via PROPFIND, we keep a manifest file (plain GET/PUT) of what's been synced.
const MANIFEST_NAME = '_index.json';

async function davRequest(
  config: ServerConfig,
  method: string,
  path: string,
  body?: string,
): Promise<Response> {
  const url = config.url.replace(/\/$/, '') + '/remote.php/dav/files/' + config.username + '/ESO-Builds/' + path;
  const creds = btoa(`${config.username}:${config.password}`);
  const headers: Record<string, string> = { Authorization: `Basic ${creds}` };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  return fetch(url, { method, headers, body });
}

async function loadManifest(config: ServerConfig): Promise<Record<string, string>> {
  try {
    const res = await davRequest(config, 'GET', MANIFEST_NAME);
    if (!res.ok) return {};
    return await res.json();
  } catch {
    return {};
  }
}

export async function sync(config: ServerConfig): Promise<SyncResult> {
  const result: SyncResult = { uploaded: 0, downloaded: 0, errors: [] };
  const builds = await getBuilds();
  const manifest = await loadManifest(config);

  // Upload all local builds
  const uploadedSlugs = new Set<string>();
  for (const build of builds) {
    const s = slug(build.name) + '.json';
    try {
      const res = await davRequest(config, 'PUT', s, JSON.stringify(toExportDict(build)));
      if (res.ok) {
        result.uploaded++;
        uploadedSlugs.add(s);
        manifest[s] = build.updatedAt;
      } else {
        result.errors.push(`Upload failed: ${build.name} (${res.status})`);
      }
    } catch (e) {
      result.errors.push(`Upload error: ${build.name}`);
    }
  }

  // Download anything in the manifest we didn't just upload ourselves
  for (const fname of Object.keys(manifest)) {
    if (uploadedSlugs.has(fname)) continue;
    try {
      const getRes = await davRequest(config, 'GET', fname);
      if (!getRes.ok) continue;
      const data = await getRes.json();
      await importBuild(data);
      result.downloaded++;
    } catch {
      result.errors.push(`Download error: ${fname}`);
    }
  }

  try {
    await davRequest(config, 'PUT', MANIFEST_NAME, JSON.stringify(manifest));
  } catch (e) {
    result.errors.push('Manifest save error');
  }

  return result;
}
