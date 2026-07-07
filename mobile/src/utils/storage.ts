import { createAsyncStorage } from '@react-native-async-storage/async-storage';
import type { Build, GearPiece, Skill } from '../types';
import { GEAR_SLOTS } from '../data/constants';

const storage = createAsyncStorage('eso-build-manager');
const BUILDS_KEY = 'builds_v1';

function emptyBuild(id: string): Build {
  return {
    id,
    name: 'New Build',
    esoClass: '', subclass1: '', subclass2: '',
    role: '', content: '', gamePatch: 'U50',
    source: '', mundusStone: '', foodBuff: '',
    attributeHealth: 0, attributeMagicka: 0, attributeStamina: 64,
    championPoints: '',
    cpSlots: Array(12).fill(''),
    classMasteries: [],
    notes: '',
    updatedAt: new Date().toISOString(),
    skills: [0, 1].flatMap(bar => [0,1,2,3,4,5].map(slot => ({ bar, slot, name: '' }))),
    gear: GEAR_SLOTS.map(slot => ({ slot, setName: '', weight: '', trait: '', enchant: '', quality: 'Epic' })),
  };
}

async function loadAll(): Promise<Build[]> {
  const raw = await storage.getItem(BUILDS_KEY);
  return raw ? JSON.parse(raw) : [];
}

async function saveAll(builds: Build[]): Promise<void> {
  await storage.setItem(BUILDS_KEY, JSON.stringify(builds));
}

export async function getBuilds(): Promise<Build[]> {
  return loadAll();
}

export async function getBuild(id: string): Promise<Build | undefined> {
  const all = await loadAll();
  return all.find(b => b.id === id);
}

export function newBuild(): Build {
  return emptyBuild(Date.now().toString());
}

export async function saveBuild(build: Build): Promise<Build> {
  const all = await loadAll();
  const updated = { ...build, updatedAt: new Date().toISOString() };
  const idx = all.findIndex(b => b.id === build.id);
  if (idx >= 0) all[idx] = updated; else all.push(updated);
  await saveAll(all);
  return updated;
}

export async function deleteBuild(id: string): Promise<void> {
  const all = await loadAll();
  await saveAll(all.filter(b => b.id !== id));
}

export async function importBuild(data: Record<string, unknown>): Promise<Build> {
  const skills: Skill[] = ((data.skills ?? []) as any[]).map((s: any) => ({
    bar: s.bar ?? 0, slot: s.slot ?? 0, name: s.name ?? '',
  }));
  const gear: GearPiece[] = ((data.gear ?? []) as any[]).map((g: any) => ({
    slot: g.slot ?? '', setName: g.set_name ?? g.setName ?? '',
    weight: g.weight ?? '', trait: g.trait ?? '',
    enchant: g.enchant ?? '', quality: g.quality ?? 'Epic',
  }));
  const cpSlots: string[] = (() => {
    try { return JSON.parse(data.cp_slots as string ?? '[]'); } catch { return Array(12).fill(''); }
  })();
  const build: Build = {
    id: Date.now().toString(),
    name: (data.name as string) ?? 'Imported Build',
    esoClass: (data.eso_class as string) ?? '',
    subclass1: (data.subclass_1 as string) ?? '',
    subclass2: (data.subclass_2 as string) ?? '',
    role: (data.role as string) ?? '',
    content: (data.content as string) ?? '',
    gamePatch: (data.game_patch as string) ?? 'U50',
    source: (data.source as string) ?? '',
    mundusStone: (data.mundus_stone as string) ?? '',
    foodBuff: (data.food_buff as string) ?? '',
    attributeHealth: (data.attribute_health as number) ?? 0,
    attributeMagicka: (data.attribute_magicka as number) ?? 0,
    attributeStamina: (data.attribute_stamina as number) ?? 64,
    championPoints: (data.champion_points as string) ?? '',
    cpSlots,
    classMasteries: ((data.class_masteries as string[]) ?? []),
    notes: (data.notes as string) ?? '',
    updatedAt: (data.updated_at as string) ?? new Date().toISOString(),
    skills, gear,
  };
  return saveBuild(build);
}
