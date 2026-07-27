import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class CodeEditorScreen extends StatefulWidget {
  const CodeEditorScreen({Key? key}) : super(key: key);

  @override
  _CodeEditorScreenState createState() => _CodeEditorScreenState();
}

class _CodeEditorScreenState extends State<CodeEditorScreen> {
  final TextEditingController _codeController = TextEditingController();
  String _selectedLanguage = 'Dart';
  bool _isEditing = false;

  @override
  void initState() {
    super.initState();
    _codeController.text = '''void main() {
  print('Hello, SupremeAI!');
  
  // Sample function to demonstrate code editing
  int calculateSum(int a, int b) {
    return a + b;
  }
  
  int result = calculateSum(5, 3);
  print('Result: \$result');
}''';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Color(0xFF2563EB),
        foregroundColor: Colors.white,
        title: const Text('Code Editor'),
        centerTitle: true,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.copy),
            onPressed: () {
              Clipboard.setData(ClipboardData(text: _codeController.text));
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Code copied to clipboard')),
              );
            },
          ),
          PopupMenuButton<String>(
            onSelected: (String result) {
              if (result == 'format') {
                // Format code
              } else if (result == 'analyze') {
                // Analyze code
              } else if (result == 'ai_help') {
                // Get AI help
              }
            },
            itemBuilder: (BuildContext context) => [
              const PopupMenuItem<String>(
                value: 'format',
                child: ListTile(
                  leading: Icon(Icons.format_align_left),
                  title: Text('Format Code'),
                ),
              ),
              const PopupMenuItem<String>(
                value: 'analyze',
                child: ListTile(
                  leading: Icon(Icons.analytics),
                  title: Text('Analyze Code'),
                ),
              ),
              const PopupMenuItem<String>(
                value: 'ai_help',
                child: ListTile(
                  leading: Icon(Icons.smart_toy),
                  title: Text('AI Help'),
                ),
              ),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            color: Color(0xFF0F172A),
            child: Row(
              children: [
                Text(
                  'main.dart',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Spacer(),
                DropdownButton<String>(
                  value: _selectedLanguage,
                  underline: Container(),
                  dropdownColor: Color(0xFF1E293B),
                  iconEnabledColor: Colors.white,
                  items: <String>['Dart', 'JavaScript', 'Python', 'Java', 'C++']
                      .map<DropdownMenuItem<String>>((String value) {
                    return DropdownMenuItem<String>(
                      value: value,
                      child: Text(
                        value,
                        style: TextStyle(color: Colors.white),
                      ),
                    );
                  }).toList(),
                  onChanged: (String? newValue) {
                    setState(() {
                      _selectedLanguage = newValue!;
                    });
                  },
                ),
              ],
            ),
          ),
          Expanded(
            child: Container(
              color: Color(0xFF1E293B),
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: TextField(
                    controller: _codeController,
                    maxLines: null,
                    expands: true,
                    keyboardType: TextInputType.multiline,
                    style: TextStyle(
                      fontFamily: 'monospace',
                      fontSize: 14,
                      color: Colors.white,
                    ),
                    decoration: InputDecoration(
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.zero,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () {
          // Simulate running code
          showDialog(
            context: context,
            builder: (BuildContext context) {
              return AlertDialog(
                title: Text('Run Code'),
                content: Text('In the full implementation, this would run the code in a secure sandbox.'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.of(context).pop(),
                    child: Text('OK'),
                  ),
                ],
              );
            },
          );
        },
        label: Text('Run'),
        icon: Icon(Icons.play_arrow),
        backgroundColor: Color(0xFF10B981),
      ),
    );
  }
}