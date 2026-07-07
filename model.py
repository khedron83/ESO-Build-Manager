"""Data model extracted from LeoAltholic and WizardsWardrobe saved variables."""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field

CONSTELLATIONS = ['Craft', 'Warfare', 'Fitness']

_CURRENCY_LABELS = {
    'gold': 'Gold', 'ap': 'Alliance Points', 'telvar': 'Tel Var Stones',
    'writVouchers': 'Writ Vouchers', 'undauntedKeys': 'Undaunted Keys',
    'crowns': 'Crowns', 'crownGems': 'Crown Gems', 'endeavorSeals': 'Seals of Endeavor',
}


@dataclass
class SkillLine:
    name: str
    rank: int


@dataclass
class Constellation:
    name: str
    spent: int
    unspent: int
    skills: list[int]   # raw point allocations per slot


@dataclass
class InventoryItem:
    name: str
    count: int
    bag: str            # 'Backpack' or 'Bank'


@dataclass
class Character:
    name: str
    class_name: str = ''
    race_name: str = ''
    faction_name: str = ''
    alliance_rank: int = 0
    level: int = 0
    champion_points: int = 0
    is_champion: bool = False
    seconds_played: int = 0
    last_updated: int = 0  # unix timestamp of the addon snapshot that produced this data
    gold: int = 0
    ap: int = 0
    telvar: int = 0
    writ_vouchers: int = 0
    currencies: dict[str, int] = field(default_factory=dict)       # display name -> on-person amount
    bank_currencies: dict[str, int] = field(default_factory=dict)  # display name -> shared account/bank amount
    soul_gems_filled: int = 0
    soul_gems_empty: int = 0
    bag_used: int = 0
    bag_size: int = 0
    health_max: int = 0
    stamina_max: int = 0
    magicka_max: int = 0
    health_recovery: int = 0
    stamina_recovery: int = 0
    magicka_recovery: int = 0
    spell_damage: int = 0
    weapon_damage: int = 0
    crit_chance: float = 0.0
    resist_physical: int = 0
    resist_spell: int = 0
    resist_crit: int = 0
    mount_speed: int = 0
    mount_stamina: int = 0
    mount_capacity: int = 0
    cp_unspent: int = 0
    cp_spent: int = 0
    skill_points_unspent: int = 0
    skills_class: list[SkillLine] = field(default_factory=list)
    skills_weapon: list[SkillLine] = field(default_factory=list)
    skills_armor: list[SkillLine] = field(default_factory=list)
    skills_guild: list[SkillLine] = field(default_factory=list)
    skills_ava: list[SkillLine] = field(default_factory=list)
    skills_world: list[SkillLine] = field(default_factory=list)
    skills_racial: list[SkillLine] = field(default_factory=list)
    skills_craft: list[SkillLine] = field(default_factory=list)
    constellations: list[Constellation] = field(default_factory=list)
    inventory: list[InventoryItem] = field(default_factory=list)


def extract(lua_data: dict) -> list[Character]:
    sv = lua_data.get('LeoAltholicSavedVariables', {})
    for server_data in sv.values():
        for account_data in server_data.values():
            char_list = account_data.get('$AccountWide', {}).get('CharList', {})
            if char_list:
                return [_parse_char(d) for d in char_list.values()]
    return []


def extract_from_wg(lua_data: dict) -> list[Character]:
    """Build Character list from WornGear's __char__ sections (replaces LeoAltholic)."""
    sv = lua_data.get('WornGearSV', {})
    chars = []
    for char_name, char_data in sv.items():
        if not isinstance(char_data, dict):
            continue
        c = char_data.get('__char__')
        if not isinstance(c, dict):
            continue
        chars.append(_parse_wg_char(char_name, c))
    return sorted(chars, key=lambda c: c.name)


