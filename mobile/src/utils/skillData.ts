import skillsJson from '../data/skills.json';
import skillIdsJson from '../data/skill_ids.json';
import { uespUrl } from './md5';

const GRIMOIRE_ICONS: Record<string, string> = {
  "Banner Bearer":         "ON-icon-book-grimoire-Support.png",
  "Elemental Explosion":   "ON-icon-book-grimoire-Destruction Staff.png",
  "Mender's Bond":         "ON-icon-book-grimoire-Restoration Staff.png",
  "Shield Throw":          "ON-icon-book-grimoire-1-Handed.png",
  "Smash":                 "ON-icon-book-grimoire-2-Handed.png",
  "Soul Burst":            "ON-icon-book-grimoire-Soul Magic 02.png",
  "Torchbearer":           "ON-icon-book-grimoire-Fighters Guild.png",
  "Trample":               "ON-icon-book-grimoire-Assault.png",
  "Traveling Knife":       "ON-icon-book-grimoire-Dual Wield.png",
  "Ulfsild's Contingency": "ON-icon-book-grimoire-Mages Guild.png",
  "Vault":                 "ON-icon-book-grimoire-Bow.png",
  "Wield Soul":            "ON-icon-book-grimoire-Soul Magic 01.png",
};

const _scribingFallback = uespUrl(GRIMOIRE_ICONS["Ulfsild's Contingency"]);

let _skillNames: string[] = [];
let _lineMap: Record<string, string> = {};
let _classMasteryMap: Record<string, string[]> = {};
let _initialized = false;

function init() {
  if (_initialized) return;
  const names = new Set<string>();

  for (const cat of skillsJson as any[]) {
    const { category, line, skills } = cat;
    if (category === 'Class Mastery') {
      _classMasteryMap[line] = (skills as any[]).map((s: any) => s.base);
      continue;
    }
    for (const skill of skills as any[]) {
      names.add(skill.base);
      _lineMap[skill.base] = line;
      for (const morph of skill.morphs ?? []) {
        names.add(morph);
        _lineMap[morph] = line;
      }
    }
  }

  for (const [lineKey, skillDict] of Object.entries(skillIdsJson as Record<string, any>)) {
    const sep = lineKey.indexOf('::');
    const line = sep >= 0 ? lineKey.substring(sep + 2) : '';
    for (const name of Object.keys(skillDict)) {
      names.add(name);
      if (line && !_lineMap[name]) _lineMap[name] = line;
    }
  }

  _skillNames = [...names].sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
  _initialized = true;
}

export function getSkillNames(): string[] {
  init();
  return _skillNames;
}

export function getClassMasteries(esoClass: string): string[] {
  init();
  return _classMasteryMap[esoClass] ?? [];
}

export function skillIconUrl(skillName: string): string {
  init();
  if (GRIMOIRE_ICONS[skillName]) return uespUrl(GRIMOIRE_ICONS[skillName]);
  const line = _lineMap[skillName];
  if (!line || line === 'Grimoires') return _scribingFallback;
  return uespUrl(`ON-icon-skill-${line}-${skillName}.png`);
}
