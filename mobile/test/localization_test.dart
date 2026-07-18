import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:parkshield_mobile/src/core/localization/domain_labels.dart';

void main() {
  test('English and Spanish catalogs expose trusted provenance labels', () {
    final AppLocalizations english = lookupAppLocalizations(const Locale('en'));
    final AppLocalizations spanish = lookupAppLocalizations(const Locale('es'));

    expect(localizedProvenance(english, 'official_data'), 'Official Data');
    expect(localizedProvenance(spanish, 'official_data'), 'Datos oficiales');
    expect(localizedRiskLevel(english, 'do_not_park'), 'Do not park');
    expect(localizedRiskLevel(spanish, 'do_not_park'), 'No estaciones');
  });

  test('unsupported machine values remain visibly labeled without fabrication',
      () {
    final AppLocalizations spanish = lookupAppLocalizations(const Locale('es'));

    expect(localizedProvenance(spanish, 'partner_feed'), 'Partner Feed');
    expect(localizedIntent(spanish, 'future_intent'), 'Future Intent');
  });
}
