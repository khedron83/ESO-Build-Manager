import { useState, useEffect, useCallback } from 'react';
import type { Build } from '../types';
import * as storage from '../utils/storage';

export function useBuilds() {
  const [builds, setBuilds] = useState<Build[]>([]);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const b = await storage.getBuilds();
    setBuilds(b);
    return b;
  }, []);

  useEffect(() => {
    refresh().then(() => setLoaded(true));
  }, [refresh]);

  const saveBuild = useCallback(async (build: Build) => {
    const saved = await storage.saveBuild(build);
    setBuilds(prev => {
      const idx = prev.findIndex(b => b.id === saved.id);
      return idx >= 0 ? prev.map(b => b.id === saved.id ? saved : b) : [...prev, saved];
    });
    return saved;
  }, []);

  const deleteBuild = useCallback(async (id: string) => {
    await storage.deleteBuild(id);
    setBuilds(prev => prev.filter(b => b.id !== id));
  }, []);

  const importBuild = useCallback(async (data: Record<string, unknown>) => {
    const saved = await storage.importBuild(data);
    setBuilds(prev => [...prev, saved]);
    return saved;
  }, []);

  return { builds, loaded, saveBuild, deleteBuild, importBuild, refresh };
}
