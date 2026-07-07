import React from 'react';
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert, Image,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList, Build, GearPiece } from '../types';
import { colors, spacing, radius, font } from '../theme';
import { GEAR_SLOTS, CP_TREE_LABELS, QUALITY_COLORS, ROLE_COLORS } from '../data/constants';
import { skillIconUrl } from '../utils/skillData';
import * as storage from '../utils/storage';
import { useEffect, useState } from 'react';

type Props = NativeStackScreenProps<RootStackParamList, 'BuildDetail'>;

export default function BuildDetailScreen({ route, navigation }: Props) {
  const [build, setBuild] = useState<Build | null>(null);

  useEffect(() => {
    storage.getBuild(route.params.buildId).then(b => {
      if (b) {
        setBuild(b);
        navigation.setOptions({
          title: b.name,
          headerRight: () => (
            <TouchableOpacity onPress={() => navigation.navigate('BuildEditor', { buildId: b.id })} style={{ marginRight: spacing.sm }}>
              <Text style={{ color: colors.primary, fontSize: font.md }}>Edit</Text>
            </TouchableOpacity>
          ),
        });
      }
    });
  }, [route.params.buildId]);

  if (!build) return null;

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      <BuildSheet build={build} />
    </ScrollView>
  );
}

export function BuildSheet({ build }: { build: Build }) {
  const tags = [
    build.esoClass,
    build.subclass1 ? `(${[build.subclass1, build.subclass2].filter(Boolean).join(' / ')})` : '',
    build.role, build.content, build.gamePatch,
  ].filter(Boolean);

  return (
    <View>
      {/* Badges */}
      <View style={s.badgeRow}>
        {tags.map((t, i) => (
          <View key={i} style={s.badge}>
            <Text style={[s.badgeText, t === build.role ? { color: ROLE_COLORS[build.role] ?? colors.primary } : {}]}>{t}</Text>
          </View>
        ))}
      </View>
      {build.source ? <Text style={s.source}>Source: {build.source}</Text> : null}

      <Divider />

      {/* Skills */}
      <Section title="Skills" />
      {[0, 1].map(bar => {
        const barLabel = bar === 0 ? 'Front Bar' : 'Back Bar';
        const barSkills = Object.fromEntries(
          build.skills.filter(s => s.bar === bar).map(s => [s.slot, s.name])
        );
        return (
          <View key={bar} style={{ marginBottom: spacing.md }}>
            <Text style={s.barLabel}>{barLabel}</Text>
            <View style={s.skillRow}>
              {[0,1,2,3,4].map(slot => (
                <SkillChip key={slot} name={barSkills[slot] ?? ''} />
              ))}
            </View>
            <View style={s.ultRow}>
              <Text style={s.ultLabel}>Ult</Text>
              <SkillChip name={barSkills[5] ?? ''} wide />
            </View>
          </View>
        );
      })}

      {/* Champion Points */}
      {build.cpSlots.some(Boolean) && (
        <>
          <Divider />
          <Section title="Champion Points" />
          {build.championPoints ? <Text style={s.cpNotes}>{build.championPoints}</Text> : null}
          {CP_TREE_LABELS.map((tree, ti) => (
            <View key={tree} style={{ marginBottom: spacing.sm }}>
              <Text style={s.treeLabel}>{tree}</Text>
              <View style={s.cpRow}>
                {[0,1,2,3].map(i => {
                  const slot = build.cpSlots[ti * 4 + i] ?? '';
                  return (
                    <View key={i} style={s.cpChip}>
                      <Text style={s.cpChipText} numberOfLines={2}>{slot || '—'}</Text>
                    </View>
                  );
                })}
              </View>
            </View>
          ))}
        </>
      )}

      <Divider />

      {/* Gear */}
      <Section title="Gear" />
      {GEAR_SLOTS.map(slot => {
        const piece = build.gear.find(g => g.slot === slot);
        return <GearRow key={slot} slot={slot} piece={piece} />;
      })}

      <Divider />

      {/* Stats */}
      <Section title="Stats & Buffs" />
      <View style={s.statRow}>
        <StatPill label="Health"  value={build.attributeHealth}  color="#f87171" />
        <StatPill label="Magicka" value={build.attributeMagicka} color="#60a5fa" />
        <StatPill label="Stamina" value={build.attributeStamina} color="#4ade80" />
      </View>
      {build.foodBuff    ? <LabeledValue label="Food"   value={build.foodBuff} /> : null}
      {build.mundusStone ? <LabeledValue label="Mundus" value={build.mundusStone} /> : null}

      {/* Passives */}
      {build.classMasteries.length > 0 && (
        <>
          <Divider />
          <Section title="Passives" />
          {build.classMasteries.map(m => (
            <Text key={m} style={s.passive}>✓  {m}</Text>
          ))}
        </>
      )}

      {/* Notes */}
      {build.notes ? (
        <>
          <Divider />
          <Section title="Notes" />
          <Text style={s.notes}>{build.notes}</Text>
        </>
      ) : null}
    </View>
  );
}

