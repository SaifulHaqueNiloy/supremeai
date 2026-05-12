import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../providers/settings_provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _modelController = TextEditingController();
  final _smallModelController = TextEditingController();
  bool _fullAuthority = false;
  bool _externalDirectory = false;
  String _shareMode = 'manual';
  String _themeMode = 'system';

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();
      final settingsProvider = context.read<SettingsProvider>();
      await settingsProvider.loadFromBackend(authToken: auth.token);
      _bind(settingsProvider.settings);
    });
  }

  void _bind(SupremeAISettings settings) {
    _modelController.text = settings.model;
    _smallModelController.text = settings.smallModel;
    _fullAuthority = settings.fullAuthority;
    _externalDirectory = settings.enableExternalDirectory;
    _shareMode = settings.shareMode;
    _themeMode = settings.themeMode;
  }

  @override
  void dispose() {
    _modelController.dispose();
    _smallModelController.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final auth = context.read<AuthProvider>();
    final provider = context.read<SettingsProvider>();
    final current = provider.settings;

    provider.update(current.copyWith(
      model: _modelController.text.trim(),
      smallModel: _smallModelController.text.trim(),
      fullAuthority: _fullAuthority,
      shareMode: _shareMode,
      enableExternalDirectory: _externalDirectory,
      themeMode: _themeMode,
    ));

    if (_fullAuthority) provider.setFullAuthority(true);
    final ok = await provider.saveToBackend(authToken: auth.token);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(ok ? 'Settings saved' : 'Save failed')));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Consumer<SettingsProvider>(
        builder: (context, settingsProvider, _) {
          if (settingsProvider.isLoading && settingsProvider.settings.model.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _buildSection('AI Models', [
                TextField(
                  controller: _modelController,
                  decoration: const InputDecoration(labelText: 'Primary model', hintText: 'gemini-1.5-pro'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _smallModelController,
                  decoration: const InputDecoration(labelText: 'Small model', hintText: 'gemini-1.5-flash'),
                ),
              ]),
              const SizedBox(height: 16),
              _buildSection('App Settings', [
                DropdownButtonFormField<String>(
                  value: _shareMode,
                  items: const [
                    DropdownMenuItem(value: 'manual', child: Text('Manual share')),
                    DropdownMenuItem(value: 'auto', child: Text('Auto share')),
                    DropdownMenuItem(value: 'disabled', child: Text('Disabled')),
                  ],
                  onChanged: (v) => v != null ? setState(() => _shareMode = v) : null,
                  decoration: const InputDecoration(labelText: 'Share mode'),
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  title: const Text('Full authority mode'),
                  subtitle: const Text('Allow all core tools without confirmation'),
                  value: _fullAuthority,
                  onChanged: (v) => setState(() => _fullAuthority = v),
                ),
                SwitchListTile(
                  title: const Text('External directory access'),
                  subtitle: const Text('Access directories outside workspace'),
                  value: _externalDirectory,
                  onChanged: (v) => setState(() => _externalDirectory = v),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: _themeMode,
                  decoration: const InputDecoration(labelText: 'Theme'),
                  items: const [
                    DropdownMenuItem(value: 'system', child: Text('System default')),
                    DropdownMenuItem(value: 'light', child: Text('Light')),
                    DropdownMenuItem(value: 'dark', child: Text('Dark')),
                  ],
                  onChanged: (v) => v != null ? setState(() => _themeMode = v) : null,
                ),
              ]),
              if (settingsProvider.error != null) ...[
                const SizedBox(height: 12),
                Text(settingsProvider.error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ],
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: settingsProvider.isLoading ? null : _save,
                icon: const Icon(Icons.save),
                label: Text(settingsProvider.isLoading ? 'Saving...' : 'Save Settings'),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            ...children,
          ],
        ),
      ),
    );
  }
}