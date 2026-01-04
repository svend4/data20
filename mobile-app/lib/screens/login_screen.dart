import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../services/backend_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final _loginFormKey = GlobalKey<FormState>();
  final _registerFormKey = GlobalKey<FormState>();

  // Login fields
  final _loginUsernameController = TextEditingController();
  final _loginPasswordController = TextEditingController();

  // Register fields
  final _registerUsernameController = TextEditingController();
  final _registerEmailController = TextEditingController();
  final _registerPasswordController = TextEditingController();
  final _registerFullNameController = TextEditingController();

  String? _errorMessage;
  bool _isBackendStarting = false;
  bool _isBackendRunning = false;
  String? _backendStatus;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _loginUsernameController.dispose();
    _loginPasswordController.dispose();
    _registerUsernameController.dispose();
    _registerEmailController.dispose();
    _registerPasswordController.dispose();
    _registerFullNameController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_loginFormKey.currentState!.validate()) return;

    setState(() => _errorMessage = null);

    final authService = context.read<AuthService>();

    try {
      await authService.login(
        _loginUsernameController.text,
        _loginPasswordController.text,
      );
      // Navigation will be handled by router
    } on ApiException catch (e) {
      setState(() => _errorMessage = e.message);
    } catch (e) {
      setState(() => _errorMessage = 'Ошибка входа: $e');
    }
  }

  Future<void> _handleRegister() async {
    if (!_registerFormKey.currentState!.validate()) return;

    setState(() => _errorMessage = null);

    final authService = context.read<AuthService>();

    try {
      await authService.register(
        username: _registerUsernameController.text,
        email: _registerEmailController.text,
        password: _registerPasswordController.text,
        fullName: _registerFullNameController.text.isNotEmpty
            ? _registerFullNameController.text
            : null,
      );

      // Show success and switch to login tab
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Регистрация успешна! Войдите в систему.'),
            backgroundColor: Colors.green,
          ),
        );
        _tabController.animateTo(0);
      }
    } on ApiException catch (e) {
      setState(() => _errorMessage = e.message);
    } catch (e) {
      setState(() => _errorMessage = 'Ошибка регистрации: $e');
    }
  }

  Future<void> _startBackend() async {
    if (_isBackendStarting || _isBackendRunning) return;

    setState(() {
      _isBackendStarting = true;
      _backendStatus = 'Запуск backend сервера...';
    });

    final backendService = context.read<BackendService>();

    try {
      await backendService.startBackend();

      if (mounted) {
        setState(() {
          _isBackendRunning = true;
          _isBackendStarting = false;
          _backendStatus = 'Backend запущен ✓';
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Backend запущен! Теперь можно войти.'),
            backgroundColor: Colors.green,
            duration: Duration(seconds: 3),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isBackendStarting = false;
          _backendStatus = 'Ошибка запуска backend';
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Ошибка запуска backend: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final authService = context.watch<AuthService>();

    return Scaffold(
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _isBackendStarting || _isBackendRunning ? null : _startBackend,
        icon: _isBackendStarting
            ? const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : Icon(_isBackendRunning ? Icons.check_circle : Icons.power_settings_new),
        label: Text(
          _isBackendRunning
              ? 'Backend запущен'
              : _isBackendStarting
                  ? 'Запуск...'
                  : 'Запустить Backend',
        ),
        backgroundColor: _isBackendRunning
            ? Colors.green
            : _isBackendStarting
                ? Colors.orange
                : Theme.of(context).colorScheme.primary,
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.centerFloat,
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).colorScheme.primary,
              Theme.of(context).colorScheme.secondary,
            ],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24.0),
              child: Card(
                elevation: 8,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Container(
                  padding: const EdgeInsets.all(24.0),
                  constraints: const BoxConstraints(maxWidth: 400),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // Logo/Title
                      const Icon(
                        Icons.storage_rounded,
                        size: 64,
                        color: Color(0xFF667eea),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Data20',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                              color: const Color(0xFF667eea),
                            ),
                      ),
                      Text(
                        'Knowledge Base',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey[600],
                            ),
                      ),
                      const SizedBox(height: 16),

                      // Backend status indicator
                      if (_backendStatus != null)
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 8,
                          ),
                          decoration: BoxDecoration(
                            color: _isBackendRunning
                                ? Colors.green[50]
                                : _isBackendStarting
                                    ? Colors.orange[50]
                                    : Colors.red[50],
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: _isBackendRunning
                                  ? Colors.green[200]!
                                  : _isBackendStarting
                                      ? Colors.orange[200]!
                                      : Colors.red[200]!,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                _isBackendRunning
                                    ? Icons.check_circle
                                    : _isBackendStarting
                                        ? Icons.hourglass_empty
                                        : Icons.error_outline,
                                size: 16,
                                color: _isBackendRunning
                                    ? Colors.green
                                    : _isBackendStarting
                                        ? Colors.orange
                                        : Colors.red,
                              ),
                              const SizedBox(width: 8),
                              Text(
                                _backendStatus!,
                                style: TextStyle(
                                  fontSize: 12,
                                  color: _isBackendRunning
                                      ? Colors.green[900]
                                      : _isBackendStarting
                                          ? Colors.orange[900]
                                          : Colors.red[900],
                                ),
                              ),
                            ],
                          ),
                        ),
                      const SizedBox(height: 16),

                      // Tabs
                      TabBar(
                        controller: _tabController,
                        labelColor: Theme.of(context).colorScheme.primary,
                        unselectedLabelColor: Colors.grey,
                        indicatorColor: Theme.of(context).colorScheme.primary,
                        tabs: const [
                          Tab(text: 'Вход'),
                          Tab(text: 'Регистрация'),
                        ],
                      ),
                      const SizedBox(height: 24),

                      // Error message
                      if (_errorMessage != null)
                        Container(
                          padding: const EdgeInsets.all(12),
                          margin: const EdgeInsets.only(bottom: 16),
                          decoration: BoxDecoration(
                            color: Colors.red[50],
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: Colors.red[200]!),
                          ),
                          child: Row(
                            children: [
                              const Icon(Icons.error_outline, color: Colors.red),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  _errorMessage!,
                                  style: const TextStyle(color: Colors.red),
                                ),
                              ),
                            ],
                          ),
                        ),

                      // Tab views
                      SizedBox(
                        height: 300,
                        child: TabBarView(
                          controller: _tabController,
                          children: [
                            _buildLoginForm(authService),
                            _buildRegisterForm(authService),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLoginForm(AuthService authService) {
    return Form(
      key: _loginFormKey,
      child: Column(
        children: [
          TextFormField(
            controller: _loginUsernameController,
            decoration: const InputDecoration(
              labelText: 'Логин',
              prefixIcon: Icon(Icons.person),
            ),
            validator: (value) =>
                value?.isEmpty ?? true ? 'Введите логин' : null,
            enabled: !authService.isLoading,
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _loginPasswordController,
            decoration: const InputDecoration(
              labelText: 'Пароль',
              prefixIcon: Icon(Icons.lock),
            ),
            obscureText: true,
            validator: (value) =>
                value?.isEmpty ?? true ? 'Введите пароль' : null,
            enabled: !authService.isLoading,
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: authService.isLoading ? null : _handleLogin,
              child: authService.isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Войти'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRegisterForm(AuthService authService) {
    return Form(
      key: _registerFormKey,
      child: SingleChildScrollView(
        child: Column(
          children: [
            TextFormField(
              controller: _registerUsernameController,
              decoration: const InputDecoration(
                labelText: 'Логин *',
                prefixIcon: Icon(Icons.person),
              ),
              validator: (value) {
                if (value?.isEmpty ?? true) return 'Введите логин';
                if (value!.length < 3) return 'Минимум 3 символа';
                return null;
              },
              enabled: !authService.isLoading,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _registerEmailController,
              decoration: const InputDecoration(
                labelText: 'Email *',
                prefixIcon: Icon(Icons.email),
              ),
              keyboardType: TextInputType.emailAddress,
              validator: (value) {
                if (value?.isEmpty ?? true) return 'Введите email';
                if (!value!.contains('@')) return 'Некорректный email';
                return null;
              },
              enabled: !authService.isLoading,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _registerPasswordController,
              decoration: const InputDecoration(
                labelText: 'Пароль *',
                prefixIcon: Icon(Icons.lock),
              ),
              obscureText: true,
              validator: (value) {
                if (value?.isEmpty ?? true) return 'Введите пароль';
                if (value!.length < 8) return 'Минимум 8 символов';
                return null;
              },
              enabled: !authService.isLoading,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _registerFullNameController,
              decoration: const InputDecoration(
                labelText: 'Полное имя',
                prefixIcon: Icon(Icons.badge),
              ),
              enabled: !authService.isLoading,
            ),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: authService.isLoading ? null : _handleRegister,
                child: authService.isLoading
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Зарегистрироваться'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
