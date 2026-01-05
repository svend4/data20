/// Battery Indicator Widget
/// Phase 8.2.4: Display battery usage and power state

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class BatteryIndicator extends StatefulWidget {
  final bool showDetailed;

  const BatteryIndicator({
    Key? key,
    this.showDetailed = false,
  }) : super(key: key);

  @override
  State<BatteryIndicator> createState() => _BatteryIndicatorState();
}

class _BatteryIndicatorState extends State<BatteryIndicator> {
  Map<String, dynamic>? _batteryStats;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.showDetailed) {
      _loadBatteryStats();
    }
  }

  Future<void> _loadBatteryStats() async {
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final apiService = context.read<ApiService>();
      final response = await apiService.client.get('/battery');

      setState(() {
        _batteryStats = response.data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.showDetailed) {
      return _buildDetailedView();
    } else {
      return _buildCompactView();
    }
  }

  Widget _buildCompactView() {
    return FutureBuilder<Map<String, dynamic>>(
      future: _fetchHealth(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const SizedBox.shrink();
        }

        final health = snapshot.data!;
        final battery = health['battery'] as Map<String, dynamic>?;

        if (battery == null) {
          return const SizedBox.shrink();
        }

        final state = battery['state'] as String? ?? 'unknown';
        final targetMet = battery['target_met'] as bool? ?? true;
        final estimatedDrain = battery['estimated_drain'] as String? ?? '0.0%/h';

        // Parse drain percentage
        final drainValue = double.tryParse(
          estimatedDrain.replaceAll('%/h', '').trim()
        ) ?? 0.0;

        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: _getStateColor(state).withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: _getStateColor(state).withOpacity(0.3),
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                _getStateIcon(state),
                size: 16,
                color: _getStateColor(state),
              ),
              const SizedBox(width: 6),
              Text(
                'Battery: $estimatedDrain',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: _getStateColor(state),
                ),
              ),
              if (targetMet) ...[
                const SizedBox(width: 4),
                Icon(
                  Icons.check_circle,
                  size: 14,
                  color: Colors.green.shade700,
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Widget _buildDetailedView() {
    if (_isLoading) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    if (_batteryStats == null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const Text(
                'Battery Statistics',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              const Text('No battery stats available'),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadBatteryStats,
                icon: const Icon(Icons.refresh),
                label: const Text('Load Stats'),
              ),
            ],
          ),
        ),
      );
    }

    final activity = _batteryStats!['activity'] as Map<String, dynamic>? ?? {};
    final powerMgmt = _batteryStats!['power_management'] as Map<String, dynamic>? ?? {};
    final batteryEst = _batteryStats!['battery_estimate'] as Map<String, dynamic>? ?? {};

    final state = powerMgmt['state'] as String? ?? 'unknown';
    final idleTime = activity['idle_time'] as String? ?? '0.0s';
    final totalRequests = activity['total_requests'] as int? ?? 0;
    final activityRate = activity['activity_rate'] as String? ?? '0.00 req/min';

    final estimatedDrain = batteryEst['estimated_drain'] as Map<String, dynamic>? ?? {};
    final perHour = estimatedDrain['per_hour'] as String? ?? '0.0%/h';
    final targetMet = batteryEst['target_met'] as bool? ?? true;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Battery Statistics',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: _loadBatteryStats,
                  tooltip: 'Refresh',
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Power State
            _buildStatRow(
              icon: _getStateIcon(state),
              label: 'Backend State',
              value: _getStateLabel(state),
              color: _getStateColor(state),
            ),

            const SizedBox(height: 12),

            // Idle Time
            _buildStatRow(
              icon: Icons.timer,
              label: 'Idle Time',
              value: idleTime,
            ),

            const SizedBox(height: 12),

            // Activity
            _buildStatRow(
              icon: Icons.show_chart,
              label: 'Activity Rate',
              value: activityRate,
              subtitle: '$totalRequests total requests',
            ),

            const SizedBox(height: 12),

            // Battery Drain
            _buildStatRow(
              icon: Icons.battery_charging_full,
              label: 'Estimated Drain',
              value: perHour,
              target: '< 5.0%/h',
              isGood: targetMet,
            ),

            if (estimatedDrain.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Divider(),
              const SizedBox(height: 8),
              const Text(
                'Breakdown:',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 8),
              _buildBreakdownRow('CPU', estimatedDrain['cpu'] as String? ?? '0.0%'),
              _buildBreakdownRow('Network', estimatedDrain['network'] as String? ?? '0.0%'),
              _buildBreakdownRow('Baseline', estimatedDrain['baseline'] as String? ?? '0.0%'),
            ],

            const SizedBox(height: 16),
            const Divider(),
            const SizedBox(height: 8),

            // Controls
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                if (state != 'active')
                  ElevatedButton.icon(
                    onPressed: _wakeBackend,
                    icon: const Icon(Icons.power_settings_new),
                    label: const Text('Wake'),
                  ),
                if (state == 'active')
                  OutlinedButton.icon(
                    onPressed: _sleepBackend,
                    icon: const Icon(Icons.bedtime),
                    label: const Text('Sleep'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow({
    required IconData icon,
    required String label,
    required String value,
    String? target,
    String? subtitle,
    bool? isGood,
    Color? color,
  }) {
    return Row(
      children: [
        Icon(icon, size: 20, color: color ?? Colors.blue.shade700),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              if (subtitle != null)
                Text(
                  subtitle,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                  ),
                ),
            ],
          ),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Row(
              children: [
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: color ?? (isGood == true
                        ? Colors.green.shade700
                        : isGood == false
                            ? Colors.orange.shade700
                            : Colors.black87),
                  ),
                ),
                if (isGood != null) ...[
                  const SizedBox(width: 4),
                  Icon(
                    isGood ? Icons.check_circle : Icons.warning_outlined,
                    size: 16,
                    color: isGood ? Colors.green.shade700 : Colors.orange.shade700,
                  ),
                ],
              ],
            ),
            if (target != null)
              Text(
                target,
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey.shade600,
                ),
              ),
          ],
        ),
      ],
    );
  }

  Widget _buildBreakdownRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            '  • $label',
            style: TextStyle(
              fontSize: 13,
              color: Colors.grey.shade700,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  IconData _getStateIcon(String state) {
    switch (state) {
      case 'active':
        return Icons.power;
      case 'idle':
        return Icons.access_time;
      case 'sleeping':
        return Icons.bedtime;
      case 'stopped':
        return Icons.power_off;
      default:
        return Icons.help_outline;
    }
  }

  String _getStateLabel(String state) {
    switch (state) {
      case 'active':
        return 'Active';
      case 'idle':
        return 'Idle';
      case 'sleeping':
        return 'Sleeping';
      case 'stopped':
        return 'Stopped';
      default:
        return 'Unknown';
    }
  }

  Color _getStateColor(String state) {
    switch (state) {
      case 'active':
        return Colors.green;
      case 'idle':
        return Colors.orange;
      case 'sleeping':
        return Colors.blue;
      case 'stopped':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  Future<void> _wakeBackend() async {
    try {
      final apiService = context.read<ApiService>();
      await apiService.client.post('/power/wake');
      await _loadBatteryStats();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Backend awakened')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  Future<void> _sleepBackend() async {
    try {
      final apiService = context.read<ApiService>();
      await apiService.client.post('/power/sleep');
      await _loadBatteryStats();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Backend sleeping')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  Future<Map<String, dynamic>> _fetchHealth() async {
    try {
      final apiService = context.read<ApiService>();
      final response = await apiService.client.get('/health');
      return response.data as Map<String, dynamic>;
    } catch (e) {
      return {};
    }
  }
}
