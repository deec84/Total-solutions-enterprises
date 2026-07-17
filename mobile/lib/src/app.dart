import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/core/config/app_config.dart';
import 'package:parkshield_mobile/src/features/auth/presentation/auth_gate.dart';
import 'package:parkshield_mobile/src/features/auth/domain/auth_session.dart';

class ParkShieldApp extends StatelessWidget {
  const ParkShieldApp({
    super.key,
    this.config = const AppConfig.fromEnvironment(),
    this.authGateway,
    this.linkStream,
  });

  final AppConfig config;
  final AuthGateway? authGateway;
  final Stream<Uri>? linkStream;

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'ParkShield AI',
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
