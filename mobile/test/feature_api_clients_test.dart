import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker/image_picker.dart';
import 'package:parkshield_mobile/src/features/admin/data/admin_api.dart';
import 'package:parkshield_mobile/src/features/alerts/data/alerts_api.dart';
import 'package:parkshield_mobile/src/features/community/data/community_report_api.dart';
import 'package:parkshield_mobile/src/features/map/data/parking_map_api.dart';
import 'package:parkshield_mobile/src/features/parking_ai/data/parking_assistant_api.dart';
import 'package:parkshield_mobile/src/features/recommendations/data/parking_recommendations_api.dart';
import 'package:parkshield_mobile/src/features/recovery/data/tow_recovery_api.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/data/sign_scanner_api.dart';

import 'support/memory_token_store.dart';

void main() {
  late MemoryTokenStore tokenStore;

  setUp(() {
    tokenStore = MemoryTokenStore(accessToken: 'access-token');
  });

  test('feature clients honor authenticated success contracts', () async {
    final List<http.Request> requests = <http.Request>[];
    final MockClient client = MockClient((http.Request request) async {
      requests.add(request);
      expect(request.headers['authorization'], 'Bearer access-token');
      return _successResponse(request);
    });

    final AdminApi admin = AdminApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: client,
    );
    expect((await admin.setupMfa()).secret, 'SECRET');
    await admin.confirmMfa('123456');
    expect((await admin.overview('123456')).users, 10);
    expect(await admin.moderationQueue('123456'), hasLength(1));
    expect((await admin.auditIntegrity('123456')).valid, isTrue);
    await admin.moderate(
      reportId: 'report-1',
      approved: true,
      reason: 'Verified photo',
      mfaCode: '123456',
    );

    final AlertsApi alerts = AlertsApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: client,
    );
    expect((await alerts.preferences()).parkingAlertsEnabled, isTrue);
    expect(
      (await alerts.updatePreferences(
        enabled: true,
        quietStartHour: 22,
        quietEndHour: 7,
        timezone: 'America/New_York',
      ))
          .backgroundLocationEnabled,
      isTrue,
    );
    expect((await alerts.evaluate(25.7, -80.2)).shouldAlert, isTrue);

    final CommunityReportApi community = CommunityReportApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: client,
    );
    expect(
      (await community.submit(
        category: 'towing',
        latitude: 25.7,
        longitude: -80.2,
        description: 'Tow truck observed beside this curb.',
      ))
          .status,
      'pending',
    );
    expect(
      (await community.submit(
        category: 'sign',
        latitude: 25.7,
        longitude: -80.2,
        description: 'A new restriction was posted.',
        photo: XFile.fromData(
          Uint8List.fromList(<int>[0xFF, 0xD8, 0xFF]),
          name: 'sign.jpg',
        ),
      ))
          .id,
      'report-1',
    );

    final ParkingMapApi map = ParkingMapApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: client,
    );
    expect(
      await map.viewport(west: -80.3, south: 25.6, east: -80.1, north: 25.8),
      hasLength(1),
    );
    expect(
      (await map.decision(latitude: 25.7, longitude: -80.2))?.parkingScore,
      20,
    );
    final ParkingMapApi emptyMap = ParkingMapApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: MockClient(
        (http.Request request) async => _json(<String, Object?>{'zone': null}),
      ),
    );
    expect(await emptyMap.decision(latitude: 0, longitude: 0), isNull);

    expect(
      (await ParkingAssistantApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: client,
      ).ask(
        question: 'Can I park here?',
        latitude: 25.7,
        longitude: -80.2,
        hasResidentPermit: false,
      ))
          .recommendation,
      'do_not_park',
    );

    expect(
      (await ParkingRecommendationsApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: client,
      ).nearby(
        latitude: 25.7,
        longitude: -80.2,
        radiusMeters: 1500,
        maxHourlyPriceCents: 2500,
      ))
          .options,
      hasLength(1),
    );

    expect(
      (await TowRecoveryApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: client,
      ).lookup(
        state: 'FL',
        licensePlate: 'ABC123',
        vinLastSix: '123456',
      ))
          .record
          ?.towCompany,
      'City Tow',
    );

    expect(
      (await SignScannerApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: client,
      ).scan(
        bytes: Uint8List.fromList(<int>[0xFF, 0xD8, 0xFF]),
        filename: 'sign.jpg',
        contentType: 'image',
      ))
          .summary,
      'Parking is prohibited.',
    );

    expect(
      requests.where((http.Request request) =>
          request.headers['content-type']?.startsWith('multipart/form-data') ??
          false),
      hasLength(2),
    );
    expect(
      requests
          .firstWhere(
            (http.Request request) =>
                request.url.path == '/api/v1/admin/overview',
          )
          .headers['x-parkshield-mfa'],
      '123456',
    );
    expect(
      jsonDecode(requests
          .firstWhere(
            (http.Request request) =>
                request.url.path == '/api/v1/recommendations/nearby',
          )
          .body),
      containsPair('max_hourly_price_cents', 2500),
    );

    admin.close();
    alerts.close();
    community.close();
    map.close();
    emptyMap.close();
  });

  test('feature clients fail closed for missing authentication', () async {
    final MemoryTokenStore missing = MemoryTokenStore();
    final MockClient unreachable = MockClient(
      (http.Request request) async => throw StateError('network must not run'),
    );

    final List<Future<Object?>> actions = <Future<Object?>>[
      AdminApi(
              baseUrl: 'https://api.test',
              tokenStore: missing,
              client: unreachable)
          .setupMfa(),
      AlertsApi(
              baseUrl: 'https://api.test',
              tokenStore: missing,
              client: unreachable)
          .preferences(),
      CommunityReportApi(
        baseUrl: 'https://api.test',
        tokenStore: missing,
        client: unreachable,
      ).submit(
        category: 'towing',
        latitude: 0,
        longitude: 0,
        description: 'description',
      ),
      ParkingMapApi(
              baseUrl: 'https://api.test',
              tokenStore: missing,
              client: unreachable)
          .viewport(west: 0, south: 0, east: 1, north: 1),
      ParkingMapApi(
              baseUrl: 'https://api.test',
              tokenStore: missing,
              client: unreachable)
          .decision(latitude: 0, longitude: 0),
      ParkingAssistantApi(
        baseUrl: 'https://api.test',
        tokenStore: missing,
        client: unreachable,
      ).ask(
        question: 'Can I park?',
        latitude: 0,
        longitude: 0,
        hasResidentPermit: false,
      ),
      ParkingRecommendationsApi(
        baseUrl: 'https://api.test',
        tokenStore: missing,
        client: unreachable,
      ).nearby(latitude: 0, longitude: 0, radiusMeters: 500),
      TowRecoveryApi(
              baseUrl: 'https://api.test',
              tokenStore: missing,
              client: unreachable)
          .lookup(state: 'FL', licensePlate: 'ABC123'),
      SignScannerApi(
              baseUrl: 'https://api.test',
              tokenStore: missing,
              client: unreachable)
          .scan(
        bytes: Uint8List(1),
        filename: 'sign.jpg',
        contentType: 'image/jpeg',
      ),
    ];

    for (final Future<Object?> action in actions) {
      await expectLater(action, throwsStateError);
    }
  });

  test('feature clients surface stable errors for rejected responses',
      () async {
    final MockClient rejected =
        MockClient((http.Request request) async => http.Response('', 503));
    final AdminApi admin = AdminApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: rejected,
    );
    final AlertsApi alerts = AlertsApi(
      baseUrl: 'https://api.test',
      tokenStore: tokenStore,
      client: rejected,
    );

    final List<Future<Object?>> actions = <Future<Object?>>[
      admin.setupMfa(),
      admin.confirmMfa('123456'),
      admin.overview('123456'),
      admin.moderationQueue('123456'),
      admin.auditIntegrity('123456'),
      admin.moderate(
        reportId: 'report-1',
        approved: false,
        reason: 'Insufficient evidence',
        mfaCode: '123456',
      ),
      alerts.preferences(),
      alerts.updatePreferences(
        enabled: false,
        quietStartHour: 22,
        quietEndHour: 7,
        timezone: 'America/New_York',
      ),
      alerts.evaluate(0, 0),
      CommunityReportApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).submit(
        category: 'towing',
        latitude: 0,
        longitude: 0,
        description: 'description',
      ),
      ParkingMapApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).viewport(west: 0, south: 0, east: 1, north: 1),
      ParkingMapApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).decision(latitude: 0, longitude: 0),
      ParkingAssistantApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).ask(
        question: 'Can I park?',
        latitude: 0,
        longitude: 0,
        hasResidentPermit: false,
      ),
      ParkingRecommendationsApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).nearby(latitude: 0, longitude: 0, radiusMeters: 500),
      TowRecoveryApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).lookup(state: 'FL', licensePlate: 'ABC123'),
      SignScannerApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: rejected,
      ).scan(
        bytes: Uint8List.fromList(<int>[1, 2, 3]),
        filename: 'sign.jpg',
        contentType: 'image/jpeg',
      ),
    ];

    for (final Future<Object?> action in actions) {
      await expectLater(action, throwsStateError);
    }
  });

  test('photo clients reject oversized evidence before transmission', () async {
    final Uint8List oversized = Uint8List(10 * 1024 * 1024 + 1);
    final MockClient unreachable = MockClient(
      (http.Request request) async => throw StateError('network must not run'),
    );

    await expectLater(
      CommunityReportApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: unreachable,
      ).submit(
        category: 'sign',
        latitude: 0,
        longitude: 0,
        description: 'description',
        photo: XFile.fromData(oversized, name: 'oversized.jpg'),
      ),
      throwsStateError,
    );
    await expectLater(
      SignScannerApi(
        baseUrl: 'https://api.test',
        tokenStore: tokenStore,
        client: unreachable,
      ).scan(
        bytes: oversized,
        filename: 'oversized.jpg',
        contentType: 'image/jpeg',
      ),
      throwsStateError,
    );
  });
}

