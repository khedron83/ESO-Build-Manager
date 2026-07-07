import React from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, Alert } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { RootStackParamList } from '../types';
import { colors, spacing, radius, font } from '../theme';
import { useSettings } from '../hooks/useSettings';

type Props = NativeStackScreenProps<RootStackParamList, 'Settings'>;

export default function SettingsScreen({ navigation }: Props) {
  const { config, saveConfig } = useSettings();
  const [url,      setUrl]      = React.useState(config.url);
  const [username, setUsername] = React.useState(config.username);
  const [password, setPassword] = React.useState(config.password);

  // keep local state in sync if hook loads async
  React.useEffect(() => {
    setUrl(config.url);
    setUsername(config.username);
    setPassword(config.password);
  }, [config.url, config.username, config.password]);

  async function handleSave() {
    await saveConfig({ url: url.trim(), username: username.trim(), password });
    Alert.alert('Saved', 'Server settings saved.', [{ text: 'OK', onPress: () => navigation.goBack() }]);
  }

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content}>
      <Text style={s.header}>Nextcloud Server</Text>
      <Text style={s.hint}>Builds are synced via WebDAV to a file in your Nextcloud Files.</Text>

      <Text style={s.label}>Server URL</Text>
      <TextInput
        style={s.input}
        value={url}
        onChangeText={setUrl}
        placeholder="https://cloud.example.com"
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
      />

      <Text style={s.label}>Username</Text>
      <TextInput
        style={s.input}
        value={username}
        onChangeText={setUsername}
        placeholder="username"
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
        autoCorrect={false}
      />

      <Text style={s.label}>Password / App password</Text>
      <TextInput
        style={s.input}
        value={password}
        onChangeText={setPassword}
        placeholder="••••••••"
        placeholderTextColor={colors.textSecondary}
        secureTextEntry
        autoCapitalize="none"
        autoCorrect={false}
      />

      <TouchableOpacity style={s.btn} onPress={handleSave}>
        <Text style={s.btnText}>Save</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  content:   { padding: spacing.md, paddingBottom: spacing.xl },
  header:    { fontSize: font.lg, fontWeight: '700', color: colors.primary, marginBottom: spacing.xs },
  hint:      { fontSize: font.sm, color: colors.textSecondary, marginBottom: spacing.lg },
  label:     { fontSize: font.xs, color: colors.textSecondary, marginBottom: 4, letterSpacing: 0.5 },
  input: {
    backgroundColor: colors.surface, borderRadius: radius.sm, padding: spacing.sm,
    fontSize: font.sm, color: colors.text, borderWidth: 1, borderColor: colors.border,
    marginBottom: spacing.md,
  },
  btn: {
    backgroundColor: colors.primary, borderRadius: radius.md,
    padding: spacing.md, alignItems: 'center', marginTop: spacing.sm,
  },
  btnText: { color: colors.background, fontSize: font.md, fontWeight: '700' },
});
