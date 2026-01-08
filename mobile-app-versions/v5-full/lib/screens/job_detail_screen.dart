import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import '../models/job.dart';
import '../services/api_service.dart';
import 'tool_detail_screen.dart';

/// Job Detail Screen - показывает детали конкретной задачи
class JobDetailScreen extends StatelessWidget {
  final String jobId;
  final Job? job;

  const JobDetailScreen({
    Key? key,
    required this.jobId,
    this.job,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Детали задачи'),
        actions: [
          if (job != null && job!.isCompleted)
            IconButton(
              icon: const Icon(Icons.replay),
              onPressed: () => _rerunJob(context),
              tooltip: 'Повторить',
            ),
        ],
      ),
      body: job == null
          ? const Center(child: CircularProgressIndicator())
          : _buildJobDetails(context),
    );
  }

  Widget _buildJobDetails(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Header card
        _buildHeaderCard(),

        const SizedBox(height: 16),

        // Status card
        _buildStatusCard(),

        const SizedBox(height: 16),

        // Timing card
        _buildTimingCard(),

        const SizedBox(height: 16),

        // Parameters card
        if (job!.parameters != null) _buildParametersCard(),

        if (job!.parameters != null) const SizedBox(height: 16),

        // Result card
        if (job!.result != null) _buildResultCard(),

        // Error card
        if (job!.error != null) _buildErrorCard(),

        const SizedBox(height: 16),

        // Actions
        _buildActions(context),
      ],
    );
  }

  Widget _buildHeaderCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _getToolIcon(job!.toolName),
                  size: 32,
                  color: Colors.blue[700],
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        job!.toolName,
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'ID: ${job!.jobId}',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey[600],
                          fontFamily: 'monospace',
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard() {
    Color statusColor;
    IconData statusIcon;
    String statusText;

    switch (job!.status) {
      case 'completed':
        statusColor = Colors.green;
        statusIcon = Icons.check_circle;
        statusText = '✅ Успешно завершено';
        break;
      case 'failed':
        statusColor = Colors.red;
        statusIcon = Icons.error;
        statusText = '❌ Ошибка выполнения';
        break;
      case 'running':
        statusColor = Colors.blue;
        statusIcon = Icons.play_circle;
        statusText = '▶️ Выполняется';
        break;
      case 'pending':
        statusColor = Colors.orange;
        statusIcon = Icons.schedule;
        statusText = '⏳ В очереди';
        break;
      default:
        statusColor = Colors.grey;
        statusIcon = Icons.help;
        statusText = job!.status;
    }

    return Card(
      color: statusColor.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(statusIcon, size: 48, color: statusColor),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Статус',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    statusText,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: statusColor,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimingCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Временные метки',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            _buildTimingRow(
              '📅 Создано',
              _formatFullDateTime(job!.createdAt),
            ),
            if (job!.startedAt != null) ...[
              const SizedBox(height: 8),
              _buildTimingRow(
                '▶️ Запущено',
                _formatFullDateTime(job!.startedAt!),
              ),
            ],
            if (job!.completedAt != null) ...[
              const SizedBox(height: 8),
              _buildTimingRow(
                '✅ Завершено',
                _formatFullDateTime(job!.completedAt!),
              ),
            ],
            if (job!.duration != null) ...[
              const Divider(height: 24),
              _buildTimingRow(
                '⏱️ Длительность',
                job!.durationText,
                highlighted: true,
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTimingRow(String label, String value, {bool highlighted = false}) {
    return Row(
      children: [
        SizedBox(
          width: 120,
          child: Text(
            label,
            style: TextStyle(
              color: Colors.grey[700],
              fontSize: 14,
            ),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: TextStyle(
              fontWeight: highlighted ? FontWeight.bold : FontWeight.normal,
              fontSize: highlighted ? 16 : 14,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildParametersCard() {
    final parametersJson = const JsonEncoder.withIndent('  ').convert(job!.parameters);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Параметры',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: SelectableText(
                parametersJson,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    final resultJson = const JsonEncoder.withIndent('  ').convert(job!.result);

    return Card(
      color: Colors.green[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.check_circle, color: Colors.green[700]),
                const SizedBox(width: 8),
                const Text(
                  'Результат',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[900],
                borderRadius: BorderRadius.circular(8),
              ),
              child: SelectableText(
                resultJson,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 13,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorCard() {
    return Card(
      color: Colors.red[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.error, color: Colors.red[700]),
                const SizedBox(width: 8),
                const Text(
                  'Ошибка',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red[200]!),
              ),
              child: SelectableText(
                job!.error!,
                style: TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 13,
                  color: Colors.red[900],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActions(BuildContext context) {
    if (!job!.isCompleted) return const SizedBox.shrink();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Действия',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: () => _rerunJob(context),
              icon: const Icon(Icons.replay),
              label: const Text('Повторить с теми же параметрами'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _rerunJob(BuildContext context) {
    // Navigate to tool detail screen with prefilled parameters
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => ToolDetailScreen(
          toolName: job!.toolName,
        ),
      ),
    );

    // Show success message
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Открыт ${job!.toolName} с параметрами из задачи'),
        backgroundColor: Colors.green,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  IconData _getToolIcon(String toolName) {
    if (toolName.contains('calculate') || toolName.contains('statistics')) {
      return Icons.calculate;
    } else if (toolName.contains('text') || toolName.contains('analysis')) {
      return Icons.text_fields;
    } else if (toolName.contains('chart') || toolName.contains('visualization')) {
      return Icons.bar_chart;
    } else if (toolName.contains('data')) {
      return Icons.data_array;
    } else if (toolName.contains('file') || toolName.contains('csv') || toolName.contains('json')) {
      return Icons.insert_drive_file;
    } else if (toolName.contains('encode') || toolName.contains('decode') || toolName.contains('hash')) {
      return Icons.lock;
    } else if (toolName.contains('date') || toolName.contains('time')) {
      return Icons.calendar_today;
    } else if (toolName.contains('url') || toolName.contains('parse')) {
      return Icons.link;
    } else {
      return Icons.build;
    }
  }

  String _formatFullDateTime(DateTime dt) {
    return '${dt.day}.${dt.month.toString().padLeft(2, '0')}.${dt.year} '
        '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}:${dt.second.toString().padLeft(2, '0')}';
  }
}
