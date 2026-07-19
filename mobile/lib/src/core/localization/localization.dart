import 'package:flutter/widgets.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';

extension LocalizedBuildContext on BuildContext {
  AppLocalizations get l10n => AppLocalizations.of(this);
}
