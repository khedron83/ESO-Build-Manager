import React, { useState, useMemo } from 'react';
import {
  View, Text, TextInput, FlatList, TouchableOpacity,
  StyleSheet, ActivityIndicator, Alert,
} from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList, Character } from '../types';
import { colors, spacing, radius, font } from '../theme';
import { useCharacters } from '../hooks/useCharacters';
import { useSettings } from '../hooks/useSettings';
import { syncCharacters } from '../utils/characterSync';

type Props = NativeStackScreenProps<RootStackParamList, 'Characters'>;

export default function CharactersScreen({ navigation }: Props) {
  const { characters, loaded, refresh } = useCharacters();
  const { config } = useSettings();
  const [query, setQuery] = useState('');
  const [accountFilter, setAccountFilter] = useState('');
  const [syncing, setSyncing] = useState(false);

  const accounts = useMemo(
    () => [...new Set(characters.map(c => c.account).filter(Boolean))].sort(),
    [characters],
  );

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return characters.filter(c => {
      const matchAccount = !accountFilter || c.account === accountFilter;
      const matchQ = !q || c.name.toLowerCase().includes(q) || c.class_name.toLowerCase().includes(q);
      return matchAccount && matchQ;
    }).sort((a, b) => a.name.localeCompare(b.name));
  }, [characters, query, accountFilter]);

  async function handleSync() {
    if (!config.url) { Alert.alert('No server configured', 'Add Nextcloud details in Settings.'); return; }
    setSyncing(true);
    try {
      const result = await syncCharacters(config);
      await refresh();
      const msg = `↓ ${result.downloaded} characters` +
        (result.errors.length ? `\n${result.errors.join('\n')}` : '');
      Alert.alert('Sync complete', msg);
    } catch (e) {
      Alert.alert('Sync error', String(e));
    } finally {
      setSyncing(false);
    }
  }

  if (!loaded) return <ActivityIndicator style={s.loader} color={colors.primary} />;

  return (
    <View style={s.container}>
      <View style={s.topRow}>
        <TextInput
          style={s.search}
          placeholder="Search characters..."
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
      </View>

      {accounts.length > 1 && (
        <View style={s.chipRow}>
          {['', ...accounts].map(acct => (
            <TouchableOpacity
              key={acct || 'all'}
              style={[s.chip, accountFilter === acct && s.chipActive]}
              onPress={() => setAccountFilter(acct)}
            >
              <Text style={[s.chipText, accountFilter === acct && { color: colors.background }]}>
                {acct || 'All Accounts'}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      <FlatList
        data={filtered}
        keyExtractor={c => c.name}
        contentContainerStyle={s.list}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={s.item}
            onPress={() => navigation.navigate('CharacterDetail', { name: item.name })}
            activeOpacity={0.7}
          >
            <View style={s.itemLeft}>
              <Text style={s.itemName} numberOfLines={1}>{item.name}</Text>
              <View style={s.itemMeta}>
                {item.class_name ? <Text style={s.badge}>{item.class_name}</Text> : null}
                {item.race_name ? <Text style={s.badge}>{item.race_name}</Text> : null}
                <Text style={s.badge}>CP {item.champion_points}</Text>
              </View>
            </View>
            <View style={s.dailyDots}>
              <View style={[s.dot, { backgroundColor: item.daily_dungeon_done ? colors.success : colors.error }]} />
              <View style={[s.dot, { backgroundColor: item.daily_writs_done ? colors.success : colors.error }]} />
            </View>
            <Text style={s.arrow}>›</Text>
          </TouchableOpacity>
        )}
        ItemSeparatorComponent={() => <View style={s.sep} />}
        ListEmptyComponent={
          <Text style={s.empty}>{loaded ? 'No characters synced yet.\nTap ⇅ to sync from Nextcloud.' : ''}</Text>
        }
      />
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
  chipRow: { flexDirection: 'row', paddingHorizontal: spacing.md, paddingBottom: spacing.sm, gap: spacing.xs, flexWrap: 'wrap' },
  chip: { paddingHorizontal: spacing.sm, paddingVertical: spacing.xs, borderRadius: radius.full, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface },
  chipActive: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipText: { fontSize: font.xs, color: colors.text },
  list: { padding: spacing.md, paddingTop: 0, paddingBottom: 80 },
  item: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface, padding: spacing.md, borderRadius: radius.md },
  itemLeft: { flex: 1 },
  itemName: { fontSize: font.md, fontWeight: '700', color: colors.text },
  itemMeta: { flexDirection: 'row', gap: spacing.sm, marginTop: 4 },
  badge: { fontSize: font.xs, color: colors.textSecondary },
  dailyDots: { flexDirection: 'row', gap: 4, marginRight: spacing.sm },
  dot: { width: 8, height: 8, borderRadius: 4 },
  arrow: { fontSize: font.xl, color: colors.border, marginLeft: spacing.xs },
  sep: { height: spacing.xs },
  empty: { textAlign: 'center', color: colors.textSecondary, marginTop: spacing.xl, fontSize: font.md },
});
