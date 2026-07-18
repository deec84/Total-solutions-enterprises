import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:parkshield_mobile/src/core/localization/domain_labels.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/recommendations/data/parking_recommendations_api.dart';
import 'package:parkshield_mobile/src/features/recommendations/domain/parking_recommendation.dart';
import 'package:url_launcher/url_launcher.dart';

class ParkingRecommendationsPage extends StatefulWidget {
  const ParkingRecommendationsPage({
    required this.apiBaseUrl,
    required this.latitude,
    required this.longitude,
    this.api,
    super.key,
  });

  final String apiBaseUrl;
  final double latitude;
  final double longitude;
  final ParkingRecommendationsApi? api;

  @override
  State<ParkingRecommendationsPage> createState() =>
      _ParkingRecommendationsPageState();
}

class _ParkingRecommendationsPageState
    extends State<ParkingRecommendationsPage> {
  final TextEditingController _maxPrice = TextEditingController();
  late final ParkingRecommendationsApi _api;
  ParkingRecommendationList? _result;
  int _radiusMeters = 1500;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _api = widget.api ??
        ParkingRecommendationsApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
  }

  @override
  void dispose() {
    _api.close();
    _maxPrice.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text(context.l10n.recommendationsTitle,
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(context.l10n.recommendationsIntro),
          const SizedBox(height: 20),
          DropdownButtonFormField<int>(
            initialValue: _radiusMeters,
            decoration: InputDecoration(
              labelText: context.l10n.maximumWalkingDistance,
              border: const OutlineInputBorder(),
            ),
            items: <DropdownMenuItem<int>>[
              DropdownMenuItem(value: 500, child: Text(context.l10n.meters500)),
              DropdownMenuItem(
                  value: 1000, child: Text(context.l10n.kilometer1)),
              DropdownMenuItem(
                  value: 1500, child: Text(context.l10n.kilometers15)),
              DropdownMenuItem(
                  value: 3000, child: Text(context.l10n.kilometers3)),
            ],
            onChanged: (int? value) {
              if (value != null) setState(() => _radiusMeters = value);
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _maxPrice,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: InputDecoration(
              labelText: context.l10n.maximumHourlyPrice,
              prefixText: '\$ ',
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _loading ? null : _search,
            icon: const Icon(Icons.local_parking_outlined),
            label: Text(context.l10n.findSaferParking),
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(24),
              child: Center(child: CircularProgressIndicator()),
            ),
          if (_error case final String message)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(message,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          if (_result case final ParkingRecommendationList result) ...<Widget>[
            if (result.options.isEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 20),
                child: Text(context.l10n.noVerifiedOptions),
              ),
            ...result.options.map(
              (ParkingRecommendation option) =>
                  _RecommendationCard(option: option),
            ),
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Text(result.disclaimer,
                  style: Theme.of(context).textTheme.bodySmall),
            ),
          ],
        ],
      );

  Future<void> _search() async {
    final String priceText = _maxPrice.text.trim();
    final double? dollars =
        priceText.isEmpty ? null : double.tryParse(priceText);
    if (priceText.isNotEmpty && (dollars == null || dollars < 0)) {
      setState(() => _error = context.l10n.invalidHourlyPrice);
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final ParkingRecommendationList result = await _api.nearby(
        latitude: widget.latitude,
        longitude: widget.longitude,
        radiusMeters: _radiusMeters,
        maxHourlyPriceCents: dollars == null ? null : (dollars * 100).round(),
      );
      if (mounted) setState(() => _result = result);
    } on Exception {
      if (mounted) {
        setState(() => _error = context.l10n.recommendationsUnavailable);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}

class _RecommendationCard extends StatelessWidget {
  const _RecommendationCard({required this.option});

  final ParkingRecommendation option;

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(top: 16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Row(
                children: <Widget>[
                  Expanded(
                    child: Text(option.name,
                        style: Theme.of(context).textTheme.titleMedium),
                  ),
                  Chip(
                      label:
                          Text(context.l10n.matchScore(option.rankingScore))),
                ],
              ),
              Text(option.address),
              const SizedBox(height: 8),
              Text(context.l10n.walkSafety(
                option.walkingDistanceMeters,
                option.safetyScore,
              )),
              Text(option.hourlyPriceCents == null
                  ? context.l10n.priceNotVerified
                  : context.l10n.pricePerHour(
                      NumberFormat.simpleCurrency(
                        locale: context.l10n.localeName,
                        name: 'USD',
                      ).format(option.hourlyPriceCents! / 100),
                    )),
              if (option.availableSpaces != null)
                Text(context.l10n.spacesAvailable(option.availableSpaces!)),
              ...option.reasons.map(
                (String reason) => Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text('• $reason'),
                ),
              ),
              const SizedBox(height: 8),
              Text(context.l10n.sourceConfidence(
                localizedProvenance(context.l10n, option.provenance),
                (option.confidence * 100).round(),
              )),
              const SizedBox(height: 8),
              FilledButton.tonalIcon(
                onPressed: () => launchUrl(
                  Uri.parse(option.navigationUrl),
                  mode: LaunchMode.externalApplication,
                ),
                icon: const Icon(Icons.navigation_outlined),
                label: Text(context.l10n.navigate),
              ),
            ],
          ),
        ),
      );
}
