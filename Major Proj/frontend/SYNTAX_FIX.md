# ✅ SYNTAX ERROR FIXED

## Issue
```dart
if (_showOptionalFields) ..[  // ❌ Wrong syntax
  // widgets
],
```

## Solution
```dart
if (_showOptionalFields)
  const SizedBox(height: 16),
if (_showOptionalFields)
  TextField(...),
if (_showOptionalFields)
  const SizedBox(height: 16),
if (_showOptionalFields)
  TextField(...),
```

## What Changed
- Removed spread operator `...[]` 
- Used individual `if` statements for each widget
- This is the correct Dart syntax for conditional widgets in a Column

## File Fixed
`frontend/lib/screens/onboarding/insta_login.dart`

## Test Now
```bash
cd frontend
flutter run -d chrome
```

Should compile without errors! ✅
