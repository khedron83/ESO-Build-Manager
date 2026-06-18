APP_VERSION = "1.0.0"

ROLE_COLORS = {
    "Tank":    "#4a9eff",
    "Healer":  "#4dbd74",
    "MagDPS":  "#b06afc",
    "StamDPS": "#f97316",
    "Hybrid":  "#eab308",
}

CLASS_COLORS = {
    "Arcanist":    "#22d3ee",
    "Dragonknight":"#f87171",
    "Necromancer": "#86efac",
    "Nightblade":  "#c084fc",
    "Sorcerer":    "#60a5fa",
    "Templar":     "#facc15",
    "Warden":      "#4ade80",
}

QUALITY_COLORS = {
    "Normal":    "#aaaaaa",
    "Fine":      "#3bc28a",
    "Superior":  "#4a9eff",
    "Epic":      "#c47cfc",
    "Legendary": "#e5a635",
}

ESO_CLASSES = [
    "Arcanist",
    "Dragonknight",
    "Necromancer",
    "Nightblade",
    "Sorcerer",
    "Templar",
    "Warden",
]

ROLES = ["Healer", "Hybrid", "MagDPS", "StamDPS", "Tank"]

CONTENT_TYPES = ["Dungeon", "Overland", "PvP", "Solo", "Trial"]

GEAR_SLOTS = [
    "Head", "Shoulder", "Chest", "Hands", "Waist", "Legs", "Feet",
    "Neck", "Ring 1", "Ring 2",
    "Main Hand", "Off Hand", "Backup Main", "Backup Off",
]

ARMOR_WEIGHTS = ["Heavy", "Light", "Medium"]

GEAR_TRAITS = sorted([
    "Infused", "Divines", "Well-Fitted", "Sturdy", "Reinforced",
    "Impenetrable", "Training", "Intricate",
    "Sharpened", "Precise", "Defending", "Powered",
    "Charged", "Nirnhoned", "Decisive", "Bloodthirsty",
    "Harmony", "Protective", "Swift", "Triune",
])

JEWELRY_TRAITS = sorted([
    "Arcane", "Robust", "Healthy",
    "Bloodthirsty", "Harmony", "Infused", "Protective", "Swift", "Triune",
])

WEAPON_TRAITS = sorted([
    "Sharpened", "Precise", "Defending", "Powered", "Charged",
    "Nirnhoned", "Decisive", "Training", "Infused",
])

WEAPON_TYPES = sorted([
    "Axe", "Battle Axe", "Bow", "Dagger", "Greatsword",
    "Ice Staff", "Inferno Staff", "Lightning Staff", "Mace", "Maul",
    "Restoration Staff", "Shield", "Sword",
])

ENCHANT_SUGGESTIONS = sorted([
    # weapon glyphs
    "Absorb Health", "Absorb Magicka", "Absorb Stamina",
    "Berserker", "Crusher", "Weakening",
    "Disease Damage", "Flame Damage", "Frost Damage", "Shock Damage", "Poison Damage",
    "Oblivion Damage", "Life Drain", "Prismatic Onslaught",
    # armor glyphs
    "Max Health", "Max Magicka", "Max Stamina", "Prismatic Defense",
    "Health Recovery", "Magicka Recovery", "Stamina Recovery",
    "Physical Resistance", "Spell Resistance",
    "Reduce Block Cost", "Reduce Feat Cost", "Reduce Roll Dodge Cost", "Reduce Sprint Cost",
    # jewelry glyphs
    "Weapon Damage", "Spell Damage", "Shielding", "Bracing",
])

QUALITY_TIERS = ["Normal", "Fine", "Superior", "Epic", "Legendary"]

MUNDUS_STONES = [
    "The Apprentice",
    "The Atronach",
    "The Lady",
    "The Lord",
    "The Lover",
    "The Mage",
    "The Ritual",
    "The Serpent",
    "The Shadow",
    "The Steed",
    "The Thief",
    "The Tower",
    "The Warrior",
]

GAME_PATCHES = [
    "U35", "U36", "U37", "U38", "U39",
    "U40", "U41", "U42", "U43", "U44",
    "U45", "U46", "U47", "U48", "U49", "U50",
]
