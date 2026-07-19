import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:parkshield_mobile/src/core/localization/domain_labels.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/map/data/parking_map_api.dart';
import 'package:parkshield_mobile/src/features/map/domain/parking_zone.dart';

class ParkingMapPage extends StatefulWidget {
  const ParkingMapPage({
    required this.apiBaseUrl,
    required this.tileUrl,
    this.onCenterChanged,
    this.api,
    this.tileProvider,
    super.key,
  });

  final String apiBaseUrl;
  final String tileUrl;
  final ValueChanged<LatLng>? onCenterChanged;
  final ParkingMapApi? api;
  final TileProvider? tileProvider;

  @override
  State<ParkingMapPage> createState() => _ParkingMapPageState();
}

class _ParkingMapPageState extends State<ParkingMapPage> {
  late final ParkingMapApi _api;
  Timer? _debounce;
  List<ParkingZone> _zones = <ParkingZone>[];
  bool _loading = true;
  String? _error;
  LatLng _center = const LatLng(25.7617, -80.1918);
  final Set<String> _visibleTypes = <String>{
    'general',
    'resident_only',
    'private_property',
    'commercial',
    'towing_hotspot',
  };

  @override
  void initState() {
    super.initState();
    _api = widget.api ??
        ParkingMapApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
    _load(west: -80.35, south: 25.65, east: -80.05, north: 25.95);
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Stack(
        children: <Widget>[
          FlutterMap(
            options: MapOptions(
              initialCenter: const LatLng(25.7617, -80.1918),
              initialZoom: 13,
              minZoom: 4,
              maxZoom: 19,
              onPositionChanged: _positionChanged,
            ),
            children: <Widget>[
              TileLayer(
                urlTemplate: widget.tileUrl,
                tileProvider: widget.tileProvider,
                userAgentPackageName: 'ai.parkshield.parkshield_mobile',
              ),
              PolygonLayer(
                polygons: _zones
                    .where((ParkingZone zone) =>
                        _visibleTypes.contains(zone.zoneType))
                    .map(
                      (ParkingZone zone) => Polygon(
                        points: zone.points,
                        color: _scoreColor(zone.parkingScore)
                            .withValues(alpha: 0.42),
                        borderColor: _scoreColor(zone.parkingScore),
                        borderStrokeWidth: 2,
                        label: '${zone.parkingScore}',
                      ),
                    )
                    .toList(growable: false),
              ),
              const RichAttributionWidget(
                attributions: <SourceAttribution>[
                  TextSourceAttribution('OpenStreetMap contributors'),
                ],
              ),
            ],
          ),
          Positioned(
            top: 12,
            left: 12,
            right: 12,
            child: Column(
              children: <Widget>[
                const _RiskLegend(),
                const SizedBox(height: 8),
                _ZoneFilters(
                  selected: _visibleTypes,
                  onChanged: (String type, bool selected) {
                    setState(() {
                      if (selected) {
                        _visibleTypes.add(type);
                      } else {
                        _visibleTypes.remove(type);
                      }
                    });
                  },
                ),
              ],
            ),
          ),
          Positioned(
            right: 16,
            bottom: 24,
            child: FloatingActionButton.extended(
              onPressed: _decideAtCenter,
              icon: const Icon(Icons.local_parking),
              label: Text(context.l10n.canIParkHere),
            ),
          ),
          if (_loading) const Center(child: CircularProgressIndicator()),
          if (_error case final String message)
            Positioned(
              left: 16,
              right: 16,
              bottom: 24,
              child: Material(
                color: Theme.of(context).colorScheme.errorContainer,
                borderRadius: BorderRadius.circular(12),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Text(message, textAlign: TextAlign.center),
                ),
              ),
            ),
        ],
      );

