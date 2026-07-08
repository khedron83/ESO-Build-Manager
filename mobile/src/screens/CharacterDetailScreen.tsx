import React, { useEffect, useState } from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList, Character } from '../types';
import { colors, spacing, radius, font } from '../theme';
import * as characterStorage from '../utils/characterStorage';

type Props = NativeStackScreenProps<RootStackParamList, 'CharacterDetail'>;

function fmtNum(n: number): string {
  return n.toLocaleString();
}

function fmtAgo(unixSeconds: number): string {
  if (!unixSeconds) return 'Unknown';
  const deltaMs = Date.now() - unixSeconds * 1000;
  const mins = Math.floor(deltaMs / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function CharacterDetailScreen({ route, navigation }: Props) {
  const [char, setChar] = useState<Character | null>(null);

  useEffect(() => {
    characterStorage.getCharacter(route.params.name).then(c => {
      if (c) {
        setChar(c);
        navigation.setOptions({ title: c.name });
      }
    });
  }, [route.params.name]);

  if (!char) return null;

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      {/* Badges */}
      <View style={s.badgeRow}>
        {[char.class_name, char.race_name, char.faction_name, char.account].filter(Boolean).map((t, i) => (
          <View key={i} style={s.badge}><Text style={s.badgeText}>{t}</Text></View>
        ))}
      </View>
      <Text style={s.updated}>Updated {fmtAgo(char.last_updated)}</Text>

      <Divider />

      {/* Dailies */}
      <Section title="Dailies" />
      <View style={s.dailyRow}>
        <DailyPill label="Random Dungeon" done={char.daily_dungeon_done} />
        <DailyPill label="Writs" done={char.daily_writs_done} />
      </View>

      <Divider />

      {/* Bio */}
      <Section title="Bio" />
      <View style={s.statGrid}>
        <StatPill label="Level" value={fmtNum(char.level)} />
        <StatPill label="Champion Points" value={fmtNum(char.champion_points)} />
        <StatPill label="Alliance Rank" value={fmtNum(char.alliance_rank)} />
        <StatPill label="Skill Points" value={fmtNum(char.skill_points_unspent)} />
      </View>

      <Divider />

      {/* Stats */}
      <Section title="Stats" />
      <View style={s.statGrid}>
        <StatPill label="Health" value={fmtNum(char.health_max)} color={colors.error} />
        <StatPill label="Magicka" value={fmtNum(char.magicka_max)} color="#4a9eff" />
        <StatPill label="Stamina" value={fmtNum(char.stamina_max)} color={colors.success} />
        <StatPill label="Spell Dmg" value={fmtNum(char.spell_damage)} />
        <StatPill label="Weapon Dmg" value={fmtNum(char.weapon_damage)} />
        <StatPill label="Crit" value={`${char.crit_chance.toFixed(1)}%`} />
        <StatPill label="Phys Res" value={fmtNum(char.resist_physical)} />
        <StatPill label="Spell Res" value={fmtNum(char.resist_spell)} />
      </View>

      <Divider />

      {/* Currencies */}
      <Section title="Currencies (on person)" />
      <CurrencyRows data={char.currencies} />
      <Text style={[s.sectionTitle, { marginTop: spacing.md }]}>Bank (account-wide)</Text>
      <CurrencyRows data={char.bank_currencies} />

      <Divider />

      {/* Champion Points */}
      {char.constellations.length > 0 && (
        <>
          <Section title="Champion Points" />
          {char.constellations.map(con => (
            <LabeledValue key={con.name} label={con.name} value={fmtNum(con.spent)} />
          ))}
          <Divider />
        </>
      )}

      {/* Inventory */}
      <Section title={`Inventory (${char.bag_used}/${char.bag_size})`} />
      <LabeledValue label="Soul Gems (filled)" value={fmtNum(char.soul_gems_filled)} />
      <LabeledValue label="Soul Gems (empty)" value={fmtNum(char.soul_gems_empty)} />
      {char.inventory.slice(0, 30).map((item, i) => (
        <LabeledValue key={i} label={item.name} value={fmtNum(item.count)} />
      ))}
      {char.inventory.length > 30 && (
        <Text style={s.updated}>+ {char.inventory.length - 30} more items</Text>
      )}
    </ScrollView>
  );
}

function Section({ title }: { title: string }) {
  return <Text style={s.sectionTitle}>{title}</Text>;
}

function Divider() {
  return <View style={s.divider} />;
}

function StatPill({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <View style={s.statPill}>
      <Text style={[s.statValue, color ? { color } : null]}>{value}</Text>
      <Text style={s.statLabel}>{label}</Text>
    </View>
  );
}

function LabeledValue({ label, value }: { label: string; value: string }) {
  return (
    <View style={s.labeledRow}>
      <Text style={s.labeledLabel}>{label}</Text>
      <Text style={s.labeledValue}>{value}</Text>
    </View>
  );
}

function DailyPill({ label, done }: { label: string; done: boolean }) {
  return (
    <View style={[s.dailyPill, { borderColor: done ? colors.success : colors.error }]}>
      <Text style={[s.dailyStatus, { color: done ? colors.success : colors.error }]}>
        {done ? 'Done' : 'Not yet'}
      </Text>
      <Text style={s.dailyLabel}>{label}</Text>
    </View>
  );
}

function CurrencyRows({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).filter(([, v]) => v);
  if (entries.length === 0) return <Text style={s.labeledLabel}>—</Text>;
  return (
    <>
      {entries.map(([name, value]) => (
        <LabeledValue key={name} label={name} value={fmtNum(value)} />
      ))}
    </>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs },
  badge: { backgroundColor: colors.surface, borderRadius: radius.full, paddingHorizontal: spacing.sm, paddingVertical: 4, borderWidth: 1, borderColor: colors.border },
  badgeText: { fontSize: font.xs, color: colors.textSecondary },
  updated: { fontSize: font.xs, color: colors.textSecondary, marginTop: spacing.xs },
  divider: { height: 1, backgroundColor: colors.border, marginVertical: spacing.md },
  sectionTitle: { fontSize: font.sm, fontWeight: '700', color: colors.primary, textTransform: 'uppercase', letterSpacing: 1, marginBottom: spacing.sm },
  dailyRow: { flexDirection: 'row', gap: spacing.sm },
  dailyPill: { flex: 1, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, alignItems: 'center' },
  dailyStatus: { fontSize: font.md, fontWeight: '700' },
  dailyLabel: { fontSize: font.xs, color: colors.textSecondary, marginTop: 2 },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  statPill: { backgroundColor: colors.surface, borderRadius: radius.md, padding: spacing.sm, minWidth: 90, alignItems: 'center' },
  statValue: { fontSize: font.lg, fontWeight: '700', color: colors.text },
  statLabel: { fontSize: font.xs, color: colors.textSecondary, marginTop: 2 },
  labeledRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  labeledLabel: { fontSize: font.sm, color: colors.textSecondary },
  labeledValue: { fontSize: font.sm, color: colors.text, fontWeight: '600' },
});
