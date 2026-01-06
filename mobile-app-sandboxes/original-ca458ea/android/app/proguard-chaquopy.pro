# Chaquopy ProGuard Rules
# Keep all Python-related classes

-keep class com.chaquo.python.** { *; }
-keep class com.chaquo.python.android.** { *; }

# Keep Python modules
-keep class **.python.** { *; }

# Don't warn about Python native libraries
-dontwarn com.chaquo.python.**

# Keep attributes for Python reflection
-keepattributes *Annotation*
-keepattributes Signature
-keepattributes Exception

# Keep line numbers for debugging
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
