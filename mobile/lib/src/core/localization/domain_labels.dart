import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';

String localizedProvenance(AppLocalizations l10n, String value) =>
    switch (value) {
      'official' || 'official_data' => l10n.provenanceOfficialData,
      'ai_prediction' || 'prediction' => l10n.provenanceAiPrediction,
      'community_verified' => l10n.provenanceCommunityVerified,
      'estimated' => l10n.provenanceEstimated,
      _ => _humanize(value),
    };

String localizedRiskLevel(AppLocalizations l10n, String value) =>
    switch (value) {
      'very_safe' => l10n.riskVerySafe,
      'safe' => l10n.riskSafe,
      'read_signs' || 'caution' => l10n.riskReadSigns,
      'high_risk' || 'high' => l10n.riskHigh,
      'very_high_risk' || 'very_high' => l10n.riskVeryHigh,
      'do_not_park' || 'critical' => l10n.riskDoNotPark,
      _ => _humanize(value),
    };

String localizedMachineValue(String value) => _humanize(value);

String localizedIntent(AppLocalizations l10n, String value) => switch (value) {
      'can_i_park_here' || 'parking_legality' => l10n.canIParkHere,
      _ => _humanize(value),
    };

String _humanize(String value) => value
    .split('_')
    .where((String word) => word.isNotEmpty)
    .map((String word) => '${word[0].toUpperCase()}${word.substring(1)}')
    .join(' ');
