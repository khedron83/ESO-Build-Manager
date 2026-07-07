import { useState, useEffect, useCallback } from 'react';
import { createAsyncStorage } from '@react-native-async-storage/async-storage';
import type { ServerConfig } from '../types';

const storage = createAsyncStorage('eso-build-manager');
const KEY = 'server_config';
const EMPTY: ServerConfig = { url: '', username: '', password: '' };

// ponytail: module-level cache + subscribers so every screen's useSettings()
// stays in sync, instead of each call site holding its own stale copy.
let cache = EMPTY;
let loadedOnce = false;
const listeners = new Set<(c: ServerConfig) => void>();

async function load(): Promise<ServerConfig> {
  if (!loadedOnce) {
    const v = await storage.getItem(KEY);
    cache = v ? JSON.parse(v) : EMPTY;
    loadedOnce = true;
  }
  return cache;
}

export function useSettings() {
  const [config, setConfig] = useState<ServerConfig>(cache);

  useEffect(() => {
    listeners.add(setConfig);
    load().then(setConfig);
    return () => { listeners.delete(setConfig); };
  }, []);

  const saveConfig = useCallback(async (c: ServerConfig) => {
    await storage.setItem(KEY, JSON.stringify(c));
    cache = c;
    listeners.forEach(l => l(c));
  }, []);

  return { config, saveConfig };
}
