import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View, Text, TextInput, ScrollView, TouchableOpacity,
  StyleSheet, Switch, FlatList, Image, Alert,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList, Build, GearPiece } from '../types';
import { colors, spacing, radius, font } from '../theme';
import {
  ESO_CLASSES, ROLES, CONTENT_TYPES, GEAR_SLOTS, GAME_PATCHES,
  ARMOR_WEIGHTS, WEAPON_TYPES, OFF_HAND_WEIGHTS, OFF_HAND_SLOTS, MAIN_HAND_SLOTS,
  JEWELRY_SLOTS, WEAPON_SLOTS, ARMOR_TRAITS, WEAPON_TRAITS, JEWELRY_TRAITS,
  WEAPON_ENCHANTS, ARMOR_ENCHANTS, JEWELRY_ENCHANTS, QUALITY_TIERS, MUNDUS_STONES, CP_TREE_LABELS, skillLinesExcluding,
} from '../data/constants';
import { getSkillNames, skillIconUrl, getClassMasteries } from '../utils/skillData';
import { newBuild, getBuild } from '../utils/storage';
import { useBuilds } from '../hooks/useBuilds';

type Props = NativeStackScreenProps<RootStackParamList, 'BuildEditor'>;

const TABS = ['Info', 'Skills', 'Gear', 'Stats', 'Passives', 'Notes'];

