import React, { useState, useMemo, useContext } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  StyleSheet, ActivityIndicator, Alert,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList, Build } from '../types';
import { colors, spacing, radius, font } from '../theme';
import { ROLES, ROLE_COLORS } from '../data/constants';
import { useBuilds } from '../hooks/useBuilds';
import { useSettings } from '../hooks/useSettings';
import { sync } from '../utils/sync';
import * as storage from '../utils/storage';

type Props = NativeStackScreenProps<RootStackParamList, 'Builds'>;

export default function BuildsScreen({ navigation }: Props) {
  const { builds, loaded, deleteBuild, importBuild, refresh } = useBuilds();
  const { config } = useSettings();
  const [query, setQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [syncing, setSyncing] = useState(false);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return builds.filter(b => {
      const matchRole = !roleFilter || b.role === roleFilter;
      const matchQ = !q || b.name.toLowerCase().includes(q) || b.esoClass.toLowerCase().includes(q);
      return matchRole && matchQ;
    }).sort((a, b) => a.name.localeCompare(b.name));
  }, [builds, query, roleFilter]);

  async function handleSync() {
    if (!config.url) { Alert.alert('No server configured', 'Add Nextcloud details in Settings.'); return; }
    setSyncing(true);
    try {
      const result = await sync(config);
      await refresh();
      const msg = `↑ ${result.uploaded}  ↓ ${result.downloaded}` +
        (result.errors.length ? `\n${result.errors.join('\n')}` : '');
      Alert.alert('Sync complete', msg);
    } catch (e) {
      Alert.alert('Sync error', String(e));
    } finally {
      setSyncing(false);
    }
  }

  function confirmDelete(build: Build) {
    Alert.alert('Delete build?', build.name, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => deleteBuild(build.id) },
    ]);
  }

  if (!loaded) return <ActivityIndicator style={s.loader} color={colors.primary} />;

  return (
    <View style={s.container}>
      {/* Search + header row */}
      <View style={s.topRow}>
        <TextInput
          style={s.search}
          placeholder="Search builds..."
          placeholderTextColor={colors.textSecondary}
          value={query}
          onChangeText={setQuery}
          autoCapitalize="none"
          autoCorrect={false}
          clearButtonMode="while-editing"
        />
        <TouchableOpacity style={s.iconBtn} onPress={handleSync} disabled={syncing}>
          {syncing ? <ActivityIndicator size="small" color={colors.primary} /> :
            <Text style={s.iconBtnText}>⇅</Text>}
        </TouchableOpacity>
        <TouchableOpacity style={s.iconBtn} onPress={() => navigation.navigate('Settings')}>
          <Text style={s.iconBtnText}>⚙</Text>
        </TouchableOpacity>
      </View>

      {/* Role filter chips */}
      <View style={s.chipRow}>
        {['', ...ROLES].map(role => (
          <TouchableOpacity
            key={role || 'all'}
            style={[s.chip, roleFilter === role && s.chipActive]}
            onPress={() => setRoleFilter(role)}
          >
            <Text style={[s.chipText, roleFilter === role && { color: colors.background }]}>
              {role || 'All'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={filtered}
        keyExtractor={b => b.id}
        contentContainerStyle={s.list}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={s.item}
            onPress={() => navigation.navigate('BuildDetail', { buildId: item.id })}
            onLongPress={() => confirmDelete(item)}
            activeOpacity={0.7}
          >
            <View style={s.itemLeft}>
              <Text style={s.itemName} numberOfLines={1}>{item.name}</Text>
              <View style={s.itemMeta}>
                {item.esoClass ? <Text style={s.badge}>{item.esoClass}</Text> : null}
                {item.role ? (
                  <Text style={[s.badge, { color: ROLE_COLORS[item.role] ?? colors.textSecondary }]}>
                    {item.role}
                  </Text>
                ) : null}
                {item.gamePatch ? <Text style={s.badge}>{item.gamePatch}</Text> : null}
              </View>
            </View>
            <Text style={s.arrow}>›</Text>
          </TouchableOpacity>
        )}
        ItemSeparatorComponent={() => <View style={s.sep} />}
        ListEmptyComponent={
          <Text style={s.empty}>{loaded ? 'No builds yet.\nTap + to add one.' : ''}</Text>
        }
      />

      {/* FAB */}
      <TouchableOpacity
        style={s.fab}
        onPress={() => navigation.navigate('BuildEditor', { buildId: null })}
      >
        <Text style={s.fabText}>+</Text>
      </TouchableOpacity>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  loader: { flex: 1 },
  topRow: { flexDirection: 'row', alignItems: 'center', padding: spacing.md, paddingBottom: spacing.sm, gap: spacing.sm },
  search: {
    flex: 1, height: 40, backgroundColor: colors.surface, borderRadius: radius.full,
    paddingHorizontal: spacing.md, fontSize: font.md, color: colors.text,
    borderWidth: 1, borderColor: colors.border,
  },
  iconBtn: { width: 40, height: 40, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.surface, borderRadius: radius.full, borderWidth: 1, borderColor: colors.border },
  iconBtnText: { color: colors.primary, fontSize: font.lg },
  chipRow: { flexDirection: 'row', paddingHorizontal: spacing.md, paddingBottom: spacing.sm, gap: spacing.xs },
  chip: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: radius.full, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { fontSize: font.xs, color: colors.text },
  list: { padding: spacing.md, paddingTop: 0, paddingBottom: 80 },
  item: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface, padding: spacing.md, borderRadius: radius.md },
  itemLeft: { flex: 1 },
  itemName: { fontSize: font.md, fontWeight: '700', color: colors.text },
  itemMeta: { flexDirection: 'row', gap: spacing.sm, marginTop: 4 },
  badge: { fontSize: font.xs, color: colors.textSecondary },
  arrow: { fontSize: font.xl, color: colors.border, marginLeft: spacing.sm },
  sep: { height: spacing.xs },
  empty: { textAlign: 'center', color: colors.textSecondary, marginTop: spacing.xl, fontSize: font.md },
  fab: {
    position: 'absolute', bottom: spacing.xl, right: spacing.xl,
    width: 56, height: 56, borderRadius: 28,
    backgroundColor: colors.primary, alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOpacity: 0.4, shadowRadius: 8, elevation: 6,
  },
  fabText: { fontSize: 28, color: colors.background, fontWeight: '300', lineHeight: 32 },
});
