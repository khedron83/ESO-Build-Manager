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

export interface SkillLine {
  name: string;
  rank: number;
}

export interface Constellation {
  name: string;
  spent: number;
  unspent: number;
  skills: number[];
}

export interface InventoryItem {
  name: string;
  count: number;
  bag: string;
}

// Field names are snake_case, matching desktop's dataclasses.asdict(Character)
// export verbatim -- this is a read-only sync path (character data always
// originates from the game addon, never edited on mobile), so there's no
// round-trip mapping layer to keep in sync the way Build has with
// toExportDict/importBuild.
export interface Character {
  name: string;
  account: string;
  class_name: string;
  race_name: string;
  faction_name: string;
  alliance_rank: number;
  level: number;
  champion_points: number;
  is_champion: boolean;
  seconds_played: number;
  last_updated: number;
  gold: number;
  ap: number;
  telvar: number;
  writ_vouchers: number;
  currencies: Record<string, number>;
  bank_currencies: Record<string, number>;
  soul_gems_filled: number;
  soul_gems_empty: number;
  bag_used: number;
  bag_size: number;
  health_max: number;
  stamina_max: number;
  magicka_max: number;
  health_recovery: number;
  stamina_recovery: number;
  magicka_recovery: number;
  spell_damage: number;
  weapon_damage: number;
  crit_chance: number;
  resist_physical: number;
  resist_spell: number;
  resist_crit: number;
  mount_speed: number;
  mount_stamina: number;
  mount_capacity: number;
  cp_spent: number;
  cp_unspent: number;
  skill_points_unspent: number;
  skills_class: SkillLine[];
  skills_weapon: SkillLine[];
  skills_armor: SkillLine[];
  skills_guild: SkillLine[];
  skills_ava: SkillLine[];
  skills_world: SkillLine[];
  skills_racial: SkillLine[];
  skills_craft: SkillLine[];
  constellations: Constellation[];
  inventory: InventoryItem[];
  daily_dungeon_done: boolean;
  daily_writs_done: boolean;
}

export type RootStackParamList = {
  Builds: undefined;
  BuildDetail: { buildId: string };
  BuildEditor: { buildId: string | null };
  Settings: undefined;
  Characters: undefined;
  CharacterDetail: { name: string };
};