export default function BuildEditorScreen({ route, navigation }: Props) {
  const { saveBuild } = useBuilds();
  const [build, setBuild] = useState<Build | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    const { buildId } = route.params;
    if (buildId) {
      getBuild(buildId).then(b => setBuild(b ?? null));
    } else {
      setBuild(newBuild());
    }
  }, [route.params.buildId]);

  useEffect(() => {
    if (!build) return;
    navigation.setOptions({
      title: build.id ? 'Edit Build' : 'New Build',
      headerRight: () => (
        <TouchableOpacity onPress={handleSave} style={{ marginRight: spacing.sm }}>
          <Text style={{ color: colors.primary, fontSize: font.md, fontWeight: '700' }}>Save</Text>
        </TouchableOpacity>
      ),
    });
  }, [build]);

  function update(patch: Partial<Build>) {
    setBuild(prev => prev ? { ...prev, ...patch } : prev);
  }

  async function handleSave() {
    if (!build) return;
    await saveBuild(build);
    navigation.goBack();
  }

  if (!build) return null;

  return (
    <View style={s.container}>
      {/* Tab bar */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.tabBar} contentContainerStyle={s.tabBarContent}>
        {TABS.map((tab, i) => (
          <TouchableOpacity key={tab} style={[s.tab, activeTab === i && s.tabActive]} onPress={() => setActiveTab(i)}>
            <Text style={[s.tabText, activeTab === i && s.tabTextActive]}>{tab}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {activeTab === 0 && <InfoTab build={build} update={update} />}
      {activeTab === 1 && <SkillsTab build={build} update={update} />}
      {activeTab === 2 && <GearTab build={build} update={update} />}
      {activeTab === 3 && <StatsTab build={build} update={update} />}
      {activeTab === 4 && <PassivesTab build={build} update={update} />}
      {activeTab === 5 && <NotesTab build={build} update={update} />}
    </View>
  );
}

// ── shared input components ───────────────────────────────────────────────────

function Field({ label, value, onChangeText, multiline, keyboardType }: {
  label: string; value: string; onChangeText: (v: string) => void;
  multiline?: boolean; keyboardType?: 'default' | 'numeric';
}) {
  return (
    <View style={f.wrap}>
      <Text style={f.label}>{label}</Text>
      <TextInput
        style={[f.input, multiline && f.multiline]}
        value={value} onChangeText={onChangeText}
        multiline={multiline}
        keyboardType={keyboardType}
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
      />
    </View>
  );
}

function Picker({ label, value, options, onSelect }: {
  label: string; value: string; options: string[]; onSelect: (v: string) => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <View style={f.wrap}>
      <Text style={f.label}>{label}</Text>
      <TouchableOpacity style={f.picker} onPress={() => setOpen(!open)}>
        <Text style={{ color: value ? colors.text : colors.textSecondary, fontSize: font.sm }}>
          {value || '—'}
        </Text>
        <Text style={{ color: colors.textSecondary }}>▾</Text>
      </TouchableOpacity>
      {open && (
        <View style={f.dropdown}>
          {options.map(opt => (
            <TouchableOpacity key={opt} style={f.dropItem} onPress={() => { onSelect(opt); setOpen(false); }}>
              <Text style={[f.dropText, opt === value && { color: colors.primary }]}>{opt || '—'}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

function AutocompleteField({ label, value, onChangeText, candidates }: {
  label: string; value: string; onChangeText: (v: string) => void; candidates: string[];
}) {
  const [showDropdown, setShowDropdown] = useState(false);
  const suggestions = useMemo(() => {
    if (value.length < 2) return [];
    return candidates.filter(c => c.toLowerCase().includes(value.toLowerCase())).slice(0, 8);
  }, [value, candidates]);

  return (
    <View style={f.wrap}>
      <Text style={f.label}>{label}</Text>
      <TextInput
        style={f.input}
        value={value}
        onChangeText={v => { onChangeText(v); setShowDropdown(true); }}
        onFocus={() => setShowDropdown(true)}
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
        autoCorrect={false}
      />
      {showDropdown && suggestions.length > 0 && (
        <View style={f.dropdown}>
          {suggestions.map(s => (
            <TouchableOpacity key={s} style={f.dropItem} onPress={() => { onChangeText(s); setShowDropdown(false); }}>
              <Text style={f.dropText}>{s}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const f = StyleSheet.create({
  wrap: { marginBottom: spacing.md },
  label: { fontSize: font.xs, color: colors.textSecondary, marginBottom: 4, letterSpacing: 0.5 },
  input: {
    backgroundColor: colors.surface, borderRadius: radius.sm, padding: spacing.sm,
    fontSize: font.sm, color: colors.text, borderWidth: 1, borderColor: colors.border,
  },
  multiline: { minHeight: 80, textAlignVertical: 'top' },
  picker: {
    backgroundColor: colors.surface, borderRadius: radius.sm, padding: spacing.sm,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    borderWidth: 1, borderColor: colors.border,
  },
  dropdown: {
    backgroundColor: colors.surfaceAlt, borderRadius: radius.sm, borderWidth: 1,
    borderColor: colors.border, maxHeight: 200,
  },
  dropItem: { padding: spacing.sm, borderBottomWidth: 0.5, borderBottomColor: colors.border },
  dropText: { fontSize: font.sm, color: colors.text },
});

// ── tabs ─────────────────────────────────────────────────────────────────────

function InfoTab({ build, update }: { build: Build; update: (p: Partial<Build>) => void }) {
  const sub1Lines = useMemo(() => ['', ...skillLinesExcluding(build.esoClass)], [build.esoClass]);
  const sub2Lines = useMemo(() => {
    const sub1Cls = Object.entries(
      require('../data/constants').CLASS_SKILL_LINES as Record<string, string[]>
    ).find(([, lines]) => lines.includes(build.subclass1))?.[0] ?? '';
    return ['', ...skillLinesExcluding(build.esoClass, sub1Cls)];
  }, [build.esoClass, build.subclass1]);

  return (
    <ScrollView style={s.tab1} contentContainerStyle={s.tabContent}>
      <Field label="Build Name" value={build.name} onChangeText={v => update({ name: v })} />
      <Picker label="Class"  value={build.esoClass}  options={['', ...ESO_CLASSES]} onSelect={v => update({ esoClass: v })} />
      <Picker label="Subclass Line 1" value={build.subclass1} options={sub1Lines} onSelect={v => update({ subclass1: v })} />
      <Picker label="Subclass Line 2" value={build.subclass2} options={sub2Lines} onSelect={v => update({ subclass2: v })} />
      <Picker label="Role"    value={build.role}    options={['', ...ROLES]} onSelect={v => update({ role: v })} />
      <Picker label="Content" value={build.content} options={['', ...CONTENT_TYPES]} onSelect={v => update({ content: v })} />
      <Picker label="Patch"   value={build.gamePatch} options={GAME_PATCHES} onSelect={v => update({ gamePatch: v })} />
      <Field  label="Source URL / Creator" value={build.source} onChangeText={v => update({ source: v })} />
    </ScrollView>
  );
}

function SkillsTab({ build, update }: { build: Build; update: (p: Partial<Build>) => void }) {
  const skillNames = useMemo(() => getSkillNames(), []);

  function setSkill(bar: number, slot: number, name: string) {
    const skills = build.skills.map(s =>
      s.bar === bar && s.slot === slot ? { ...s, name } : s
    );
    update({ skills });
  }

  return (
    <ScrollView style={s.tab1} contentContainerStyle={s.tabContent}>
      {[0, 1].map(bar => {
        const barSkills = Object.fromEntries(build.skills.filter(s => s.bar === bar).map(s => [s.slot, s.name]));
        return (
          <View key={bar} style={{ marginBottom: spacing.lg }}>
            <Text style={s.barHeader}>{bar === 0 ? 'Front Bar' : 'Back Bar'}</Text>
            {[0,1,2,3,4].map(slot => (
              <SkillSlotRow
                key={slot}
                label={`Slot ${slot + 1}`}
                value={barSkills[slot] ?? ''}
                onChangeText={v => setSkill(bar, slot, v)}
                candidates={skillNames}
              />
            ))}
            <SkillSlotRow
              label="Ultimate"
              value={barSkills[5] ?? ''}
              onChangeText={v => setSkill(bar, 5, v)}
              candidates={skillNames}
            />
          </View>
        );
      })}
    </ScrollView>
  );
}

function SkillSlotRow({ label, value, onChangeText, candidates }: {
  label: string; value: string; onChangeText: (v: string) => void; candidates: string[];
}) {
  const [showDropdown, setShowDropdown] = useState(false);
  const suggestions = useMemo(() => {
    if (value.length < 2) return [];
    return candidates.filter(c => c.toLowerCase().includes(value.toLowerCase())).slice(0, 8);
  }, [value, candidates]);
  const url = value ? skillIconUrl(value) : null;

  return (
    <View style={{ marginBottom: spacing.sm }}>
      <Text style={f.label}>{label}</Text>
      <View style={s.skillSlotRow}>
        <Image source={url ? { uri: url } : undefined} style={s.slotIcon} />
        <View style={{ flex: 1 }}>
          <TextInput
            style={f.input}
            value={value}
            onChangeText={v => { onChangeText(v); setShowDropdown(true); }}
            onFocus={() => setShowDropdown(true)}
            placeholderTextColor={colors.textSecondary}
            autoCapitalize="none"
            autoCorrect={false}
          />
          {showDropdown && suggestions.length > 0 && (
            <View style={f.dropdown}>
              {suggestions.map(sug => (
                <TouchableOpacity key={sug} style={f.dropItem} onPress={() => { onChangeText(sug); setShowDropdown(false); }}>
                  <Text style={f.dropText}>{sug}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

function GearTab({ build, update }: { build: Build; update: (p: Partial<Build>) => void }) {
  function setGear(slot: string, patch: Partial<GearPiece>) {
    const gear = build.gear.map(g => g.slot === slot ? { ...g, ...patch } : g);
    update({ gear });
  }

  return (
    <ScrollView style={s.tab1} contentContainerStyle={s.tabContent}>
      {GEAR_SLOTS.map(slot => {
        const piece = build.gear.find(g => g.slot === slot) ?? { slot, setName: '', weight: '', trait: '', enchant: '', quality: 'Epic' };
        const isOffHand   = OFF_HAND_SLOTS.has(slot);
        const isMainHand  = MAIN_HAND_SLOTS.has(slot);
        const isJewelry   = JEWELRY_SLOTS.has(slot);
        const isWeapon    = WEAPON_SLOTS.has(slot);
        const [exp, setExp] = useState(false);
        return (
          <View key={slot} style={s.gearCard}>
            <TouchableOpacity style={s.gearCardHeader} onPress={() => setExp(!exp)}>
              <Text style={s.gearCardSlot}>{slot}</Text>
              {piece.setName ? <Text style={s.gearCardSet} numberOfLines={1}>{piece.setName}</Text> : null}
              <Text style={s.gearCardChev}>{exp ? '▴' : '▾'}</Text>
            </TouchableOpacity>
            {exp && (
              <View style={s.gearCardBody}>
                <Field label="Set Name" value={piece.setName} onChangeText={v => setGear(slot, { setName: v })} />
                {isMainHand
                  ? <Picker label="Weapon Type" value={piece.weight} options={['', ...WEAPON_TYPES]} onSelect={v => setGear(slot, { weight: v })} />
                  : isOffHand
                  ? <Picker label="Off-hand" value={piece.weight} options={OFF_HAND_WEIGHTS} onSelect={v => setGear(slot, { weight: v })} />
                  : !isJewelry
                  ? <Picker label="Weight" value={piece.weight} options={['', ...ARMOR_WEIGHTS]} onSelect={v => setGear(slot, { weight: v })} />
                  : null}
                <Picker
                  label="Trait" value={piece.trait}
                  options={['', ...(isJewelry ? JEWELRY_TRAITS : isWeapon ? WEAPON_TRAITS : ARMOR_TRAITS)]}
                  onSelect={v => setGear(slot, { trait: v })}
                />
                <AutocompleteField
                  label="Enchant" value={piece.enchant} onChangeText={v => setGear(slot, { enchant: v })}
                  candidates={isJewelry ? JEWELRY_ENCHANTS : isWeapon ? WEAPON_ENCHANTS : ARMOR_ENCHANTS}
                />
                <Picker label="Quality" value={piece.quality} options={QUALITY_TIERS} onSelect={v => setGear(slot, { quality: v })} />
              </View>
            )}
          </View>
        );
      })}
    </ScrollView>
  );
}

function StatsTab({ build, update }: { build: Build; update: (p: Partial<Build>) => void }) {
  function setCpSlot(i: number, v: string) {
    const slots = [...build.cpSlots];
    while (slots.length <= i) slots.push('');
    slots[i] = v;
    update({ cpSlots: slots });
  }
  return (
    <ScrollView style={s.tab1} contentContainerStyle={s.tabContent}>
      <Text style={s.subHeader}>Attribute Points</Text>
      <Field label="Health"  value={String(build.attributeHealth)}  onChangeText={v => update({ attributeHealth: parseInt(v) || 0 })} keyboardType="numeric" />
      <Field label="Magicka" value={String(build.attributeMagicka)} onChangeText={v => update({ attributeMagicka: parseInt(v) || 0 })} keyboardType="numeric" />
      <Field label="Stamina" value={String(build.attributeStamina)} onChangeText={v => update({ attributeStamina: parseInt(v) || 0 })} keyboardType="numeric" />
      <Text style={s.subHeader}>Buffs</Text>
      <Picker label="Mundus Stone" value={build.mundusStone} options={['', ...MUNDUS_STONES]} onSelect={v => update({ mundusStone: v })} />
      <Field label="Food / Drink Buff" value={build.foodBuff} onChangeText={v => update({ foodBuff: v })} />
      <Text style={s.subHeader}>Champion Points</Text>
      <Field label="CP Notes" value={build.championPoints} onChangeText={v => update({ championPoints: v })} multiline />
      {CP_TREE_LABELS.map((tree, ti) => (
        <View key={tree} style={{ marginBottom: spacing.md }}>
          <Text style={s.treeLabel}>{tree}</Text>
          {[0,1,2,3].map(i => (
            <Field
              key={i}
              label={`Star ${i + 1}`}
              value={build.cpSlots[ti * 4 + i] ?? ''}
              onChangeText={v => setCpSlot(ti * 4 + i, v)}
            />
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

function PassivesTab({ build, update }: { build: Build; update: (p: Partial<Build>) => void }) {
  const options = useMemo(() => getClassMasteries(build.esoClass), [build.esoClass]);

  if (!options.length) return (
    <View style={s.emptyState}>
      <Text style={s.emptyText}>Select a class in the Info tab to see passives.</Text>
    </View>
  );

  function toggle(name: string) {
    const cur = build.classMasteries;
    update({ classMasteries: cur.includes(name) ? cur.filter(m => m !== name) : [...cur, name] });
  }

  return (
    <ScrollView style={s.tab1} contentContainerStyle={s.tabContent}>
      <Text style={s.subHeader}>{build.esoClass} Class Mastery</Text>
      {options.map(name => (
        <TouchableOpacity key={name} style={s.checkRow} onPress={() => toggle(name)}>
          <View style={[s.checkbox, build.classMasteries.includes(name) && s.checkboxOn]}>
            {build.classMasteries.includes(name) && <Text style={s.checkmark}>✓</Text>}
          </View>
          <Text style={s.checkLabel}>{name}</Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

function NotesTab({ build, update }: { build: Build; update: (p: Partial<Build>) => void }) {
  return (
    <TextInput
      style={s.notesInput}
      value={build.notes}
      onChangeText={v => update({ notes: v })}
      multiline
      placeholder="Notes..."
      placeholderTextColor={colors.textSecondary}
    />
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: colors.background },
  tabBar:      { maxHeight: 44, borderBottomWidth: 1, borderBottomColor: colors.border },
  tabBarContent: { paddingHorizontal: spacing.sm },
  tab:         { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, marginHorizontal: 2 },
  tabActive:   { borderBottomWidth: 2, borderBottomColor: colors.primary },
  tabText:     { fontSize: font.sm, color: colors.textSecondary },
  tabTextActive: { color: colors.primary, fontWeight: '700' },
  tab1:        { flex: 1 },
  tabContent:  { padding: spacing.md, paddingBottom: spacing.xl },
  barHeader:   { fontSize: font.sm, fontWeight: '700', color: colors.primary, marginBottom: spacing.sm, letterSpacing: 1 },
  skillSlotRow: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.sm },
  slotIcon:    { width: 40, height: 40, borderRadius: 3, backgroundColor: colors.surfaceAlt, marginTop: 2 },
  gearCard:    { backgroundColor: colors.surface, borderRadius: radius.md, marginBottom: spacing.sm, borderWidth: 1, borderColor: colors.border, overflow: 'hidden' },
  gearCardHeader: { flexDirection: 'row', alignItems: 'center', padding: spacing.sm },
  gearCardSlot: { fontSize: font.sm, fontWeight: '700', color: colors.text, width: 90 },
  gearCardSet: { flex: 1, fontSize: font.sm, color: colors.textSecondary },
  gearCardChev: { color: colors.textSecondary, marginLeft: spacing.sm },
  gearCardBody: { padding: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border },
  subHeader:   { fontSize: font.sm, fontWeight: '700', color: colors.primary, marginBottom: spacing.sm, marginTop: spacing.sm },
  treeLabel:   { fontSize: font.xs, color: colors.textSecondary, fontWeight: '600', marginBottom: 4 },
  emptyState:  { flex: 1, alignItems: 'center', justifyContent: 'center', padding: spacing.xl },
  emptyText:   { color: colors.textSecondary, textAlign: 'center', fontSize: font.md },
  checkRow:    { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, gap: spacing.sm },
  checkbox:    { width: 22, height: 22, borderRadius: 4, borderWidth: 2, borderColor: colors.border, alignItems: 'center', justifyContent: 'center' },
  checkboxOn:  { backgroundColor: colors.primary, borderColor: colors.primary },
  checkmark:   { color: colors.background, fontSize: font.sm, fontWeight: '700' },
  checkLabel:  { fontSize: font.md, color: colors.text, flex: 1 },
  notesInput:  { flex: 1, padding: spacing.md, fontSize: font.md, color: colors.text, textAlignVertical: 'top', backgroundColor: colors.background },
});
