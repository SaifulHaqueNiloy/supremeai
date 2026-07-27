import 'package:flutter/material.dart';

class ChatMessage extends StatelessWidget {
  final String text;
  final String sender;
  final bool isMe;

  const ChatMessage({
    Key? key,
    required this.text,
    required this.sender,
    required this.isMe,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 5.0, horizontal: 8.0),
      child: Row(
        mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isMe) ...[
            CircleAvatar(
              radius: 18,
              backgroundColor: Color(0xFF2563EB),
              child: Text(
                sender[0],
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
            SizedBox(width: 8),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.all(12.0),
              decoration: BoxDecoration(
                color: isMe ? Color(0xFF2563EB) : Color(0xFFF1F5F9),
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(18),
                  topRight: Radius.circular(18),
                  bottomLeft: !isMe ? Radius.circular(4) : Radius.circular(18),
                  bottomRight: isMe ? Radius.circular(4) : Radius.circular(18),
                ),
              ),
              child: Text(
                text,
                style: TextStyle(
                  color: isMe ? Colors.white : Color(0xFF334155),
                  fontSize: 16,
                ),
              ),
            ),
          ),
          if (isMe) ...[
            SizedBox(width: 8),
            CircleAvatar(
              radius: 18,
              backgroundColor: Color(0xFF10B981),
              child: Text(
                'U',
                style: TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}