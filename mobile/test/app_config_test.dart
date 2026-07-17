import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/src/core/config/app_config.dart';

void main() {
  test('release configuration accepts contracted HTTPS services', () {
    const config = AppConfig(
      apiBaseUrl: 'https://api.parkshield.ai',
      mapTileUrl: 'https://tiles.parkshield.ai/{z}/{x}/{y}.png',
    );

    expect(config.validateForRelease, returnsNormally);
  });

  test('release configuration rejects a local API', () {
    const config = AppConfig(
      apiBaseUrl: 'http://localhost:8000',
      mapTileUrl: 'https://tiles.parkshield.ai/{z}/{x}/{y}.png',
    );

    expect(config.validateForRelease, throwsStateError);
  });

  test('release configuration rejects the public OSM tile service', () {
    const config = AppConfig(
      apiBaseUrl: 'https://api.parkshield.ai',
      mapTileUrl: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    );

    expect(config.validateForRelease, throwsStateError);
  });
}