def _parse_wg_char(char_name: str, c: dict) -> Character:
    bio  = c.get('bio', {})
    st   = c.get('stats', {})
    mnt  = c.get('mount', {})
    cur     = c.get('currencies', {})
    bankCur = c.get('bankCurrencies', {})
    bag  = c.get('bag', {})
    sk   = c.get('skills', {})
    champ = c.get('champion', {})
    inv_raw = c.get('inventory', [])

    # Champion constellations from full per-star data
    cp_spent = cp_unspent = 0
    constellations = []
    disciplines = champ.get('disciplines', {}) if isinstance(champ, dict) else {}
    earned = champ.get('earned', 0) if isinstance(champ, dict) else 0
    cp_unspent = champ.get('unspent', 0) if isinstance(champ, dict) else 0
    cp_spent   = champ.get('spent', 0) if isinstance(champ, dict) else 0
    for disc_name in CONSTELLATIONS:
        d = disciplines.get(disc_name, {})
        spent = d.get('spent', 0) if isinstance(d, dict) else 0
        stars_raw = d.get('stars', {}) if isinstance(d, dict) else {}
        stars = list(stars_raw.values()) if isinstance(stars_raw, dict) else []
        constellations.append(Constellation(name=disc_name, spent=spent,
                                            unspent=0, skills=stars))

    items = [InventoryItem(name=i['name'], count=i.get('count', 1), bag=i.get('bag', ''))
             for i in (inv_raw if isinstance(inv_raw, list) else [])
             if isinstance(i, dict) and 'name' in i]

    return Character(
        name=bio.get('name', char_name),
        class_name=bio.get('class', ''),
        race_name=bio.get('race', ''),
        faction_name=bio.get('alliance', ''),
        alliance_rank=bio.get('avARank', 0),
        level=bio.get('level', 0),
        champion_points=bio.get('championPoints', 0),
        is_champion=bio.get('isChampion', False),
        seconds_played=bio.get('secondsPlayed', 0),
        last_updated=bio.get('lastUpdated', 0),
        skill_points_unspent=bio.get('skillPoints', 0),
        gold=cur.get('gold', 0),
        ap=cur.get('ap', 0),
        telvar=cur.get('telvar', 0),
        writ_vouchers=cur.get('writVouchers', 0),
        currencies={_CURRENCY_LABELS.get(k, k): v for k, v in cur.items()},
        bank_currencies={_CURRENCY_LABELS.get(k, k): v for k, v in bankCur.items()},
        soul_gems_filled=bag.get('soulsFilled', 0),
        soul_gems_empty=bag.get('soulsEmpty', 0),
        bag_used=bag.get('used', 0),
        bag_size=bag.get('size', 0),
        health_max=st.get('healthMax', 0),
        stamina_max=st.get('staminaMax', 0),
        magicka_max=st.get('magickaMax', 0),
        health_recovery=st.get('healthRegen', 0),
        stamina_recovery=st.get('staminaRegen', 0),
        magicka_recovery=st.get('magickaRegen', 0),
        spell_damage=st.get('spellDamage', 0),
        weapon_damage=st.get('weaponDamage', 0),
        crit_chance=st.get('critChance', 0.0),
        resist_physical=st.get('physResist', 0),
        resist_spell=st.get('spellResist', 0),
        resist_crit=st.get('critResist', 0),
        mount_speed=mnt.get('speed', 0),
        mount_stamina=mnt.get('stamina', 0),
        mount_capacity=mnt.get('capacity', 0),
        cp_spent=cp_spent,
        cp_unspent=cp_unspent,
        skills_class=_wg_skill_lines(sk.get('class', [])),
        skills_weapon=_wg_skill_lines(sk.get('weapon', [])),
        skills_armor=_wg_skill_lines(sk.get('armor', [])),
        skills_guild=_wg_skill_lines(sk.get('guild', [])),
        skills_ava=_wg_skill_lines(sk.get('ava', [])),
        skills_world=_wg_skill_lines(sk.get('world', [])),
        skills_racial=_wg_skill_lines(sk.get('racial', [])),
        skills_craft=_wg_skill_lines(sk.get('craft', [])),
        constellations=constellations,
        inventory=items,
    )


def _wg_skill_lines(raw) -> list[SkillLine]:
    if not isinstance(raw, list):
        return []
    return sorted(
        [SkillLine(name=i['name'], rank=i.get('rank', 0))
         for i in raw if isinstance(i, dict) and 'name' in i],
        key=lambda s: s.name,
    )


def _skill_lines(raw) -> list[SkillLine]:
    items = raw.values() if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
    return sorted(
        [SkillLine(name=i['name'], rank=i.get('rank', 0))
         for i in items if isinstance(i, dict) and 'name' in i],
        key=lambda s: s.name,
    )


