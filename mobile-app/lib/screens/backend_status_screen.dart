import 'package:flutter/material.dart';
import '../services/backend_service.dart';

/**
 * BackendStatusScreen - Diagnostic screen for embedded backend
 *
 * Shows:
 * - Backend running status
 * - Connection details
 * - File paths
 * - Control buttons (start/stop/restart)
 * - Health check
 */
class BackendStatusScreen extends StatefulWidget {
  final BackendService backendService;

  const BackendStatusScreen({
    Key? key,
    required this.backendService,
  }) : super(key: key);

  @override
  State<BackendStatusScreen> createState() => _BackendStatusScreenState();
}

class _BackendStatusScreenState extends State<BackendStatusScreen> {
  Map<String, dynamic>? _status;
  bool _isLoading = false;
  String? _healthStatus;

  @override
  void initState() {
    super.initState();
    _refreshStatus();

    // Listen to status updates
    widget.backendService.statusStream.listen((status) {
      if (mounted) {
        setState(() {
          _status = status;
        });
      }
    });
  }

  Future<void> _refreshStatus() async {
    setState(() => _isLoading = true);

    try {
      final status = await widget.backendService.refreshStatus();
      final isHealthy = await widget.backendService.checkHealth();

      setState(() {
        _status = status;
        _healthStatus = isHealthy ? 'Healthy' : 'Unhealthy';
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _healthStatus = 'Error: $e';
        _isLoading = false;
      });
    }
  }

  Future<void> _startBackend() async {
    setState(() => _isLoading = true);

    try {
      await widget.backendService.startBackend();
      _showSnackBar('Backend started successfully', isError: false);
    } catch (e) {
      _showSnackBar('Failed to start: $e', isError: true);
    } finally {
      await _refreshStatus();
    }
  }

  Future<void> _stopBackend() async {
    setState(() => _isLoading = true);

    try {
      await widget.backendService.stopBackend();
      _showSnackBar('Backend stopped', isError: false);
    } catch (e) {
      _showSnackBar('Failed to stop: $e', isError: true);
    } finally {
      await _refreshStatus();
    }
  }

  Future<void> _restartBackend() async {
    setState(() => _isLoading = true);

    try {
      await widget.backendService.restartBackend();
      _showSnackBar('Backend restarted', isError: false);
    } catch (e) {
      _showSnackBar('Failed to restart: $e', isError: true);
    } finally {
      await _refreshStatus();
    }
  }

  void _showSnackBar(String message, {required bool isError}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
        duration: Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isRunning = widget.backendService.isRunning;

    return Scaffold(
      appBar: AppBar(
        title: Text('Backend Status'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _isLoading ? null : _refreshStatus,
          ),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refreshStatus,
              child: ListView(
                padding: EdgeInsets.all(16),
                children: [
                  // Status Card
                  _buildStatusCard(isRunning),

                  SizedBox(height: 16),

                  // Connection Details
                  _buildConnectionCard(),

                  SizedBox(height: 16),

                  // File Paths
                  if (_status != null) _buildPathsCard(),

                  SizedBox(height: 16),

                  // Control Buttons
                  _buildControlButtons(isRunning),

                  SizedBox(height: 16),

                  // Health Status
                  if (_healthStatus != null) _buildHealthCard(),
                ],
              ),
            ),
    );
  }

  Widget _buildStatusCard(bool isRunning) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isRunning ? Icons.check_circle : Icons.cancel,
                  color: isRunning ? Colors.green : Colors.red,
                  size: 32,
                ),
                SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Backend Status',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        isRunning ? 'Running' : 'Stopped',
                        style: TextStyle(
                          color: isRunning ? Colors.green : Colors.grey,
                          fontSize: 16,
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

  Widget _buildConnectionCard() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Connection Details',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 12),
            _buildInfoRow('Host', _status?['host'] ?? '127.0.0.1'),
            _buildInfoRow('Port', '${_status?['port'] ?? 8001}'),
            _buildInfoRow('URL', _status?['url'] ?? 'http://127.0.0.1:8001'),
          ],
        ),
      ),
    );
  }

  Widget _buildPathsCard() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Storage Paths',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 12),
            _buildInfoRow(
              'Database',
              _status?['databasePath'] ?? 'N/A',
              isPath: true,
            ),
            _buildInfoRow(
              'Uploads',
              _status?['uploadPath'] ?? 'N/A',
              isPath: true,
            ),
            _buildInfoRow(
              'Logs',
              _status?['logsPath'] ?? 'N/A',
              isPath: true,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHealthCard() {
    final isHealthy = _healthStatus == 'Healthy';

    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              isHealthy ? Icons.favorite : Icons.error,
              color: isHealthy ? Colors.green : Colors.orange,
            ),
            SizedBox(width: 12),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Health Check',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                Text(_healthStatus!),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isPath = false}) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 100,
            child: Text(
              '$label:',
              style: TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey[700],
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                fontSize: isPath ? 12 : 14,
                fontFamily: isPath ? 'monospace' : null,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControlButtons(bool isRunning) {
    return Column(
      children: [
        if (!isRunning)
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: _isLoading ? null : _startBackend,
              icon: Icon(Icons.play_arrow),
              label: Text('Start Backend'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
              ),
            ),
          ),
        if (isRunning) ...[
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: _isLoading ? null : _stopBackend,
              icon: Icon(Icons.stop),
              label: Text('Stop Backend'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
              ),
            ),
          ),
          SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: OutlinedButton.icon(
              onPressed: _isLoading ? null : _restartBackend,
              icon: Icon(Icons.refresh),
              label: Text('Restart Backend'),
            ),
          ),
        ],
      ],
    );
  }
}