  void _positionChanged(MapCamera camera, bool hasGesture) {
    _center = camera.center;
    widget.onCenterChanged?.call(_center);
    if (!hasGesture) return;
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 450), () {
      final LatLngBounds bounds = camera.visibleBounds;
      _load(
        west: bounds.west,
        south: bounds.south,
        east: bounds.east,
        north: bounds.north,
      );
    });
  }

  Future<void> _decideAtCenter() async {
    setState(() => _loading = true);
    try {
      final ParkingZone? zone = await _api.decision(
        latitude: _center.latitude,
        longitude: _center.longitude,
      );
      if (!mounted) return;
      await showModalBottomSheet<void>(
        context: context,
        showDragHandle: true,
        builder: (BuildContext context) => _ParkingDecisionSheet(zone: zone),
      );
    } on Exception {
      if (mounted) {
        setState(() => _error = context.l10n.mapEvaluationError);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _load({
    required double west,
    required double south,
    required double east,
    required double north,
  }) async {
    if (mounted) setState(() => _loading = true);
    try {
      final List<ParkingZone> zones = await _api.viewport(
        west: west,
        south: south,
        east: east,
        north: north,
      );
      if (!mounted) return;
      setState(() {
        _zones = zones;
        _error = null;
      });
    } on Exception {
      if (mounted) {
        setState(() => _error = context.l10n.mapUnavailable);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Color _scoreColor(int score) => switch (score) {
        >= 90 => const Color(0xFF178A4A),
        >= 75 => const Color(0xFF63A83D),
        >= 55 => const Color(0xFFF2C94C),
        >= 35 => const Color(0xFFF2994A),
        > 0 => const Color(0xFFEB5757),
        _ => const Color(0xFF7A0019),
      };
}

class _RiskLegend extends StatelessWidget {
  const _RiskLegend();

  @override
  Widget build(BuildContext context) => Material(
        elevation: 2,
        borderRadius: BorderRadius.circular(14),
        color: Theme.of(context).colorScheme.surface.withValues(alpha: 0.94),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Wrap(
            alignment: WrapAlignment.spaceBetween,
            spacing: 10,
            runSpacing: 6,
            children: <Widget>[
              _LegendItem(const Color(0xFF178A4A), context.l10n.riskSafe),
              _LegendItem(const Color(0xFFF2C94C), context.l10n.riskReadSigns),
              _LegendItem(const Color(0xFFF2994A), context.l10n.riskHigh),
              _LegendItem(const Color(0xFF7A0019), context.l10n.riskDoNotPark),
            ],
          ),
        ),
      );
}

class _LegendItem extends StatelessWidget {
  const _LegendItem(this.color, this.label);

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Container(width: 10, height: 10, color: color),
          const SizedBox(width: 4),
          Text(label, style: Theme.of(context).textTheme.labelSmall),
        ],
      );
}

class _ZoneFilters extends StatelessWidget {
  const _ZoneFilters({required this.selected, required this.onChanged});

  final Set<String> selected;
  final void Function(String type, bool selected) onChanged;

  @override
  Widget build(BuildContext context) {
    final Map<String, String> labels = <String, String>{
      'general': context.l10n.zoneGeneral,
      'resident_only': context.l10n.zoneResidents,
      'private_property': context.l10n.zonePrivate,
      'commercial': context.l10n.zoneCommercial,
      'towing_hotspot': context.l10n.zoneTowHotspots,
    };
    return Material(
      color: Colors.transparent,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: labels.entries
              .map(
                (MapEntry<String, String> entry) => Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: FilterChip(
                    label: Text(entry.value),
                    selected: selected.contains(entry.key),
                    onSelected: (bool value) => onChanged(entry.key, value),
                  ),
                ),
              )
              .toList(growable: false),
        ),
      ),
    );
  }
}

class _ParkingDecisionSheet extends StatelessWidget {
  const _ParkingDecisionSheet({required this.zone});

  final ParkingZone? zone;

  @override
  Widget build(BuildContext context) {
    final ParkingZone? value = zone;
    if (value == null) {
      return SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              const Icon(Icons.warning_amber_rounded, size: 48),
              const SizedBox(height: 12),
              Text(
                context.l10n.noVerifiedLocationData,
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                CircleAvatar(
                  radius: 30,
                  child: Text('${value.parkingScore}',
                      style: const TextStyle(fontSize: 20)),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(value.name,
                          style: Theme.of(context).textTheme.titleLarge),
                      Text(localizedRiskLevel(context.l10n, value.riskLevel)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(value.restrictionSummary ?? context.l10n.noRestrictionSummary),
            const SizedBox(height: 12),
            Text(context.l10n.sourceWithValue(
              localizedProvenance(context.l10n, value.provenance),
            )),
            Text(context.l10n
                .confidencePercent((value.confidence * 100).round())),
            if (value.averageTowingCostCents case final int cents)
              Text(context.l10n.estimatedTowingCost(
                '\$${(cents / 100).toStringAsFixed(2)}',
              )),
            if (value.towingHotspot)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(context.l10n.knownTowingHotspot,
                    style: const TextStyle(fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }
}
