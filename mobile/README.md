# ParkShield Mobile

Flutter client following feature-first Clean Architecture. The reproducible CI baseline is Flutter 3.44.6 with its bundled Dart SDK.

Authentication tokens are stored with `flutter_secure_storage`, which maps to Keychain on iOS and encrypted platform storage on Android. Never replace it with shared preferences or source-controlled values.

```sh
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=PARKSHIELD_API_BASE_URL=http://localhost:8000
```

Release builds require HTTPS API and contracted map-tile endpoints through `PARKSHIELD_API_BASE_URL` and `PARKSHIELD_MAP_TILE_URL` dart defines. The public OSM tile service is accepted only for development.

The protected `mobile-release` workflow builds a signed Android App Bundle and iOS IPA. Its `mobile-production` environment stores `ANDROID_KEYSTORE_BASE64`, alias/password values, Apple distribution certificate/password, provisioning profile, keychain password, `APPLE_TEAM_ID`, `API_BASE_URL`, and `MAP_TILE_URL`. Release signing fails closed if credentials are absent; debug keys are never used for release.

The checked-in iOS project uses Flutter's Swift Package Manager integration. A full Xcode installation and Apple signing identity are still required for native/signed builds; CocoaPods is not a prerequisite for this project layout.
