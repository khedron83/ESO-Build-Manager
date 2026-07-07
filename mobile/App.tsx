import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { RootStackParamList } from './src/types';
import { colors, font } from './src/theme';
import BuildsScreen     from './src/screens/BuildsScreen';
import BuildDetailScreen from './src/screens/BuildDetailScreen';
import BuildEditorScreen from './src/screens/BuildEditorScreen';
import SettingsScreen   from './src/screens/SettingsScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

const navTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background:   colors.background,
    card:         colors.surface,
    text:         colors.text,
    border:       colors.border,
    primary:      colors.primary,
    notification: colors.primary,
  },
};

export default function App() {
  return (
    <NavigationContainer theme={navTheme}>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle:     { backgroundColor: colors.surface },
          headerTintColor: colors.primary,
          headerTitleStyle: { fontWeight: '700', fontSize: font.md, color: colors.text },
        }}
      >
        <Stack.Screen name="Builds"      component={BuildsScreen}      options={{ title: 'ESO Builds' }} />
        <Stack.Screen name="BuildDetail" component={BuildDetailScreen} options={{ title: '' }} />
        <Stack.Screen name="BuildEditor" component={BuildEditorScreen} options={{ title: 'Build' }} />
        <Stack.Screen name="Settings"    component={SettingsScreen}    options={{ title: 'Settings' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
