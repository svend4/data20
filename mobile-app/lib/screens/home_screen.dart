import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/tool.dart';
import '../config/app_variant.dart';
import '../widgets/performance_indicator.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Tool> _tools = [];
  List<Tool> _filteredTools = [];
  bool _isLoading = true;
  String? _error;
  String _searchQuery = '';
  String _selectedCategory = 'all';

  @override
  void initState() {
    super.initState();
    _loadTools();
  }

  Future<void> _loadTools() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final apiService = context.read<ApiService>();
      final tools = await apiService.getTools();

      setState(() {
        _tools = tools;
        _filterTools();
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Ошибка загрузки инструментов: $e';
        _isLoading = false;
      });
    }
  }

  void _filterTools() {
    setState(() {
      _filteredTools = _tools.where((tool) {
        // Category filter
        if (_selectedCategory != 'all' && tool.category != _selectedCategory) {
          return false;
        }

        // Search filter
        if (_searchQuery.isNotEmpty) {
          final query = _searchQuery.toLowerCase();
          final name = tool.effectiveDisplayName.toLowerCase();
          final description = (tool.description ?? '').toLowerCase();
          final category = (tool.category ?? '').toLowerCase();

          return name.contains(query) ||
              description.contains(query) ||
              category.contains(query);
        }

        return true;
      }).toList();
    });
  }

  List<String> get _categories {
    final categories = _tools.map((t) => t.category ?? 'other').toSet().toList();
    categories.sort();
    return ['all', ...categories];
  }

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();
    final user = authService.user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Data20 Knowledge Base'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () => context.push('/jobs'),
            tooltip: 'История задач',
          ),
          PopupMenuButton(
            icon: CircleAvatar(
              child: Text(
                user?.username[0].toUpperCase() ?? '?',
                style: const TextStyle(color: Colors.white),
              ),
            ),
            itemBuilder: (context) => [
              PopupMenuItem(
                child: ListTile(
                  leading: const Icon(Icons.person),
                  title: Text(user?.username ?? ''),
                  subtitle: Text(user?.email ?? ''),
                  contentPadding: EdgeInsets.zero,
                ),
                enabled: false,
              ),
              const PopupMenuDivider(),
              PopupMenuItem(
                child: const ListTile(
                  leading: Icon(Icons.logout),
                  title: Text('Выход'),
                  contentPadding: EdgeInsets.zero,
                ),
                onTap: () async {
                  await authService.logout();
                },
              ),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadTools,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
                ? _buildError()
                : _buildContent(),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _loadTools,
              icon: const Icon(Icons.refresh),
              label: const Text('Повторить'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVariantBanner() {
    final variant = AppVariantConfig.variant;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Color(variant.color).withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Color(variant.color).withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          Text(
            variant.icon,
            style: const TextStyle(fontSize: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${variant.displayName} Edition',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Color(variant.color),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  variant.description,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[700],
                  ),
                ),
              ],
            ),
          ),
          if (variant.canUpgrade)
            IconButton(
              icon: const Icon(Icons.arrow_upward),
              color: Color(variant.color),
              tooltip: variant.upgradeMessage,
              onPressed: () {
                _showUpgradeDialog();
              },
            ),
        ],
      ),
    );
  }

  void _showUpgradeDialog() {
    final variant = AppVariantConfig.variant;
    final nextVariant = variant.nextVariant;

    if (nextVariant == null) return;

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Text(nextVariant.icon),
            const SizedBox(width: 8),
            Text('Upgrade to ${nextVariant.displayName}'),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(nextVariant.description),
            const SizedBox(height: 16),
            _buildUpgradeFeature('Tools', '${variant.toolCount}', '${nextVariant.toolCount}'),
            const SizedBox(height: 8),
            _buildUpgradeFeature('Size', variant.appSize, nextVariant.appSize),
            const SizedBox(height: 16),
            const Text(
              'Download the upgraded version from:',
              style: TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 4),
            const Text(
              '• Google Play Store\n• Official website',
              style: TextStyle(fontSize: 12),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
          ElevatedButton(
            onPressed: () {
              // Open Play Store or website
              Navigator.pop(context);
            },
            child: const Text('Learn More'),
          ),
        ],
      ),
    );
  }

  Widget _buildUpgradeFeature(String label, String current, String next) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontWeight: FontWeight.bold)),
        Row(
          children: [
            Text(current, style: TextStyle(color: Colors.grey[600])),
            const Icon(Icons.arrow_forward, size: 16),
            Text(next, style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
          ],
        ),
      ],
    );
  }

  Widget _buildContent() {
    return Column(
      children: [
        // Variant banner
        _buildVariantBanner(),

        // Phase 8.2.3: Performance indicator
        const PerformanceIndicator(),

        // Search bar
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: TextField(
            decoration: InputDecoration(
              hintText: '🔍 Поиск инструментов...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _searchQuery.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        setState(() {
                          _searchQuery = '';
                          _filterTools();
                        });
                      },
                    )
                  : null,
            ),
            onChanged: (value) {
              setState(() {
                _searchQuery = value;
                _filterTools();
              });
            },
          ),
        ),

        // Category filter
        SizedBox(
          height: 50,
          child: ListView.builder(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _categories.length,
            itemBuilder: (context, index) {
              final category = _categories[index];
              final isSelected = category == _selectedCategory;

              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(
                    category == 'all'
                        ? 'Все инструменты'
                        : Tool(name: '', category: category).getCategoryDisplayName(),
                  ),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() {
                        _selectedCategory = category;
                        _filterTools();
                      });
                    }
                  },
                ),
              );
            },
          ),
        ),

        const SizedBox(height: 8),

        // Tools grid
        Expanded(
          child: _filteredTools.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.search_off, size: 64, color: Colors.grey),
                      const SizedBox(height: 16),
                      Text(
                        'Ничего не найдено',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                              color: Colors.grey,
                            ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Попробуйте изменить запрос',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                )
              : GridView.builder(
                  padding: const EdgeInsets.all(16),
                  gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                    crossAxisCount: 2,
                    childAspectRatio: 0.85,
                    crossAxisSpacing: 16,
                    mainAxisSpacing: 16,
                  ),
                  itemCount: _filteredTools.length,
                  itemBuilder: (context, index) {
                    return _buildToolCard(_filteredTools[index]);
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildToolCard(Tool tool) {
    final paramsCount = tool.parameters?.length ?? 0;
    final requiredParams =
        tool.parameters?.values.where((p) => p.required).length ?? 0;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => context.push('/tool/${tool.name}'),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Category badge
              Chip(
                label: Text(
                  tool.getCategoryDisplayName(),
                  style: const TextStyle(fontSize: 10),
                ),
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                padding: EdgeInsets.zero,
                visualDensity: VisualDensity.compact,
              ),
              const SizedBox(height: 8),

              // Icon and name
              Row(
                children: [
                  Text(
                    tool.getCategoryIcon(),
                    style: const TextStyle(fontSize: 24),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      tool.effectiveDisplayName,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // Description
              Expanded(
                child: Text(
                  tool.description ?? 'Описание недоступно',
                  style: Theme.of(context).textTheme.bodySmall,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
              ),

              // Parameters count
              Text(
                '📝 Параметров: $paramsCount${requiredParams > 0 ? " ($requiredParams обязательных)" : ""}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
