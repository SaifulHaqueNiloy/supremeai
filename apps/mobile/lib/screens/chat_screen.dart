import 'package:flutter/material.dart';
import 'package:supreme_ai/widgets/chat_message_widget.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({Key? key}) : super(key: key);

  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _textController = TextEditingController();
  final List<ChatMessage> _messages = <ChatMessage>[];
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Color(0xFF2563EB),
        foregroundColor: Colors.white,
        title: const Text('AI Assistant'),
        centerTitle: true,
        elevation: 0,
      ),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    itemCount: _messages.length,
                    itemBuilder: (context, index) {
                      return _messages[index];
                    },
                  ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.all(8.0),
              child: LinearProgressIndicator(),
            ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          spreadRadius: 1,
                          blurRadius: 5,
                          offset: Offset(0, 2),
                        ),
                      ],
                    ),
                    child: Row(
                      children: [
                        SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: _textController,
                            decoration: const InputDecoration(
                              hintText: 'Ask AI anything...',
                              border: InputBorder.none,
                              hintStyle: TextStyle(color: Color(0xFF94A3B8)),
                            ),
                            onSubmitted: (_) => _sendMessage(),
                          ),
                        ),
                        IconButton(
                          icon: Icon(Icons.send, color: Color(0xFF2563EB)),
                          onPressed: _isLoading ? null : _sendMessage,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.chat_outlined,
            size: 80,
            color: Color(0xFFCBD5E1),
          ),
          const SizedBox(height: 16),
          Text(
            'Start a conversation with SupremeAI',
            style: TextStyle(
              fontSize: 18,
              color: Color(0xFF64748B),
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          Text(
            'Ask about code, get suggestions, or find solutions',
            style: TextStyle(
              fontSize: 14,
              color: Color(0xFF94A3B8),
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  void _sendMessage() async {
    if (_textController.text.isEmpty || _isLoading) return;

    String messageText = _textController.text.trim();
    _textController.clear();

    setState(() {
      _messages.add(ChatMessage(
        text: messageText,
        sender: 'user',
        isMe: true,
      ));
      _isLoading = true;
    });

    // Simulate AI response
    await Future.delayed(Duration(seconds: 1));
    
    setState(() {
      _messages.add(ChatMessage(
        text: "I received your message: \"$messageText\". This is a simulated response from SupremeAI. In the full implementation, this would connect to the AI backend.",
        sender: 'AI',
        isMe: false,
      ));
      _isLoading = false;
    });
  }
}