import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter/services.dart';

import 'services/auth_service.dart';
import 'services/api_service.dart';
import 'services/storage_service.dart';
import 'services/backend_service.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/tool_detail_screen.dart';
import 'screens/job_detail_screen.dart';
import 'screens/jobs_screen.dart';
import 'screens/backend_status_screen.dart';
import 'utils/theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Set preferred orientations
  await SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Initialize services
  final storageService = StorageService();
  await storageService.init();

  final apiService = ApiService();
  final authService = AuthService(apiService, storageService);
  final backendService = BackendService();

  // Check if user is already logged in
  // TEMPORARILY DISABLED for testing - allows app to open without login
  // await authService.checkAuth();

  // Auto-start embedded backend (DISABLED to prevent startup crash)
  // User can manually start backend from Settings > Backend Status screen
  //
  // To enable auto-start, uncomment the code below:
  /*
  try {
    print('🚀 Auto-starting embedded backend...');
    await backendService.startBackend();
    print('✅ Embedded backend started successfully');
  } catch (e) {
    print('⚠️ Failed to auto-start backend: $e');
    // Continue anyway - user can start manually from status screen
  }
  */

  runApp(Data20App(
    authService: authService,
    apiService: apiService,
    backendService: backendService,
  ));
}

class Data20App extends StatelessWidget {
  final AuthService authService;
  final ApiService apiService;
  final BackendService backendService;

  const Data20App({
    Key? key,
    required this.authService,
    required this.apiService,
    required this.backendService,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: authService),
        Provider.value(value: apiService),
        Provider.value(value: backendService),
      ],
      child: Consumer<AuthService>(
        builder: (context, auth, _) {
          return MaterialApp.router(
            title: 'Data20 Knowledge Base',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: ThemeMode.system,
            routerConfig: _router(auth),
            debugShowCheckedModeBanner: false,
          );
        },
      ),
    );
  }

  GoRouter _router(AuthService auth) {
    return GoRouter(
      // TEMPORARILY DISABLED: Authentication requirement for testing
      // This allows the app to open directly to home screen without login
      //
      // To re-enable authentication, uncomment the line below:
      // initialLocation: auth.isAuthenticated ? '/home' : '/login',
      initialLocation: '/home',  // Skip login for testing

      // TEMPORARILY DISABLED: Auth redirect for testing
      // To re-enable, uncomment the redirect function below:
      /*
      redirect: (context, state) {
        final isAuthenticated = auth.isAuthenticated;
        final isLoginRoute = state.matchedLocation == '/login';

        // Redirect to login if not authenticated
        if (!isAuthenticated && !isLoginRoute) {
          return '/login';
        }

        // Redirect to home if authenticated and on login page
        if (isAuthenticated && isLoginRoute) {
          return '/home';
        }

        return null;
      },
      */
      routes: [
        GoRoute(
          path: '/login',
          builder: (context, state) => const LoginScreen(),
        ),
        GoRoute(
          path: '/home',
          builder: (context, state) => const HomeScreen(),
        ),
        GoRoute(
          path: '/tool/:toolName',
          builder: (context, state) {
            final toolName = state.pathParameters['toolName']!;
            return ToolDetailScreen(toolName: toolName);
          },
        ),
        GoRoute(
          path: '/jobs',
          builder: (context, state) => const JobsScreen(),
        ),
        GoRoute(
          path: '/job/:jobId',
          builder: (context, state) {
            final jobId = state.pathParameters['jobId']!;
            return JobDetailScreen(jobId: jobId);
          },
        ),
        GoRoute(
          path: '/backend-status',
          builder: (context, state) {
            return BackendStatusScreen(
              backendService: backendService,
            );
          },
        ),
      ],
      refreshListenable: auth,
    );
  }
}
