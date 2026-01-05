# 📱 Version 2: Hybrid Edition

## 🔄 Cloud Backend + Local Cache

This version uses **external backend** with **SQLite cache** for partial offline functionality.

---

## 📊 Version Information

- **Version**: v2-hybrid
- **Based on**: v1-original (with cache added)
- **Status**: ⚙️ Conceptual (requires implementation)
- **Purpose**: Bridge between v1 and v3

---

## 🔄 Architecture

### Hybrid Approach

```
Mobile App (Flutter)
    ↓
Cache Check (SQLite)
    ├─ Hit → Return cached data (offline)
    └─ Miss → Fetch from server
              ↓
         External Server
              ↓
         Cache result (SQLite)
              ↓
         Return to app
```

### Technology Stack
- **Frontend**: Flutter 3.16.0
- **Backend**: External FastAPI (same as v1)
- **Cache**: SQLite (local)
- **Communication**: HTTP/HTTPS REST API

---

## 📦 What's Included

### Features from v1-original
✅ All v1 features
✅ External backend integration
✅ JWT authentication
✅ Material Design 3 UI

### New in v2-hybrid
✅ **SQLite cache** - Store fetched data locally
✅ **Offline viewing** - View cached data without internet
✅ **Smart sync** - Auto-update when online
✅ **Cache management** - Clear, refresh controls
✅ **Connectivity detection** - Auto-switch online/offline

### NOT Included
❌ Embedded Python backend
❌ Embedded tools (all run on server)
❌ Full offline tool execution

---

## 📊 Technical Specifications

### APK Size: ~25MB
- Flutter runtime: ~15MB
- App code: ~8MB
- SQLite: ~2MB

### System Requirements
- Android 7.0+ (API 24)
- RAM: 1GB
- Storage: 60MB (with cache)
- Internet: Required for first use, optional after

### Offline Capability
- **Offline**: ~40%
- **What works offline**:
  - View cached tools
  - View cached jobs
  - View cached results
- **What needs internet**:
  - Execute new tools
  - Fetch fresh data
  - Authentication (first time)

---

## 🎯 Use Cases

### ✅ When to Use v2-hybrid

- **Intermittent connectivity** - Sometimes online, sometimes not
- **View previous results offline** - Access cached data
- **Transition from v1 to v3** - Gradual migration
- **Low-end devices** - Can't handle embedded backend
- **Testing offline UX** - Before committing to full embedded

### ❌ When NOT to Use

- **Always offline** → Use v3-lite, v4-standard, or v5-full
- **No server available** → Use embedded versions
- **Full offline needed** → Use v3+

---

## 📊 Comparison

| Feature | v1-original | v2-hybrid | v3-lite |
|---------|-------------|-----------|---------|
| APK Size | 20MB | 25MB | 50MB |
| Backend | External | External | Embedded |
| Cache | No | Yes (SQLite) | N/A |
| Offline | 0% | 40% | 100% |
| Tools | 0 local | 0 local | 12 local |
| Internet | Required | Recommended | Not required |

---

## 🔧 Implementation Notes

### Cache Strategy

**What to Cache**:
- Tool definitions
- Job history (last 100)
- Job results (last 50)
- User profile
- Tool parameters

**Cache Invalidation**:
- TTL: 24 hours for tool definitions
- TTL: 1 hour for job results
- Manual refresh available
- Auto-clear on logout

### Database Schema

```sql
CREATE TABLE cache_tools (
  id TEXT PRIMARY KEY,
  data TEXT,
  cached_at TIMESTAMP,
  expires_at TIMESTAMP
);

CREATE TABLE cache_jobs (
  id TEXT PRIMARY KEY,
  data TEXT,
  cached_at TIMESTAMP
);

CREATE TABLE cache_results (
  job_id TEXT PRIMARY KEY,
  data TEXT,
  cached_at TIMESTAMP
);
```

---

## 🚀 Development Required

This version requires implementation of:

1. **SQLite integration** (sqflite package)
2. **Cache service layer**
3. **Connectivity detection** (connectivity_plus)
4. **Offline UI indicators**
5. **Cache management screen**

Estimated effort: 1-2 days

---

## 📊 Performance Metrics

### With Cache (Offline)
- Tool listing: Instant (cached)
- Job history: Instant (cached)
- Results viewing: Instant (cached)

### Without Cache (Online)
- Same as v1-original
- Plus cache write overhead (~100ms)

---

## 🔄 Migration

### From v1-original to v2-hybrid
- Add SQLite dependency
- Implement cache layer
- Add offline indicators
- Test offline mode

### From v2-hybrid to v3-lite
- Remove external backend dependency
- Add embedded backend
- Migrate cache to full database
- Enable offline tool execution

---

**Version**: v2-hybrid
**Status**: ⚙️ Conceptual
**APK**: ~25MB
**Offline**: 40% (viewing only)
**Purpose**: Bridge between external and embedded

**Good for intermittent connectivity scenarios!** 🔄
