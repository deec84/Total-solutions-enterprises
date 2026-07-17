import 'package:flutter/material.dart';
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
          Text('Safer parking nearby',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
            'Options balance walking distance, price, safety, towing history, '
            'ratings, and current availability.',
          ),
          const SizedBox(height: 20),
          DropdownButtonFormField<int>(
            initialValue: _radiusMeters,
            decoration: const InputDecoration(
              labelText: 'Maximum walking distance',
              border: OutlineInputBorder(),
            ),
            items: const <DropdownMenuItem<int>>[
              DropdownMenuItem(value: 500, child: Text('500 meters')),
              DropdownMenuItem(value: 1000, child: Text('1 kilometer')),
              DropdownMenuItem(value: 1500, child: Text('1.5 kilometers')),
              DropdownMenuItem(value: 3000, child: Text('3 kilometers')),
            ],
            onChanged: (int? value) {
              if (value != null) setState(() => _radiusMeters = value);
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _maxPrice,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Maximum hourly price (optional)',
              prefixText: '\$ ',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _loading ? null : _search,
            icon: const Icon(Icons.local_parking_outlined),
            label: const Text('Find safer parking'),
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
              const Padding(
                padding: EdgeInsets.only(top: 20),
                child: Text('No verified options match these filters.'),
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
      setState(() => _error = 'Enter a valid maximum hourly price.');
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
        setState(() =>
            _error = 'Parking recommendations are temporarily unavailable.');
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
                  Chip(label: Text('Match ${option.rankingScore}')),
                ],
              ),
              Text(option.address),
              const SizedBox(height: 8),
              Text('${option.walkingDistanceMeters} m walk · '
                  'Safety ${option.safetyScore}/100'),
              Text(option.hourlyPriceCents == null
                  ? 'Price not verified'
                  : '\$${(option.hourlyPriceCents! / 100).toStringAsFixed(2)}/hour'),
              if (option.availableSpaces != null)
                Text('${option.availableSpaces} spaces reported available'),
              ...option.reasons.map(
                (String reason) => Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text('• $reason'),
                ),
              ),
              const SizedBox(height: 8),
              Text('Source: ${option.provenance} · '
                  '${(option.confidence * 100).round()}% confidence'),
              const SizedBox(height: 8),
              FilledButton.tonalIcon(
                onPressed: () => launchUrl(
                  Uri.parse(option.navigationUrl),
                  mode: LaunchMode.externalApplication,
                ),
                icon: const Icon(Icons.navigation_outlined),
                label: const Text('Navigate'),
              ),
            ],
          ),
        ),
      );
}