def _parse_char(data: dict) -> Character:
    bio    = data.get('bio', {})
    attrs  = data.get('attributes', {})
    resist = data.get('resistances', {})
    inv    = data.get('inventory', {})
    skills = data.get('skills', {})
    champ  = data.get('champion', [])
    riding = attrs.get('riding', {})
    alliance = bio.get('alliance') or {}

    cp_unspent = cp_spent = 0
    constellations = []
    for i, c in enumerate(champ):
        if isinstance(c, dict):
            cp_unspent += c.get('unspent', 0)
            cp_spent   += c.get('spent', 0)
            constellations.append(Constellation(
                name=CONSTELLATIONS[i] if i < len(CONSTELLATIONS) else f'Constellation {i+1}',
                spent=c.get('spent', 0),
                unspent=c.get('unspent', 0),
                skills=c.get('skills', []),
            ))

    # inventory: bag key 0 = backpack, 1 = bank
    items: list[InventoryItem] = []
    for bag_key, bag_name in [(0, 'Backpack'), (1, 'Bank')]:
        bag = inv.get(bag_key, {})
        if isinstance(bag, dict):
            for slot in bag.values():
                if isinstance(slot, dict) and 'name' in slot:
                    items.append(InventoryItem(
                        name=slot['name'],
                        count=slot.get('count', 1),
                        bag=bag_name,
                    ))

    return Character(
        name=bio.get('name', '?'),
        class_name=bio.get('class', '?'),
        race_name=bio.get('race', '?'),
        faction_name=alliance.get('name', '?'),
        alliance_rank=alliance.get('rank', 0),
        level=bio.get('level', 0),
        champion_points=bio.get('championPoints', 0),
        is_champion=bio.get('isChampion', False),
        seconds_played=data.get('secondsPlayed', 0),
        gold=inv.get('gold', 0),
        ap=inv.get('ap', 0),
        telvar=inv.get('telvar', 0),
        writ_vouchers=inv.get('writVoucher', 0),
        soul_gems_filled=inv.get('soulGemFilled', 0),
        soul_gems_empty=inv.get('soulGemEmpty', 0),
        bag_used=inv.get('used', 0),
        bag_size=inv.get('size', 0),
        health_max=attrs.get('health', {}).get('max', 0),
        stamina_max=attrs.get('stamina', {}).get('max', 0),
        magicka_max=attrs.get('magicka', {}).get('max', 0),
        health_recovery=attrs.get('health', {}).get('recovery', 0),
        stamina_recovery=attrs.get('stamina', {}).get('recovery', 0),
        magicka_recovery=attrs.get('magicka', {}).get('recovery', 0),
        spell_damage=attrs.get('spell', {}).get('damage', 0),
        weapon_damage=attrs.get('weapon', {}).get('damage', 0),
        crit_chance=attrs.get('spell', {}).get('criticalChance', 0.0),
        resist_physical=resist.get('resistPhysical', 0),
        resist_spell=resist.get('spell', 0),
        resist_crit=resist.get('crit', 0),
        mount_speed=riding.get('speed', 0),
        mount_stamina=riding.get('stamina', 0),
        mount_capacity=riding.get('capacity', 0),
        cp_unspent=cp_unspent,
        cp_spent=cp_spent,
        skill_points_unspent=skills.get('unspent', 0),
        skills_class=_skill_lines(skills.get('class', [])),
        skills_weapon=_skill_lines(skills.get('weapon', [])),
        skills_armor=_skill_lines(skills.get('armor', [])),
        skills_guild=_skill_lines(skills.get('guild', [])),
        skills_ava=_skill_lines(skills.get('ava', [])),
        skills_world=_skill_lines(skills.get('world', [])),
        skills_racial=_skill_lines(skills.get('racial', [])),
        skills_craft=_skill_lines(skills.get('craft', [])),
        constellations=constellations,
        inventory=items,
    )


# ── WizardsWardrobe gear setups ───────────────────────────────────────────────

@dataclass
class WWSetup:
    name: str                          # e.g. "Tank", "DPS", "Trash"
    sets: dict[str, int]               # {set_name: piece_count}


def extract_worn_gear(lua_data: dict) -> dict[str, dict[str, dict[str, dict]]]:
    """Return {char_name: {build_name: {slot_name: {name, setName, link}}}} from WornGear addon."""
    return lua_data.get('WornGearSV', {})


def extract_ww(lua_data: dict, sets_db: dict[int, str]) -> dict[str, list[WWSetup]]:
    """Return {char_name: [WWSetup, ...]} for chars with gear-populated GEN setups."""
    sv = lua_data.get('WizardsWardrobeSV', {}).get('Default', {})
    account = next(iter(sv.values()), {}) if sv else {}

    result: dict[str, list[WWSetup]] = {}
    for char_id, char_data in account.items():
        if not isinstance(char_data, dict):
            continue
        char_name = char_data.get('$LastCharacterName', '')
        if not char_name:
            continue
        gen = char_data.get('setups', {}).get('GEN', [])
        # GEN is a list of groups; each group is a list of setup dicts
        char_setups: list[WWSetup] = []
        for group in (gen if isinstance(gen, list) else gen.values()):
            pages = group if isinstance(group, list) else group.values()
            for page in pages:
                if not isinstance(page, dict) or 'name' not in page or 'gear' not in page:
                    continue
                gear = page['gear']
                if not isinstance(gear, dict):
                    continue
                counts: Counter = Counter()
                for item in gear.values():
                    if not isinstance(item, dict):
                        continue
                    link = item.get('link', '')
                    if not link or item.get('id', '0') == '0':
                        continue
                    parts = link.split(':')
                    if len(parts) > 17 and parts[17].isdigit():
                        set_id = int(parts[17])
                        if set_id:
                            counts[set_id] += 1
                if counts:
                    named = {sets_db.get(sid, f'Set #{sid}'): n for sid, n in counts.items()}
                    char_setups.append(WWSetup(name=page['name'], sets=named))
        if char_setups:
            result[char_name] = char_setups
    return result
