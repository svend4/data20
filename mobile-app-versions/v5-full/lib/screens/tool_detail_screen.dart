import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'dart:convert';
import '../services/api_service.dart';

/// Tool Detail Screen - Execute tools with parameters
class ToolDetailScreen extends StatefulWidget {
  final String toolName;
  final Map<String, dynamic>? toolData;

  const ToolDetailScreen({
    Key? key,
    required this.toolName,
    this.toolData,
  }) : super(key: key);

  @override
  State<ToolDetailScreen> createState() => _ToolDetailScreenState();
}

class _ToolDetailScreenState extends State<ToolDetailScreen> {
  final _formKey = GlobalKey<FormState>();
  final _parametersController = TextEditingController();
  bool _isLoading = false;
  Map<String, dynamic>? _result;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadExampleParameters();
  }

  @override
  void dispose() {
    _parametersController.dispose();
    super.dispose();
  }

  void _loadExampleParameters() {
    // Load example parameters based on tool name
    final examples = _getExampleParameters(widget.toolName);
    _parametersController.text = const JsonEncoder.withIndent('  ').convert(examples);
  }

  Map<String, dynamic> _getExampleParameters(String toolName) {
    switch (toolName) {
      case 'calculate_statistics':
        return {
          'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
          'metrics': ['mean', 'median', 'std', 'min', 'max']
        };
      case 'text_analysis':
        return {
          'text': 'Hello world! This is a test message. Hello again!',
          'language': 'en'
        };
      case 'correlation_analysis':
        return {
          'x': [1, 2, 3, 4, 5],
          'y': [2, 4, 5, 4, 5]
        };
      case 'base64_encode':
        return {
          'text': 'Hello, World!',
          'operation': 'encode'
        };
      case 'hash_calculator':
        return {
          'text': 'password123',
          'algorithm': 'sha256'
        };
      case 'json_parser':
        return {
          'json_string': '{"name": "John", "age": 30}',
          'operation': 'validate'
        };
      case 'csv_parser':
        return {
          'csv_data': 'name,age\\nJohn,30\\nJane,25',
          'delimiter': ','
        };
      case 'url_parser':
        return {
          'url': 'https://example.com/path?query=value&foo=bar'
        };
      case 'date_calculator':
        return {
          'date': '2026-01-08',
          'operation': 'add_days',
          'value': 7
        };
      case 'word_frequency':
        return {
          'text': 'hello world hello test world hello',
          'top_n': 3
        };
      case 'outlier_detection':
        return {
          'data': [1, 2, 3, 4, 5, 100, 6, 7, 8, 9],
          'method': 'iqr'
        };
      case 'data_filter':
        return {
          'data': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
          'condition': 'greater_than',
          'value': 5
        };
      default:
        return {};
    }
  }

  Future<void> _runTool() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _result = null;
      _error = null;
    });

    try {
      // Parse JSON parameters
      final parametersText = _parametersController.text.trim();
      Map<String, dynamic> parameters = {};

      if (parametersText.isNotEmpty) {
        parameters = json.decode(parametersText);
      }

      // Call API
      final apiService = context.read<ApiService>();
      final result = await apiService.runTool(widget.toolName, parameters);

      setState(() {
        _result = result;
        _isLoading = false;
      });

      _showSnackBar('Tool executed successfully!', isError: false);
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });

      _showSnackBar('Error: $e', isError: true);
    }
  }

  void _showSnackBar(String message, {required bool isError}) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.toolName),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadExampleParameters,
            tooltip: 'Load example',
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Tool info
            if (widget.toolData != null) _buildToolInfo(),

            const SizedBox(height: 16),

            // Parameters input
            _buildParametersInput(),

            const SizedBox(height: 16),

            // Run button
            _buildRunButton(),

            const SizedBox(height: 24),

            // Result display
            if (_isLoading) _buildLoadingIndicator(),
            if (_result != null) _buildResult(),
            if (_error != null) _buildError(),
          ],
        ),
      ),
    );
  }

  Widget _buildToolInfo() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              widget.toolData?['display_name'] ?? widget.toolName,
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            if (widget.toolData?['description'] != null)
              Text(
                widget.toolData!['description'],
                style: TextStyle(color: Colors.grey[600]),
              ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                Chip(
                  label: Text(widget.toolData?['category'] ?? 'Unknown'),
                  backgroundColor: Colors.blue[100],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildParametersInput() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Parameters (JSON):',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _parametersController,
              maxLines: 10,
              style: const TextStyle(fontFamily: 'monospace', fontSize: 14),
              decoration: const InputDecoration(
                hintText: '{\n  "param1": "value1",\n  "param2": "value2"\n}',
                border: OutlineInputBorder(),
                filled: true,
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return null; // Allow empty parameters
                }
                try {
                  json.decode(value);
                  return null;
                } catch (e) {
                  return 'Invalid JSON format';
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRunButton() {
    return SizedBox(
      height: 54,
      child: ElevatedButton.icon(
        onPressed: _isLoading ? null : _runTool,
        icon: const Icon(Icons.play_arrow, size: 28),
        label: const Text(
          'Execute Tool',
          style: TextStyle(fontSize: 18),
        ),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.green,
          foregroundColor: Colors.white,
        ),
      ),
    );
  }

  Widget _buildLoadingIndicator() {
    return const Card(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Column(
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Executing tool...'),
          ],
        ),
      ),
    );
  }

  Widget _buildResult() {
    final resultJson = const JsonEncoder.withIndent('  ').convert(_result);
    final isSuccess = _result?['success'] == true || !_result!.containsKey('success');

    return Card(
      color: isSuccess ? Colors.green[50] : Colors.orange[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  isSuccess ? Icons.check_circle : Icons.warning,
                  color: isSuccess ? Colors.green : Colors.orange,
                ),
                const SizedBox(width: 8),
                const Text(
                  'Result:',
                  style: TextStyle(
                    fontSize: 18,
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

  Widget _buildError() {
    return Card(
      color: Colors.red[50],
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.error, color: Colors.red),
                SizedBox(width: 8),
                Text(
                  'Error:',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Colors.red,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            SelectableText(
              _error!,
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 13,
                color: Colors.red,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