function SkillChip({ name, wide }: { name: string; wide?: boolean }) {
  const empty = !name;
  const url = empty ? null : skillIconUrl(name);
  return (
    <View style={[s.skillChip, wide && s.skillChipWide, empty && s.skillChipEmpty]}>
      {url && <Image source={{ uri: url }} style={s.skillIcon} />}
      <Text style={[s.skillName, empty && { color: colors.textSecondary }]} numberOfLines={2}>
        {name || '—'}
      </Text>
    </View>
  );
}

function GearRow({ slot, piece }: { slot: string; piece?: GearPiece }) {
  const parts = [
    piece?.setName,
    piece?.weight && piece.weight !== '—' && piece.weight !== 'N/A' ? piece.weight : null,
    piece?.trait,
    piece?.enchant?.replace(/^Maximum /, ''),
    piece?.quality && piece.quality !== 'Epic' ? piece.quality : null,
  ].filter(Boolean);
  const qualColor = piece?.quality ? QUALITY_COLORS[piece.quality] : undefined;
  return (
    <View style={s.gearRow}>
      <Text style={s.gearSlot}>{slot}</Text>
      {piece?.weight === 'N/A'
        ? <Text style={s.gearValue}>N/A (two-handed)</Text>
        : <Text style={[s.gearValue, qualColor ? { color: qualColor } : {}]} numberOfLines={1}>
            {parts.length ? parts.join('  ·  ') : '—'}
          </Text>
      }
    </View>
  );
}

function Section({ title }: { title: string }) {
  return <Text style={s.sectionTitle}>{title}</Text>;
}

function Divider() {
  return <View style={s.divider} />;
}

function StatPill({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={s.statPill}>
      <Text style={[s.statValue, { color }]}>{value}</Text>
      <Text style={s.statLabel}>{label}</Text>
    </View>
  );
}

function LabeledValue({ label, value }: { label: string; value: string }) {
  return (
    <View style={s.labeledRow}>
      <Text style={s.labeledKey}>{label}:</Text>
      <Text style={s.labeledVal}>{value}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  badgeRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.sm },
  badge: { backgroundColor: colors.surfaceAlt, borderRadius: radius.sm, paddingHorizontal: spacing.sm, paddingVertical: 3 },
  badgeText: { fontSize: font.xs, color: colors.text },
  source: { fontSize: font.xs, color: colors.textSecondary, marginBottom: spacing.sm },
  divider: { height: 1, backgroundColor: colors.border, marginVertical: spacing.md },
  sectionTitle: { fontSize: font.sm, fontWeight: '700', color: colors.primary, marginBottom: spacing.sm, letterSpacing: 1 },
  barLabel: { fontSize: font.xs, color: colors.textSecondary, fontWeight: '600', marginBottom: spacing.xs, letterSpacing: 1 },
  skillRow: { flexDirection: 'row', gap: spacing.xs, marginBottom: spacing.xs },
  ultRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  ultLabel: { fontSize: font.xs, color: colors.textSecondary, width: 24 },
  skillChip: {
    flex: 1, backgroundColor: colors.surface, borderRadius: radius.sm,
    padding: spacing.xs, alignItems: 'center', borderWidth: 1, borderColor: colors.border,
  },
  skillChipWide: { flex: 1 },
  skillChipEmpty: { borderStyle: 'dashed', borderColor: colors.border },
  skillIcon: { width: 40, height: 40, borderRadius: 3, marginBottom: 2 },
  skillName: { fontSize: font.xs, color: colors.text, textAlign: 'center' },
  cpNotes: { fontSize: font.sm, color: colors.textSecondary, marginBottom: spacing.sm },
  treeLabel: { fontSize: font.xs, color: colors.textSecondary, fontWeight: '600', marginBottom: 4, letterSpacing: 1 },
  cpRow: { flexDirection: 'row', gap: spacing.xs },
  cpChip: { flex: 1, backgroundColor: colors.surface, borderRadius: radius.sm, padding: spacing.xs, borderWidth: 1, borderColor: colors.border },
  cpChipText: { fontSize: font.xs, color: colors.text, textAlign: 'center' },
  gearRow: { flexDirection: 'row', paddingVertical: 5, borderBottomWidth: 0.5, borderBottomColor: colors.border },
  gearSlot: { width: 90, fontSize: font.xs, color: colors.textSecondary },
  gearValue: { flex: 1, fontSize: font.xs, color: colors.text },
  statRow: { flexDirection: 'row', gap: spacing.xl, marginBottom: spacing.sm },
  statPill: { alignItems: 'center' },
  statValue: { fontSize: font.xl, fontWeight: '700' },
  statLabel: { fontSize: font.xs, color: colors.textSecondary },
  labeledRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: 4 },
  labeledKey: { fontSize: font.sm, color: colors.textSecondary, width: 56 },
  labeledVal: { fontSize: font.sm, color: colors.text, flex: 1 },
  passive: { fontSize: font.sm, color: colors.text, marginBottom: 4 },
  notes: { fontSize: font.sm, color: colors.text, lineHeight: 20 },
});
