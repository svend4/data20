import 'package:flutter/material.dart';

// Placeholder for Jobs List Screen
// Full implementation would show all user jobs with filters
class JobsScreen extends StatelessWidget {
  const JobsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('История задач'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: const [
            Icon(Icons.history, size: 64, color: Colors.blue),
            SizedBox(height: 16),
            Text(
              'Jobs Screen',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 16),
            Padding(
              padding: EdgeInsets.all(24.0),
              child: Text(
                'Full implementation would include:\n'
                '• List of all jobs\n'
                '• Status filters\n'
                '• Tool filters\n'
                '• Auto-refresh\n'
                '• Job details\n'
                '• Rerun capability',
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
