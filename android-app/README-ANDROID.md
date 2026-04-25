# CampusFix Android App

This folder contains a proper Android Studio project that wraps the CampusFix web app in a native Android application shell.

## What it does

- Loads CampusFix in a `WebView`
- Supports pull-to-refresh
- Keeps in-app navigation inside the Android app
- Uses a launcher icon and Android theme
- Lets you change the backend URL without editing Kotlin code

## Before building

You need:

- Android Studio installed
- Android SDK for API 34
- JDK 17

## Important backend requirement

This Android app needs the Flask server to be reachable from your phone.

For local testing on the same Wi‑Fi:

1. Start Flask so it listens on your LAN:
   ```powershell
   $env:CAMPUSFIX_HOST="0.0.0.0"
   .\.venv\Scripts\python.exe app.py
   ```
2. Find your laptop IP address, for example `192.168.1.20`
3. In [gradle.properties](/c:/Users/bhupe/OneDrive/Desktop/campusfix/android-app/gradle.properties), change:
   ```properties
   campusfixBaseUrl=http://10.0.2.2:5000/
   ```
   to:
   ```properties
   campusfixBaseUrl=http://192.168.1.20:5000/
   ```

`10.0.2.2` only works for the Android emulator, not a real phone.

## Build APK

1. Open [android-app](/c:/Users/bhupe/OneDrive/Desktop/campusfix/android-app) in Android Studio
2. Let Gradle sync
3. Build:
   `Build > Build Bundle(s) / APK(s) > Build APK(s)`

The debug APK will be generated under:

`app/build/outputs/apk/debug/`
