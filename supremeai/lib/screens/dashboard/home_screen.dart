import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/orchestration_provider.dart';
import '../../providers/auth_provider.dart';
import '../settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  final TextEditingController _chatController = TextEditingController();
  final List<ChatMessage> _messages = [];

  void _sendMessage() async {
    if (_chatController.text.trim().isEmpty) return;

    final userMessage = _chatController.text.trim();
    setState(() {
      _messages.add(ChatMessage(
        text: userMessage,
        isUser: true,
        timestamp: DateTime.now(),
      ));
    });
    _chatController.clear();

    final orchestration = context.read<OrchestrationProvider>();
    final auth = context.read<AuthProvider>();

    // Allow guest usage (token is null)
    await orchestration.orchestrateRequirement(userMessage, auth.token ?? 'GUEST_MODE');

    if (orchestration.lastResult != null && mounted) {
      setState(() {
        final result = orchestration.lastResult!;
        final response = result['status'] == 'DECIDED' || result['status'] == 'COMPLETED'
            ? 'I\'ve analyzed your requirement using ${result['mode'] ?? 'AI'} mode. Tap "Generate" to create your project.'
            : result.toString();
        
        _messages.add(ChatMessage(
          text: response,
          isUser: false,
          timestamp: DateTime.now(),
          hasAction: result['status'] == 'DECIDED' || result['status'] == 'COMPLETED',
          result: result,
        ));
      });
    }
  }

  void _generateProject() {
    final auth = context.read<AuthProvider>();
    final orchestration = context.read<OrchestrationProvider>();
    orchestration.generateProject(auth.token ?? 'GUEST_MODE');
  }

  @override
  void dispose() {
    _chatController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SupremeAI'),
        actions: [
          if (context.watch<AuthProvider>().isGuest)
            IconButton(
              icon: const Icon(Icons.login),
              tooltip: 'Login for more quota',
              onPressed: () {
                // Return to login screen
                context.read<AuthProvider>().logout(); 
              },
            )
          else
            IconButton(
              icon: const Icon(Icons.logout),
              onPressed: () => context.read<AuthProvider>().logout(),
            ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          _buildChatTab(),
          const SettingsScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) => setState(() => _currentIndex = index),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.chat), label: 'Chat'),
          NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
        ],
      ),
    );
  }

  Widget _buildChatTab() {
    final orchestration = context.watch<OrchestrationProvider>();

    final auth = context.watch<AuthProvider>();
    return Column(
      children: [
        if (auth.isGuest)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
            color: Colors.amber.withValues(alpha: 0.1),
            child: Row(
              children: [
                const Icon(Icons.info_outline, size: 16, color: Colors.amber),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'Guest Mode: Limited quota. Login to increase limits.',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                ),
                TextButton(
                  onPressed: () => auth.logout(),
                  child: const Text('Login'),
                ),
              ],
            ),
          ),
        Expanded(
          child: _messages.isEmpty
              ? _buildEmptyState()
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _messages.length,
                  itemBuilder: (context, index) => _buildMessage(_messages[index]),
                ),
        ),
        if (orchestration.isLoading)
          LinearProgressIndicator(
            color: Theme.of(context).colorScheme.primary,
          ),
        if (orchestration.error != null)
          _buildErrorBanner(orchestration.error!.message),
        _buildInputArea(orchestration),
      ],
    );
  }

  Widget _buildMessage(ChatMessage message) {
    final isUser = message.isUser;
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(16),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        decoration: BoxDecoration(
          color: isUser
              ? Theme.of(context).colorScheme.primaryContainer
              : Theme.of(context).colorScheme.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(message.text),
            if (message.hasAction) ...[
              const SizedBox(height: 12),
              ElevatedButton.icon(
                onPressed: message.isUser ? null : _generateProject,
                icon: const Icon(Icons.rocket_launch, size: 18),
                label: const Text('Generate Project'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.auto_awesome, size: 64, color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            Text('Describe what you want to build...', textAlign: TextAlign.center),
            const SizedBox(height: 8),
            Text('AI will analyze and generate your project automatically.', textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorBanner(String error) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      color: Theme.of(context).colorScheme.errorContainer,
      child: Row(
        children: [
          Icon(Icons.error_outline, color: Theme.of(context).colorScheme.onErrorContainer),
          const SizedBox(width: 8),
          Expanded(child: Text(error, style: TextStyle(color: Theme.of(context).colorScheme.onErrorContainer))),
          TextButton(onPressed: () => context.read<OrchestrationProvider>().clearError(), child: const Text('Dismiss')),
        ],
      ),
    );
  }

  Widget _buildInputArea(OrchestrationProvider orchestration) {
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _chatController,
              decoration: const InputDecoration(hintText: 'Enter your requirement...', border: OutlineInputBorder()),
              onSubmitted: (_) => _sendMessage(),
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            onPressed: orchestration.isLoading ? null : _sendMessage,
            icon: const Icon(Icons.send),
          ),
        ],
      ),
    );
  }
}

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final bool hasAction;
  final Map<String, dynamic>? result;

  ChatMessage({required this.text, required this.isUser, required this.timestamp, this.hasAction = false, this.result});
}