export interface Skill {
  bar: number;    // 0 = front, 1 = back
  slot: number;   // 0-4 = active, 5 = ultimate
  name: string;
}

export interface GearPiece {
  slot: string;
  setName: string;
  weight: string;
  trait: string;
  enchant: string;
  quality: string;
}

export interface Build {
  id: string;
  name: string;
  esoClass: string;
  subclass1: string;
  subclass2: string;
  role: string;
  content: string;
  gamePatch: string;
  source: string;
  mundusStone: string;
  foodBuff: string;
  attributeHealth: number;
  attributeMagicka: number;
  attributeStamina: number;
  championPoints: string;
  cpSlots: string[];      // 12 items
  classMasteries: string[];
  notes: string;
  updatedAt: string;
  skills: Skill[];
  gear: GearPiece[];
}

export interface ServerConfig {
  url: string;
  username: string;
  password: string;
}

export type RootStackParamList = {
  Builds: undefined;
  BuildDetail: { buildId: string };
  BuildEditor: { buildId: string | null };
  Settings: undefined;
};
