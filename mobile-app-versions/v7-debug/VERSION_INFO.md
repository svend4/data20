# 📱 Version 7: Debug Edition

## 🔍 Development & Debugging Version

This version contains **all v5 features** plus **extensive debugging tools** for development and troubleshooting.

---

## 📊 Version Information

- **Version**: v7-debug
- **Based on**: v5-full
- **Status**: 🔧 Development only
- **Purpose**: Debugging and development

---

## 🔍 What's Different

### All v5-full Features
✅ 57 production tools
✅ Embedded Python backend
✅ 100% offline
✅ All v5 functionality

### Plus Debug Features

**Logging & Monitoring**:
- Verbose logging (all API calls)
- Performance profiling
- Memory usage tracking
- Network request logging
- Database query logging

**Developer Tools**:
- API inspector UI
- Database browser
- Log viewer screen
- Cache inspector
- Performance dashboard

**Debug Endpoints**:
- `/debug/memory` - Memory stats
- `/debug/logs` - View logs
- `/debug/database` - DB inspection
- `/debug/performance` - Performance metrics

---

## 📊 Technical Specifications

### APK Size: ~110MB
- v5 base: ~100MB
- Debug tools: ~10MB

### System Requirements
- Android 7.0+ (API 24)
- RAM: 2GB (more for debug overhead)
- Storage: 160MB
- Internet: Not required

### Performance
- First launch: 5-7 seconds
- RAM usage: ~300-500MB (higher due to logging)
- Battery: ~5-10% per hour
- Log files: ~10-50MB

---

## 🔧 Debug Features

### Log Levels

**Available levels**:
- DEBUG - All details
- INFO - Important events
- WARNING - Potential issues
- ERROR - Error messages
- CRITICAL - Critical failures

**Toggle in app**:
- Settings → Developer Options → Log Level

### Performance Profiling

**Metrics tracked**:
- Tool execution time
- API response time
- Database query time
- Memory allocation
- CPU usage

**View in app**:
- Developer Menu → Performance Dashboard

### Database Inspector

**Features**:
- Browse all tables
- View records
- Execute SQL queries
- Export database
- Clear database

**Access**:
- Developer Menu → Database Browser

---

## ⚠️ Warnings

### DO NOT Use for Production

❌ **Slower** - Debug overhead
❌ **Larger** - Extra logging
❌ **Privacy** - Logs may contain sensitive data
❌ **Battery** - More battery usage

### Use Only For

✅ **Development** - Testing code changes
✅ **Debugging** - Troubleshooting issues
✅ **Profiling** - Performance optimization
✅ **Testing** - Finding bugs

---

## 🎯 Use Cases

### ✅ When to Use v7-debug

- **Developer** - Writing new code
- **Debugging issues** - Troubleshooting bugs
- **Performance testing** - Optimizing app
- **Learning** - Understanding how app works

### ❌ When NOT to Use

- **Production** → Use v5-full
- **End users** → Use v4-standard or v5-full
- **Privacy concerns** → Use v5-full (no logs)

---

## 🔍 Debugging Workflow

### 1. Enable Debug Mode

```
Settings → Developer Options → Enable Debug Mode
```

### 2. Reproduce Issue

Use the app and reproduce the bug/issue

### 3. View Logs

```
Developer Menu → Logs → Filter by ERROR
```

### 4. Export Logs

```
Logs → Export → Share to developer
```

### 5. Disable When Done

```
Settings → Developer Options → Disable Debug Mode
```

---

## 📊 Comparison

| Metric | v5-full | v7-debug |
|--------|---------|----------|
| APK Size | 100MB | 110MB |
| Tools | 57 | 57 + debug |
| Logging | Minimal | Verbose |
| RAM | 2GB | 2GB+ |
| Purpose | Production | Development |

---

## 🔧 Build Instructions

```bash
cd mobile-app-versions/v7-debug
./build-android-embedded.sh debug  # Note: debug mode
```

⚠️ **Debug builds are NOT optimized**

---

## 📝 Log Format

```
[2026-01-05 18:30:45] [DEBUG] [BackendService] Starting backend...
[2026-01-05 18:30:48] [INFO] [BackendService] Backend started on 127.0.0.1:8001
[2026-01-05 18:30:50] [DEBUG] [ApiService] GET /api/tools
[2026-01-05 18:30:51] [DEBUG] [ApiService] Response: 200 OK (1.2s)
[2026-01-05 18:31:00] [ERROR] [ToolRunner] Tool execution failed: IndexError
[2026-01-05 18:31:00] [DEBUG] [ToolRunner] Traceback: ...
```

---

## 🐛 Debugging Tips

### Common Issues

**Backend won't start**:
1. Check logs: `grep "Backend" /data/logs/app.log`
2. Verify port 8001 not in use
3. Check Python initialization errors

**Tool execution fails**:
1. Check tool logs: `grep "ToolRunner" /data/logs/app.log`
2. Verify tool parameters
3. Check database connection

**UI freezing**:
1. Check performance dashboard
2. Look for slow API calls (>2s)
3. Check memory usage

---

**Version**: v7-debug
**Status**: 🔧 Development only
**APK**: ~110MB
**Tools**: 57 + debug tools
**Purpose**: Debugging and development

**For developers only!** 🔍
