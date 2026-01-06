class Tool {
  final String name;
  final String? displayName;
  final String? description;
  final String? category;
  final Map<String, Parameter>? parameters;

  Tool({
    required this.name,
    this.displayName,
    this.description,
    this.category,
    this.parameters,
  });

  factory Tool.fromJson(Map<String, dynamic> json) {
    Map<String, Parameter>? params;
    if (json['parameters'] != null) {
      params = {};
      (json['parameters'] as Map<String, dynamic>).forEach((key, value) {
        params![key] = Parameter.fromJson(value);
      });
    }

    return Tool(
      name: json['name'],
      displayName: json['display_name'],
      description: json['description'],
      category: json['category'],
      parameters: params,
    );
  }

  String get effectiveDisplayName => displayName ?? name;

  String getCategoryDisplayName() {
    const categoryMap = {
      'statistics': '📊 Статистика',
      'visualization': '📈 Визуализация',
      'cleaning': '🧹 Очистка данных',
      'transformation': '🔄 Преобразование',
      'analysis': '🔍 Анализ',
      'ml': '🤖 Машинное обучение',
      'nlp': '💬 NLP',
      'timeseries': '⏰ Временные ряды',
      'text': '📝 Текст',
      'network': '🌐 Сети',
      'other': '🔧 Другое',
    };
    return categoryMap[category ?? 'other'] ?? category ?? 'Другое';
  }

  String getCategoryIcon() {
    const iconMap = {
      'statistics': '📊',
      'visualization': '📈',
      'cleaning': '🧹',
      'transformation': '🔄',
      'analysis': '🔍',
      'ml': '🤖',
      'nlp': '💬',
      'timeseries': '⏰',
      'text': '📝',
      'network': '🌐',
      'other': '🔧',
    };
    return iconMap[category ?? 'other'] ?? '🔧';
  }
}

class Parameter {
  final String type;
  final bool required;
  final dynamic defaultValue;
  final List<dynamic>? enumValues;
  final String? description;
  final String? displayName;

  Parameter({
    required this.type,
    required this.required,
    this.defaultValue,
    this.enumValues,
    this.description,
    this.displayName,
  });

  factory Parameter.fromJson(Map<String, dynamic> json) {
    return Parameter(
      type: json['type'],
      required: json['required'] ?? false,
      defaultValue: json['default'],
      enumValues: json['enum'] != null ? List.from(json['enum']) : null,
      description: json['description'],
      displayName: json['display_name'],
    );
  }
}
