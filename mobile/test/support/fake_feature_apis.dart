import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:latlong2/latlong.dart';
import 'package:parkshield_mobile/src/features/admin/data/admin_api.dart';
import 'package:parkshield_mobile/src/features/admin/domain/admin_models.dart';
import 'package:parkshield_mobile/src/features/alerts/data/alerts_api.dart';
import 'package:parkshield_mobile/src/features/alerts/domain/alert_models.dart';
import 'package:parkshield_mobile/src/features/community/data/community_report_api.dart';
import 'package:parkshield_mobile/src/features/community/domain/community_report.dart';
import 'package:parkshield_mobile/src/features/map/data/parking_map_api.dart';
import 'package:parkshield_mobile/src/features/map/domain/parking_zone.dart';
import 'package:parkshield_mobile/src/features/parking_ai/data/parking_assistant_api.dart';
import 'package:parkshield_mobile/src/features/parking_ai/domain/parking_assessment.dart';
import 'package:parkshield_mobile/src/features/recommendations/data/parking_recommendations_api.dart';
import 'package:parkshield_mobile/src/features/recommendations/domain/parking_recommendation.dart';
import 'package:parkshield_mobile/src/features/recovery/data/tow_recovery_api.dart';
import 'package:parkshield_mobile/src/features/recovery/domain/tow_recovery.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/data/sign_scanner_api.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/domain/sign_scan_result.dart';

import 'memory_token_store.dart';

final MockClient unusedClient = MockClient(
  (http.Request request) async => throw StateError('unexpected network call'),
);

class FakeAdminApi extends AdminApi {
  FakeAdminApi({this.fail = false})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  int moderationCalls = 0;

  Never _failure() => throw Exception('administration unavailable');

  @override
  Future<MfaSetup> setupMfa() async => fail
      ? _failure()
      : const MfaSetup(
          secret: 'MFA-SECRET',
          provisioningUri: 'otpauth://totp/ParkShield',
        );

  @override
  Future<void> confirmMfa(String code) async {
    if (fail) _failure();
  }

  @override
  Future<AdminOverview> overview(String code) async => fail
      ? _failure()
      : const AdminOverview(
          users: 10,
          activeSessions: 4,
          pendingReports: 1,
          publishedReports: 8,
          rejectedReports: 2,
        );

  @override
  Future<List<ModerationReport>> moderationQueue(String code) async => fail
      ? _failure()
      : const <ModerationReport>[
          ModerationReport(
            id: 'report-1',
            category: 'towing',
            description: 'Tow truck observed',
            validationScore: 0.8,
          ),
        ];

  @override
  Future<AuditIntegrity> auditIntegrity(String code) async =>
      fail ? _failure() : const AuditIntegrity(valid: true, recordsChecked: 12);

  @override
  Future<void> moderate({
    required String reportId,
    required bool approved,
    required String reason,
    required String mfaCode,
  }) async {
    if (fail) _failure();
    moderationCalls += 1;
  }

  @override
  void close() {}
}

class FakeAlertsApi extends AlertsApi {
  FakeAlertsApi({this.fail = false, this.enabled = false})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  bool enabled;
  int updateCalls = 0;

  AlertPreferences get _preferences => AlertPreferences(
        parkingAlertsEnabled: enabled,
        backgroundLocationEnabled: enabled,
        quietStartHour: 22,
        quietEndHour: 7,
        timezone: 'America/New_York',
      );

  @override
  Future<AlertPreferences> preferences() async {
    if (fail) throw Exception('preferences unavailable');
    return _preferences;
  }

  @override
  Future<AlertPreferences> updatePreferences({
    required bool enabled,
    required int quietStartHour,
    required int quietEndHour,
    required String timezone,
  }) async {
    if (fail) throw Exception('preferences unavailable');
    this.enabled = enabled;
    updateCalls += 1;
    return _preferences;
  }

  @override
  void close() {}
}

class FakeCommunityReportApi extends CommunityReportApi {
  FakeCommunityReportApi({this.fail = false, this.status = 'pending'})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  String status;
  int submissions = 0;

  @override
  Future<CommunityReport> submit({
    required String category,
    required double latitude,
    required double longitude,
    required String description,
    dynamic photo,
  }) async {
    if (fail) throw Exception('submission unavailable');
    submissions += 1;
    return CommunityReport(
      id: 'report-1',
      status: status,
      validationScore: 0.8,
      expiresAt: DateTime.utc(2026, 8, 17),
    );
  }

  @override
  void close() {}
}

class FakeParkingMapApi extends ParkingMapApi {
  FakeParkingMapApi({this.fail = false, this.zone})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  ParkingZone? zone;

  @override
  Future<List<ParkingZone>> viewport({
    required double west,
    required double south,
    required double east,
    required double north,
  }) async {
    if (fail) throw Exception('map unavailable');
    return <ParkingZone>[if (zone != null) zone!];
  }

