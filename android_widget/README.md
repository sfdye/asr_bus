# ASR Bus Widget (Android)

A native Android home screen widget showing next shuttle bus arrival times for Avenue South Residence.

## Features

- 📍 Auto-detect nearest stop via GPS (opt-in)
- 📶 Works offline — schedule is embedded
- 🌏 English and Chinese based on device language
- 🔄 Auto-refresh every 5 minutes
- 🔧 Configurable stop selection and text size
- Reconfigurable via long-press on widget

## Development

### Prerequisites

- Android Studio (includes SDK, emulator, and JDK)

### Build & Run

```bash
cd android_widget
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew assembleDebug
```

Or open the project in Android Studio and click Run ▶.

### Test on Emulator

1. Run the app on the emulator
2. Long-press home screen → Widgets → "ASR Bus Widget" → drag to home screen
3. Choose a stop → tap Confirm

To test GPS auto-detect, set a mock location in Extended Controls → Location.

## Release Build

Build, zipalign, and sign in one step:

```bash
cd android_widget
JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home" ./gradlew assembleRelease \
  && PATH="/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin:$PATH" \
     /Users/lwan/Library/Android/sdk/build-tools/37.0.0/zipalign -f 4 \
     "app/build/outputs/apk/release/ASR Bus Widget.apk" ~/Desktop/ASR-Bus-Widget-aligned.apk \
  && PATH="/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin:$PATH" \
     /Users/lwan/Library/Android/sdk/build-tools/37.0.0/apksigner sign \
     --ks ~/asr-bus-widget.jks --ks-key-alias asrbus \
     --out ~/Desktop/"ASR Bus Widget.apk" ~/Desktop/ASR-Bus-Widget-aligned.apk \
  && rm ~/Desktop/ASR-Bus-Widget-aligned.apk
```

The signed APK will be at `~/Desktop/ASR Bus Widget.apk`.

### Keystore

The signing keystore (`asr-bus-widget.jks`) is not committed to the repo. To generate a new one:

```bash
/Applications/Android\ Studio.app/Contents/jbr/Contents/Home/bin/keytool -genkey -v -keystore ~/asr-bus-widget.jks -keyalg RSA -keysize 2048 -validity 10000 -alias asrbus
```

## Distribution

Share the signed APK directly (Telegram, WhatsApp, GitHub Release). Users install by tapping the file and enabling "Install from unknown sources" if prompted.
