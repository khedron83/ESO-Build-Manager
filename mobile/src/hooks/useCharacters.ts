import { useState, useEffect, useCallback } from 'react';
import type { Character } from '../types';
import * as characterStorage from '../utils/characterStorage';

export function useCharacters() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    const c = await characterStorage.getCharacters();
    setCharacters(c);
    return c;
  }, []);

  useEffect(() => {
    refresh().then(() => setLoaded(true));
  }, [refresh]);

  return { characters, loaded, refresh };
}
