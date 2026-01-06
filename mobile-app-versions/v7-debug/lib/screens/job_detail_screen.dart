import 'package:flutter/material.dart';

// Placeholder for Job Detail Screen
// Full implementation would show job status and results
class JobDetailScreen extends StatelessWidget {
  final String jobId;

  const JobDetailScreen({Key? key, required this.jobId}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Детали задачи'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.task_alt, size: 64, color: Colors.green),
            const SizedBox(height: 16),
            const Text(
              'Job Detail Screen',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text('Job ID: $jobId'),
            const SizedBox(height: 16),
            const Padding(
              padding: EdgeInsets.all(24.0),
              child: Text(
                'Full implementation would include:\n'
                '• Job status\n'
                '• Progress indicator\n'
                '• Start/end times\n'
                '• Duration\n'
                '• Parameters used\n'
                '• Result or error\n'
                '• Auto-refresh polling',
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
