/// Performance Indicator Widget
/// Phase 8.2.3: Display performance metrics and startup time

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';

class PerformanceIndicator extends StatefulWidget {
  final bool showDetailed;

  const PerformanceIndicator({
    Key? key,
    this.showDetailed = false,
  }) : super(key: key);

  @override
  State<PerformanceIndicator> createState() => _PerformanceIndicatorState();
}

class _PerformanceIndicatorState extends State<PerformanceIndicator> {
  Map<String, dynamic>? _metrics;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.showDetailed) {
      _loadMetrics();
    }
  }

  Future<void> _loadMetrics() async {
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final apiService = context.read<ApiService>();
      final response = await apiService.client.get('/metrics');

      setState(() {
        _metrics = response.data;
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
        final performance = health['performance'] as Map<String, dynamic>?;

        if (performance == null) {
          return const SizedBox.shrink();
        }

        final startupTime = performance['startup_time'] as String?;
        final targetMet = performance['startup_target_met'] as bool? ?? false;

        if (startupTime == null) {
          return const SizedBox.shrink();
        }

        return Container(
          margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          decoration: BoxDecoration(
            color: targetMet ? Colors.green.shade50 : Colors.orange.shade50,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: targetMet ? Colors.green.shade200 : Colors.orange.shade200,
            ),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                targetMet ? Icons.speed : Icons.warning_outlined,
                size: 16,
                color: targetMet ? Colors.green.shade700 : Colors.orange.shade700,
              ),
              const SizedBox(width: 6),
              Text(
                'Startup: $startupTime',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w500,
                  color: targetMet ? Colors.green.shade700 : Colors.orange.shade700,
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

    if (_metrics == null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              const Text(
                'Performance Metrics',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 16),
              const Text('No metrics available'),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadMetrics,
                icon: const Icon(Icons.refresh),
                label: const Text('Load Metrics'),
              ),
            ],
          ),
        ),
      );
    }

    final metrics = _metrics!['metrics'] as Map<String, dynamic>? ?? {};
    final cacheStats = _metrics!['cache_stats'] as Map<String, dynamic>? ?? {};
    final recommendations = _metrics!['recommendations'] as List? ?? [];

    final startupTime = metrics['startup_time'] as num?;
    final toolsLoaded = metrics['tools_loaded'] as int? ?? 0;
    final toolsPreloaded = metrics['tools_preloaded'] as int? ?? 0;
    final cacheHitRate = cacheStats['hit_rate'] as num? ?? 0;
    final registryCacheSize = cacheStats['registry_cache_size'] as int? ?? 0;
    final resultCacheSize = cacheStats['result_cache_size'] as int? ?? 0;

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
                  'Performance Metrics',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: _loadMetrics,
                  tooltip: 'Refresh',
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Startup Time
            _buildMetricRow(
              icon: Icons.rocket_launch,
              label: 'Startup Time',
              value: startupTime != null ? '${startupTime.toStringAsFixed(2)}s' : 'N/A',
              target: '< 3.0s',
              isGood: startupTime != null && startupTime < 3.0,
            ),

            const SizedBox(height: 12),

            // Tools Loaded
            _buildMetricRow(
              icon: Icons.apps,
              label: 'Tools Loaded',
              value: '$toolsLoaded',
              subtitle: '$toolsPreloaded preloaded',
            ),

            const SizedBox(height: 12),

            // Cache Hit Rate
            _buildMetricRow(
              icon: Icons.cached,
              label: 'Cache Hit Rate',
              value: '${cacheHitRate.toStringAsFixed(1)}%',
              isGood: cacheHitRate >= 50,
            ),

            const SizedBox(height: 12),

            // Cache Sizes
            _buildMetricRow(
              icon: Icons.storage,
              label: 'Cache Sizes',
              value: 'Registry: $registryCacheSize',
              subtitle: 'Results: $resultCacheSize',
            ),

            if (recommendations.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Divider(),
              const SizedBox(height: 8),
              const Text(
                'Recommendations',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              ...recommendations.map((rec) => Padding(
                    padding: const EdgeInsets.only(bottom: 8.0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          rec.toString().startsWith('✅')
                              ? Icons.check_circle
                              : Icons.info_outline,
                          size: 16,
                          color: rec.toString().startsWith('✅')
                              ? Colors.green
                              : Colors.orange,
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            rec.toString(),
                            style: const TextStyle(fontSize: 13),
                          ),
                        ),
                      ],
                    ),
                  )),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildMetricRow({
    required IconData icon,
    required String label,
    required String value,
    String? target,
    String? subtitle,
    bool? isGood,
  }) {
    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.blue.shade700),
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
                    color: isGood == true
                        ? Colors.green.shade700
                        : isGood == false
                            ? Colors.orange.shade700
                            : Colors.black87,
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