  @override
  Future<ParkingZone?> decision({
    required double latitude,
    required double longitude,
  }) async {
    if (fail) throw Exception('decision unavailable');
    return zone;
  }

  @override
  void close() {}
}

class FakeParkingAssistantApi extends ParkingAssistantApi {
  FakeParkingAssistantApi({this.fail = false, this.requiresReview = true})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  bool requiresReview;

  @override
  Future<ParkingAssessment> ask({
    required String question,
    required double latitude,
    required double longitude,
    required bool hasResidentPermit,
  }) async {
    if (fail) throw Exception('assistant unavailable');
    return ParkingAssessment(
      answer: 'Do not park here.',
      interpretedIntent: 'parking_legality',
      parkingScore: 20,
      riskLevel: 'very_high_risk',
      recommendation: 'do_not_park',
      provenance: 'official',
      confidence: 0.98,
      reasons: const <String>['Tow-away restriction'],
      disclaimer: 'Follow posted signs.',
      requiresHumanReview: requiresReview,
    );
  }

  @override
  void close() {}
}

class FakeParkingRecommendationsApi extends ParkingRecommendationsApi {
  FakeParkingRecommendationsApi({this.fail = false, this.empty = false})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  bool empty;

  @override
  Future<ParkingRecommendationList> nearby({
    required double latitude,
    required double longitude,
    required int radiusMeters,
    int? maxHourlyPriceCents,
  }) async {
    if (fail) throw Exception('recommendations unavailable');
    return ParkingRecommendationList(
      options: empty
          ? const <ParkingRecommendation>[]
          : const <ParkingRecommendation>[
              ParkingRecommendation(
                id: 'facility-1',
                name: 'Safe Garage',
                address: '100 Safe Way',
                walkingDistanceMeters: 200,
                hourlyPriceCents: 1200,
                safetyScore: 92,
                towingIncidentsPer1000: 2,
                rating: 4.7,
                availableSpaces: 10,
                capacity: 100,
                navigationUrl: 'https://maps.example.com/safe',
                provenance: 'official',
                confidence: 0.95,
                rankingScore: 87,
                reasons: <String>['Safety score 92/100.'],
              ),
            ],
      disclaimer: 'Confirm posted terms.',
    );
  }

  @override
  void close() {}
}

class FakeTowRecoveryApi extends TowRecoveryApi {
  FakeTowRecoveryApi({this.fail = false, this.found = true})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  bool found;

  @override
  Future<TowLookupResult> lookup({
    required String state,
    required String licensePlate,
    String? vinLastSix,
  }) async {
    if (fail) throw Exception('lookup unavailable');
    return TowLookupResult(
      found: found,
      message: found ? 'Verified record found.' : 'No record found.',
      record: found
          ? TowRecord(
              towCompany: 'City Tow',
              storageLocation: '100 Secure Lot',
              phoneNumber: '+1-305-555-0100',
              businessHours: 'Open 24 hours',
              requiredDocuments: const <String>['Photo ID'],
              estimatedFeesCents: 24500,
              paymentMethods: const <String>['Credit card'],
              navigationUrl: 'https://maps.example.com/tow',
              provenance: 'official',
              confidence: 0.98,
              lastVerifiedAt: DateTime.utc(2026, 7, 17),
            )
          : null,
      privacyNotice: 'Identifiers are not retained.',
    );
  }

  @override
  void close() {}
}

class FakeSignScannerApi extends SignScannerApi {
  FakeSignScannerApi({this.fail = false, this.requiresReview = true})
      : super(
          baseUrl: 'https://api.test',
          tokenStore: MemoryTokenStore(accessToken: 'token'),
          client: unusedClient,
        );

  bool fail;
  bool requiresReview;

  @override
  Future<SignScanResult> scan({
    required Uint8List bytes,
    required String filename,
    required String contentType,
  }) async {
    if (fail) throw Exception('scan unavailable');
    return SignScanResult(
      detectedText: 'NO PARKING',
      summary: 'Parking is prohibited.',
      restrictions: const <String>['No parking', 'Tow-away zone'],
      towingRiskScore: 95,
      confidence: 0.91,
      requiresHumanReview: requiresReview,
      disclaimer: 'Verify the physical sign.',
    );
  }

  @override
  void close() {}
}

const ParkingZone towingZone = ParkingZone(
  id: 'zone-1',
  name: 'Tow zone',
  points: <LatLng>[
    LatLng(25.7, -80.2),
    LatLng(25.7, -80.1),
    LatLng(25.8, -80.1),
  ],
  parkingScore: 20,
  riskLevel: 'very_high_risk',
  provenance: 'official',
  confidence: 1,
  zoneType: 'towing_hotspot',
  towingHotspot: true,
  restrictionSummary: 'Tow-away restriction',
  averageTowingCostCents: 25000,
);
