import 'dart:async';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart'; // kReleaseMode-এর জন্য

class NeuralStreamService {
  WebSocketChannel? _channel;

  final String apiBase = const String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://supremeai-backend-docker.onrender.com',
  );
  
  late final String wsUrl = (apiBase
      .replaceFirst('https://', 'wss://')
      .replaceFirst('http://', 'ws://')) + '/ws/chat';

  // ব্রডকাস্ট স্ট্রিম কন্ট্রোলার (মাল্টিপল লিসেনার এবং রিকানেকশনের জন্য)
  final StreamController<dynamic> _streamController = StreamController.broadcast();
  Stream<dynamic> get stream => _streamController.stream;

  bool _isIntentionalDisconnect = false;

  void connect() {
    _isIntentionalDisconnect = false;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      debugPrint('🟢 [WS] Connected to Neural Engine ($wsUrl)');

      _channel!.stream.listen(
        (data) {
          _streamController.add(data);
        },
        onDone: () {
          debugPrint('🔴 [WS] Connection closed.');
          _reconnect();
        },
        onError: (error) {
          debugPrint('⚠️ [WS] Error: $error');
          _reconnect();
        },
      );
    } catch (e) {
      _reconnect();
    }
  }

  void _reconnect() {
    if (_isIntentionalDisconnect) return;
    debugPrint('🔄 [WS] Connection lost. Reconnecting in 3 seconds...');
    Future.delayed(const Duration(seconds: 3), () => connect());
  }

  void sendMessage(String message) {
    if (message.isNotEmpty && _channel != null) {
      _channel!.sink.add(message);
    }
  }

  void disconnect() {
    _isIntentionalDisconnect = true;
    _channel?.sink.close();
    debugPrint('🛑 [WS] Disconnected manually');
  }
}
