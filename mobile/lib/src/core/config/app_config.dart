class AppConfig {
  const AppConfig({
    required this.apiBaseUrl,
    this.mapTileUrl = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    this.productAnalyticsEnabled = false,
  });

  const AppConfig.fromEnvironment()
      : apiBaseUrl = const String.fromEnvironment(
          'PARKSHIELD_API_BASE_URL',
          defaultValue: 'http://localhost:8000',
        ),
        mapTileUrl = const String.fromEnvironment(
          'PARKSHIELD_MAP_TILE_URL',
          defaultValue: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        ),
        productAnalyticsEnabled = const bool.fromEnvironment(
          'PARKSHIELD_PRODUCT_ANALYTICS_ENABLED',
          defaultValue: false,
        );

  final String apiBaseUrl;
  final String mapTileUrl;
  final bool productAnalyticsEnabled;

  void validateForRelease() {
    final apiUri = Uri.tryParse(apiBaseUrl);
    if (apiUri == null || apiUri.scheme != 'https' || apiUri.host.isEmpty) {
      throw StateError('Release API URL must be an absolute HTTPS URL.');
    }
    final tileUri = Uri.tryParse(mapTileUrl);
    if (tileUri == null ||
        tileUri.scheme != 'https' ||
        tileUri.host.isEmpty ||
        !mapTileUrl.contains('{z}') ||
        !mapTileUrl.contains('{x}') ||
        !mapTileUrl.contains('{y}')) {
      throw StateError('Release map tile URL must be an HTTPS tile template.');
    }
    if (tileUri.host == 'tile.openstreetmap.org') {
      throw StateError(
          'Release builds require a contracted map tile provider.');
    }
  }
}