http.Response _successResponse(http.Request request) {
  final String path = request.url.path;
  if (path == '/api/v1/admin/mfa/setup') {
    return _json(<String, Object>{
      'secret': 'SECRET',
      'provisioning_uri': 'otpauth://totp/ParkShield',
    });
  }
  if (path == '/api/v1/admin/mfa/confirm') return http.Response('', 204);
  if (path == '/api/v1/admin/overview') {
    return _json(<String, Object>{
      'users': 10,
      'active_sessions': 4,
      'pending_reports': 2,
      'published_reports': 8,
      'rejected_reports': 1,
    });
  }
  if (path == '/api/v1/reports/moderation') {
    return _jsonList(<Map<String, Object>>[
      <String, Object>{
        'id': 'report-1',
        'category': 'towing',
        'description': 'Tow truck observed',
        'validation_score': 0.8,
      },
    ]);
  }
  if (path == '/api/v1/admin/audit/integrity') {
    return _json(<String, Object>{'valid': true, 'records_checked': 12});
  }
  if (path.endsWith('/moderate')) return _json(<String, Object>{'ok': true});
  if (path == '/api/v1/notifications/preferences') {
    return _json(<String, Object>{
      'parking_alerts_enabled': true,
      'background_location_enabled': true,
      'quiet_start_hour': 22,
      'quiet_end_hour': 7,
      'timezone': 'America/New_York',
    });
  }
  if (path == '/api/v1/notifications/evaluate-location') {
    return _json(<String, Object>{
      'should_alert': true,
      'reason': 'Tow-away restriction',
      'parking_score': 20,
      'risk_level': 'very_high_risk',
      'estimated_towing_cost_cents': 25000,
      'deduplicated': false,
    });
  }
  if (path == '/api/v1/reports' || path == '/api/v1/reports/with-photo') {
    return _json(<String, Object>{
      'id': 'report-1',
      'status': 'pending',
      'validation_score': 0.7,
      'expires_at': '2026-08-17T12:00:00Z',
    }, 201);
  }
  if (path == '/api/v1/parking/zones') {
    return _json(<String, Object>{
      'zones': <Map<String, Object?>>[_zone()],
    });
  }
  if (path == '/api/v1/parking/decision') {
    return _json(<String, Object?>{'zone': _zone()});
  }
  if (path == '/api/v1/ai/parking-assistant') {
    return _json(<String, Object>{
      'answer': 'Do not park here.',
      'interpreted_intent': 'parking_legality',
      'parking_score': 20,
      'risk_level': 'very_high_risk',
      'recommendation': 'do_not_park',
      'provenance': 'official',
      'confidence': 1.0,
      'reasons': <String>['Tow-away restriction'],
      'disclaimer': 'Follow posted signs.',
      'requires_human_review': false,
    });
  }
  if (path == '/api/v1/recommendations/nearby') {
    return _json(<String, Object>{
      'disclaimer': 'Confirm posted terms.',
      'recommendations': <Map<String, Object?>>[
        <String, Object?>{
          'id': 'facility-1',
          'name': 'Safe Garage',
          'address': '100 Safe Way',
          'walking_distance_meters': 200,
          'hourly_price_cents': 1200,
          'safety_score': 92,
          'towing_incidents_per_1000': 2.0,
          'rating': 4.7,
          'available_spaces': 10,
          'capacity': 100,
          'navigation_url': 'https://maps.example.com/safe',
          'provenance': 'official',
          'confidence': 0.95,
          'ranking_score': 87,
          'reasons': <String>['Safety score 92/100.'],
        },
      ],
    });
  }
  if (path == '/api/v1/recovery/lookup') {
    return _json(<String, Object>{
      'found': true,
      'message': 'Verified record found.',
      'privacy_notice': 'Identifiers are not retained.',
      'record': <String, Object?>{
        'tow_company': 'City Tow',
        'storage_location': '100 Secure Lot',
        'phone_number': '+1-305-555-0100',
        'business_hours': 'Open 24 hours',
        'required_documents': <String>['Photo ID'],
        'estimated_fees_cents': 24500,
        'payment_methods': <String>['Credit card'],
        'navigation_url': 'https://maps.example.com/tow',
        'provenance': 'official',
        'confidence': 0.98,
        'last_verified_at': '2026-07-17T12:00:00Z',
      },
    });
  }
  if (path == '/api/v1/signs/scan') {
    return _json(<String, Object>{
      'redacted_text': 'NO PARKING',
      'summary': 'Parking is prohibited.',
      'restrictions': <String>['No parking'],
      'towing_risk_score': 95,
      'confidence': 0.91,
      'requires_human_review': false,
      'disclaimer': 'Verify the physical sign.',
    });
  }
  return http.Response('', 404);
}

Map<String, Object?> _zone() => <String, Object?>{
      'id': 'zone-1',
      'name': 'Tow zone',
      'geometry': <String, Object>{
        'type': 'Polygon',
        'coordinates': <Object>[
          <Object>[
            <double>[-80.2, 25.7],
            <double>[-80.1, 25.7],
            <double>[-80.2, 25.7],
          ],
        ],
      },
      'parking_score': 20,
      'risk_level': 'very_high_risk',
      'provenance': 'official',
      'confidence': 1.0,
      'zone_type': 'towing_hotspot',
      'towing_hotspot': true,
      'restriction_summary': 'Tow-away restriction',
      'average_towing_cost_cents': 25000,
    };

http.Response _json(Map<String, Object?> body, [int status = 200]) =>
    http.Response(
      jsonEncode(body),
      status,
      headers: <String, String>{'content-type': 'application/json'},
    );

http.Response _jsonList(List<Map<String, Object>> body) => http.Response(
      jsonEncode(body),
      200,
      headers: <String, String>{'content-type': 'application/json'},
    );
