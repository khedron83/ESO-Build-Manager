import { createAsyncStorage } from '@react-native-async-storage/async-storage';
import type { Character } from '../types';

const storage = createAsyncStorage('eso-build-manager');
const CHARACTERS_KEY = 'characters_v1';

export async function getCharacters(): Promise<Character[]> {
  const raw = await storage.getItem(CHARACTERS_KEY);
  return raw ? JSON.parse(raw) : [];
}

export async function getCharacter(name: string): Promise<Character | undefined> {
  const all = await getCharacters();
  return all.find(c => c.name === name);
}

// Character data is a straight replace-all on every sync (desktop always has
// the freshest snapshot from the game addon), unlike builds which merge
// individual records.
export async function replaceAllCharacters(chars: Character[]): Promise<void> {
  await storage.setItem(CHARACTERS_KEY, JSON.stringify(chars));
}
