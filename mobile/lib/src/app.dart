import 'package:flutter/material.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/core/config/app_config.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_gate.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class ParkShieldApp extends StatelessWidget {
  const ParkShieldApp({
    super.key,
    this.config = const AppConfig.fromEnvironment(),
    this.authGateway,
    this.linkStream,
    this.locale,
  });

  final AppConfig config;
  final AuthGateway? authGateway;
  final Stream<Uri>? linkStream;
  final Locale? locale;

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        onGenerateTitle: (BuildContext context) =>
            AppLocalizations.of(context).appTitle,
        locale: locale,
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF146C43)),
          useMaterial3: true,
        ),
        home: AuthGate(
          apiBaseUrl: config.apiBaseUrl,
          mapTileUrl: config.mapTileUrl,
          gateway: authGateway,
          linkStream: linkStream,
        ),
      );
}
