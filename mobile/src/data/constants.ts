export const ESO_CLASSES = [
  'Arcanist','Dragonknight','Necromancer','Nightblade','Sorcerer','Templar','Warden',
];

export const ROLES = ['DPS','Healer','Hybrid','Tank'];

export const CONTENT_TYPES = ['Dungeon','Overland','PvP','Solo','Trial'];

export const GEAR_SLOTS = [
  'Head','Shoulder','Chest','Hands','Waist','Legs','Feet',
  'Neck','Ring 1','Ring 2',
  'Main Hand','Off Hand','Backup Main','Backup Off',
];

export const ARMOR_WEIGHTS  = ['Heavy','Light','Medium'];
export const WEAPON_TYPES   = [
  'Axe','Battle Axe','Bow','Dagger','Greatsword',
  'Ice Staff','Inferno Staff','Lightning Staff','Mace','Maul',
  'Restoration Staff','Shield','Sword',
];
export const OFF_HAND_WEIGHTS = ['—','N/A','Heavy','Light','Medium'];
export const OFF_HAND_SLOTS   = new Set(['Off Hand','Backup Off']);
export const MAIN_HAND_SLOTS  = new Set(['Main Hand','Backup Main']);
export const JEWELRY_SLOTS    = new Set(['Neck','Ring 1','Ring 2']);
export const WEAPON_SLOTS     = new Set(['Main Hand','Off Hand','Backup Main','Backup Off']);

export const ARMOR_TRAITS = [
  'Divines','Infused','Impenetrable','Reinforced','Sturdy',
  'Training','Well-Fitted','Nirnhoned','Invigorating',
];
export const WEAPON_TRAITS = [
  'Charged','Defending','Infused','Nirnhoned','Precise',
  'Sharpened','Training','Powered','Decisive',
];
export const JEWELRY_TRAITS = [
  'Arcane','Bloodthirsty','Harmony','Healthy','Infused',
  'Protective','Robust','Swift','Triune',
];
export const WEAPON_ENCHANTS = [
  'Absorb Health','Absorb Magicka','Absorb Stamina',
  'Weapon Damage','Weakening','Crusher',
  'Fiery Weapon','Frost Weapon','Shock Weapon','Poisoned Weapon','Disease Weapon',
  'Decrease Health','Hardening','Prismatic Onslaught',
];
export const ARMOR_ENCHANTS = [
  'Maximum Health','Maximum Magicka','Maximum Stamina','Multi-Effect',
];
export const JEWELRY_ENCHANTS = [
  'Weapon Damage','Spell Damage',
  'Health Recovery','Magicka Recovery','Stamina Recovery','Prismatic Recovery',
  'Physical Resistance','Spell Resistance',
  'Flame Resist','Frost Resist','Shock Resist','Poison Resist','Disease Resist',
  'Reduce Spell Cost','Reduce Feat Cost','Reduce Skill Cost',
  'Shielding','Bashing','Potion Boost','Potion Resist',
];
export const QUALITY_TIERS = ['Normal','Fine','Superior','Epic','Legendary'];
export const MUNDUS_STONES = [
  'The Apprentice','The Atronach','The Lady','The Lord','The Lover',
  'The Mage','The Ritual','The Serpent','The Shadow','The Steed',
  'The Thief','The Tower','The Warrior',
];
export const GAME_PATCHES = [
  'U35','U36','U37','U38','U39','U40','U41','U42',
  'U43','U44','U45','U46','U47','U48','U49','U50',
];
export const CP_TREE_LABELS = ['Craft','Warfare','Fitness'];
export const CP_SLOT_COUNT  = 12;

export const QUALITY_COLORS: Record<string, string> = {
  Legendary: '#e5a623',
  Epic:      '#a335ee',
  Superior:  '#0070dd',
  Fine:      '#1eff00',
  Normal:    '#888',
};

export const ROLE_COLORS: Record<string, string> = {
  Tank:    '#4fc3f7',
  Healer:  '#81c784',
  DPS:     '#ef5350',
  Hybrid:  '#ffb74d',
};

export const CLASS_SKILL_LINES: Record<string, string[]> = {
  Arcanist:     ['Apocrypha','Herald of the Tome','Soldier of Apocrypha'],
  Dragonknight: ['Ardent Flame','Draconic Power','Earthen Heart'],
  Necromancer:  ['Bone Tyrant','Grave Lord','Living Death'],
  Nightblade:   ['Assassination','Shadow','Siphoning'],
  Sorcerer:     ['Daedric Summoning','Dark Magic','Storm Calling'],
  Templar:      ['Aedric Spear',"Dawn's Wrath",'Restoring Light'],
  Warden:       ['Animal Companions','Green Balance',"Winter's Embrace"],
};

export function skillLinesExcluding(...excluded: string[]): string[] {
  return Object.entries(CLASS_SKILL_LINES)
    .filter(([cls]) => !excluded.includes(cls))
    .flatMap(([, lines]) => lines);
}
