# Flutter optimization rules
-keep class io.flutter.** { *; }
-keep class androidx.lifecycle.** { *; }
-dontwarn androidx.lifecycle.**
-keep class com.google.firebase.** { *; }
-dontwarn com.google.firebase.**
-assumenosideeffects class io.flutter.util.Trace { *; }