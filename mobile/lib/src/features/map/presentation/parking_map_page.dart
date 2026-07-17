import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
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
          const Positioned(top: 12, left: 12, right: 12, child: _RiskLegend()),
          Positioned(
            top: 68,
            left: 12,
            right: 12,
            child: _ZoneFilters(
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
          ),
          Positioned(
            right: 16,
            bottom: 24,
            child: FloatingActionButton.extended(
              onPressed: _decideAtCenter,
              icon: const Icon(Icons.local_parking),
              label: const Text('Can I park here?'),
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
        setState(() => _error =
            'Unable to evaluate this location. Read all posted signs.');
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
        setState(
            () => _error = 'Parking intelligence is temporarily unavailable.');
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
        child: const Padding(
          padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: <Widget>[
              _LegendItem(Color(0xFF178A4A), 'Safe'),
              _LegendItem(Color(0xFFF2C94C), 'Read signs'),
              _LegendItem(Color(0xFFF2994A), 'High risk'),
              _LegendItem(Color(0xFF7A0019), 'Do not park'),
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

  static const Map<String, String> _labels = <String, String>{
    'general': 'General',
    'resident_only': 'Residents',
    'private_property': 'Private',
    'commercial': 'Commercial',
    'towing_hotspot': 'Tow hotspots',
  };

  @override
  Widget build(BuildContext context) => Material(
        color: Colors.transparent,
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: _labels.entries
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

class _ParkingDecisionSheet extends StatelessWidget {
  const _ParkingDecisionSheet({required this.zone});

  final ParkingZone? zone;

  @override
  Widget build(BuildContext context) {
    final ParkingZone? value = zone;
    if (value == null) {
      return const SafeArea(
        child: Padding(
          padding: EdgeInsets.fromLTRB(24, 8, 24, 32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Icon(Icons.warning_amber_rounded, size: 48),
              SizedBox(height: 12),
              Text(
                'No verified data covers this location. Read every posted sign before parking.',
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
                      Text(_label(value.riskLevel)),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Text(value.restrictionSummary ??
                'No restriction summary is available.'),
            const SizedBox(height: 12),
            Text('Source: ${_label(value.provenance)}'),
            Text('Confidence: ${(value.confidence * 100).round()}%'),
            if (value.averageTowingCostCents case final int cents)
              Text(
                  'Estimated towing cost: \$${(cents / 100).toStringAsFixed(2)}'),
            if (value.towingHotspot)
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Text('Known towing hotspot',
                    style: TextStyle(fontWeight: FontWeight.bold)),
              ),
          ],
        ),
      ),
    );
  }

  String _label(String value) => value
      .split('_')
      .map((String word) => '${word[0].toUpperCase()}${word.substring(1)}')
      .join(' ');
}
