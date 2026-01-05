import 'package:flutter/material.dart';

// Placeholder for Tool Detail Screen
// Full implementation would include parameter form and job execution
class ToolDetailScreen extends StatelessWidget {
  final String toolName;

  const ToolDetailScreen({Key? key, required this.toolName}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(toolName),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.construction, size: 64, color: Colors.orange),
            const SizedBox(height: 16),
            const Text(
              'Tool Detail Screen',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text('Tool: $toolName'),
            const SizedBox(height: 16),
            const Padding(
              padding: EdgeInsets.all(24.0),
              child: Text(
                'Full implementation would include:\n'
                '• Tool description\n'
                '• Parameter form builder\n'
                '• Dynamic input fields\n'
                '• Validation\n'
                '• Job execution\n'
                '• Real-time status',
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
