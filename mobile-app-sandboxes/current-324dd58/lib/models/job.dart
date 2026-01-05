class Job {
  final String jobId;
  final String toolName;
  final String status;
  final DateTime createdAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final Map<String, dynamic>? parameters;
  final dynamic result;
  final String? error;
  final String? userId;

  Job({
    required this.jobId,
    required this.toolName,
    required this.status,
    required this.createdAt,
    this.startedAt,
    this.completedAt,
    this.parameters,
    this.result,
    this.error,
    this.userId,
  });

  factory Job.fromJson(Map<String, dynamic> json) {
    return Job(
      jobId: json['job_id'],
      toolName: json['tool_name'],
      status: json['status'],
      createdAt: DateTime.parse(json['created_at']),
      startedAt: json['started_at'] != null
          ? DateTime.parse(json['started_at'])
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'])
          : null,
      parameters: json['parameters'],
      result: json['result'],
      error: json['error'],
      userId: json['user_id'],
    );
  }

  bool get isPending => status == 'pending';
  bool get isRunning => status == 'running';
  bool get isCompleted => status == 'completed';
  bool get isFailed => status == 'failed';

  String get statusDisplayName {
    const statusMap = {
      'pending': '⏳ Ожидание',
      'running': '▶️ Выполняется',
      'completed': '✅ Завершено',
      'failed': '❌ Ошибка',
    };
    return statusMap[status] ?? status;
  }

  Duration? get duration {
    if (startedAt != null && completedAt != null) {
      return completedAt!.difference(startedAt!);
    } else if (startedAt != null && isRunning) {
      return DateTime.now().difference(startedAt!);
    }
    return null;
  }

  String get durationText {
    final d = duration;
    if (d == null) return '-';

    if (d.inSeconds < 60) {
      return '${d.inSeconds}с';
    }
    final minutes = d.inMinutes;
    final seconds = d.inSeconds % 60;
    return '${minutes}м ${seconds}с';
  }
}
