import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/app.dart';
import 'package:parkshield_mobile/src/core/config/app_config.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  const config = AppConfig.fromEnvironment();
  if (kReleaseMode) {
    config.validateForRelease();
  }
  runApp(const ParkShieldApp(config: config));
}
