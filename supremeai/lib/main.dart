import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'providers/settings_provider.dart';
import 'providers/orchestration_provider.dart';
import 'screens/login_screen.dart';
import 'screens/dashboard/home_screen.dart';

import 'services/localization_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LocalizationService.load('bn'); // Default to Bengali
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => SettingsProvider()),
        ChangeNotifierProvider(create: (_) => OrchestrationProvider()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  ThemeMode _getThemeMode(String mode) {
    switch (mode) {
      case 'light':
        return ThemeMode.light;
      case 'dark':
        return ThemeMode.dark;
      default:
        return ThemeMode.system;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<SettingsProvider>(
      builder: (context, settings, _) {
        return Semantics(
          container: true,
          label: 'SupremeAI Application',
          child: MaterialApp(
            title: 'SupremeAI',
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
              useMaterial3: true,
            ),
            darkTheme: ThemeData(
              colorScheme: ColorScheme.fromSeed(
                seedColor: Colors.deepPurple,
                brightness: Brightness.dark,
              ),
              useMaterial3: true,
            ),
            themeMode: _getThemeMode(settings.settings.themeMode),
            home: Consumer<AuthProvider>(
              builder: (context, auth, _) {
                if (auth.status == AuthStatus.authenticated ||
                    auth.status == AuthStatus.guest) {
                  return const HomeScreen();
                }
                return const LoginScreen();
              },
            ),
          ),
        );
      },
    );
  }
}

