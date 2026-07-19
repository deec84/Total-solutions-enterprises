import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:parkshield_mobile/l10n/generated/app_localizations.dart';
import 'package:image_picker/image_picker.dart';
import 'package:parkshield_mobile/src/features/admin/presentation/admin_page.dart';
import 'package:parkshield_mobile/src/features/alerts/application/parking_alert_coordinator.dart';
import 'package:parkshield_mobile/src/features/alerts/data/alerts_api.dart';
import 'package:parkshield_mobile/src/features/alerts/data/local_alert_notifier.dart';
import 'package:parkshield_mobile/src/features/alerts/presentation/alerts_page.dart';
import 'package:parkshield_mobile/src/features/community/presentation/community_report_page.dart';
import 'package:parkshield_mobile/src/features/map/presentation/parking_map_page.dart';
import 'package:parkshield_mobile/src/features/parking_ai/presentation/parking_assistant_page.dart';
import 'package:parkshield_mobile/src/features/recommendations/presentation/parking_recommendations_page.dart';
import 'package:parkshield_mobile/src/features/recovery/presentation/tow_recovery_page.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/presentation/sign_scanner_page.dart';

import 'support/fake_feature_apis.dart';

void main() {
  setUp(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
  });

  testWidgets('administration supports MFA, dashboard, moderation, and errors',
      (WidgetTester tester) async {
    final FakeAdminApi api = FakeAdminApi();
    await _pumpPage(
        tester, AdminPage(apiBaseUrl: 'https://api.test', api: api));

    await tester.enterText(find.byType(TextField).first, '123456');
    await tester.tap(find.text('Enroll MFA'));
    await _pumpFrames(tester);
    expect(find.text('MFA-SECRET'), findsOneWidget);

    await tester.tap(find.text('Confirm MFA'));
    await _pumpFrames(tester);
    expect(find.text('MFA enabled.'), findsOneWidget);

    await tester.tap(find.text('Open dashboard'));
    await _pumpFrames(tester);
    expect(find.text('Users: 10'), findsOneWidget);
    expect(find.text('Audit chain verified'), findsOneWidget);
    expect(find.text('towing'), findsOneWidget);

    await tester.tap(find.byType(PopupMenuButton<bool>));
    await _pumpFrames(tester);
    await tester.tap(find.text('Approve'));
    await _pumpFrames(tester);
    await tester.enterText(find.byType(TextField).last, 'Verified evidence');
    await tester.tap(find.text('Confirm'));
    await tester.pumpAndSettle();
    expect(api.moderationCalls, 1);

    api.fail = true;
    await tester.tap(find.text('Open dashboard'));
    await tester.pumpAndSettle();
    expect(
      find.text('Administrative request failed. Verify role and MFA.'),
      findsOneWidget,
    );
  });

  testWidgets('alert preferences activate, save, disable, and fail safely',
      (WidgetTester tester) async {
    final FakeAlertsApi api = FakeAlertsApi();
    final FakeParkingAlertCoordinator coordinator =
        FakeParkingAlertCoordinator(api);
    await _pumpPage(
      tester,
      AlertsPage(
        apiBaseUrl: 'https://api.test',
        api: api,
        coordinator: coordinator,
      ),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();
    expect(find.text('Preventive parking alerts are active.'), findsOneWidget);
    expect(coordinator.startCalls, 1);

    await tester.tap(find.text('Save quiet hours'));
    await tester.pumpAndSettle();
    expect(api.updateCalls, 2);

    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();
    expect(find.text('Preventive parking alerts are off.'), findsOneWidget);
    expect(coordinator.stopCalls, greaterThanOrEqualTo(1));

    api.fail = true;
    await tester.tap(find.text('Save quiet hours'));
    await tester.pumpAndSettle();
    expect(find.text('Alert settings could not be updated.'), findsOneWidget);
  });

  testWidgets(
      'community report validates, submits, publishes, and handles errors',
      (WidgetTester tester) async {
    final FakeCommunityReportApi api = FakeCommunityReportApi();
    await _pumpPage(
      tester,
      CommunityReportPage(
        apiBaseUrl: 'https://api.test',
        latitude: 25.7,
        longitude: -80.2,
        api: api,
        imagePicker: FakeImagePicker(),
      ),
    );

    await tester.enterText(find.byType(TextField), 'short');
    await tester.tap(find.text('Submit report'));
    await tester.pump();
    expect(
      find.text('Add at least 12 characters of useful detail.'),
      findsOneWidget,
    );

    await tester.enterText(
      find.byType(TextField),
      'Tow truck activity observed at this curb.',
    );
    await tester.tap(find.text('Submit report'));
    await tester.pumpAndSettle();
    expect(find.text('Report received and queued for review.'), findsOneWidget);

    api.status = 'published';
    await tester.enterText(
      find.byType(TextField),
      'A verified restriction was posted today.',
    );
    await tester.tap(find.text('Submit report'));
    await tester.pumpAndSettle();
    expect(find.text('Report verified and published.'), findsOneWidget);

    api.fail = true;
    await tester.enterText(
      find.byType(TextField),
      'This valid report now exercises the error path.',
    );
    await tester.tap(find.text('Submit report'));
    await tester.pumpAndSettle();
    expect(find.text('The report could not be submitted.'), findsOneWidget);
  });

  testWidgets('parking assistant renders evidence and a safe degraded state',
      (WidgetTester tester) async {
    final FakeParkingAssistantApi api = FakeParkingAssistantApi();
    await _pumpPage(
      tester,
      ParkingAssistantPage(
        apiBaseUrl: 'https://api.test',
        latitude: 25.7,
        longitude: -80.2,
        api: api,
      ),
    );

    await tester.tap(find.byType(Switch));
    await tester.tap(find.text('Analyze parking'));
    await tester.pumpAndSettle();
    expect(find.text('Score 20'), findsOneWidget);
    expect(find.text('Do not park here.'), findsOneWidget);
    expect(find.textContaining('Low confidence:'), findsOneWidget);

    api.fail = true;
    await tester.tap(find.text('Analyze parking'));
    await tester.pumpAndSettle();
    expect(
        find.text('The assistant is temporarily unavailable.'), findsOneWidget);
  });

  testWidgets('recommendations validate filters and render ranked alternatives',
      (WidgetTester tester) async {
    final FakeParkingRecommendationsApi api = FakeParkingRecommendationsApi();
    await _pumpPage(
      tester,
      ParkingRecommendationsPage(
        apiBaseUrl: 'https://api.test',
        latitude: 25.7,
        longitude: -80.2,
        api: api,
      ),
    );

    await tester.enterText(find.byType(TextField), '-1');
    await tester.tap(find.text('Find safer parking'));
    await tester.pump();
    expect(find.text('Enter a valid maximum hourly price.'), findsOneWidget);

    await tester.enterText(find.byType(TextField), '25');
    await tester.tap(find.text('Find safer parking'));
    await tester.pumpAndSettle();
    expect(find.text('Safe Garage'), findsOneWidget);
    expect(find.text('Match 87'), findsOneWidget);
    expect(find.text(r'$12.00/hour'), findsOneWidget);

    api.empty = true;
    await tester.tap(find.text('Find safer parking'));
    await tester.pumpAndSettle();
    expect(
        find.text('No verified options match these filters.'), findsOneWidget);

    api.fail = true;
    await tester.tap(find.text('Find safer parking'));
    await tester.pumpAndSettle();
    expect(
      find.text('Parking recommendations are temporarily unavailable.'),
      findsOneWidget,
    );
  });

  testWidgets('tow recovery validates inputs and renders verified custody data',
      (WidgetTester tester) async {
    final FakeTowRecoveryApi api = FakeTowRecoveryApi();
    await _pumpPage(
      tester,
      TowRecoveryPage(apiBaseUrl: 'https://api.test', api: api),
    );

    await tester.tap(find.text('Search tow records'));
    await tester.pump();
    expect(find.text('Enter a 2-letter state code'), findsOneWidget);
    expect(find.text('Enter the license plate'), findsOneWidget);

    final Finder fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'FL');
    await tester.enterText(fields.at(1), 'ABC123');
    await tester.enterText(fields.at(2), '123456');
    await tester.tap(find.text('Search tow records'));
    await tester.pumpAndSettle();
    expect(find.text('Verified record found'), findsOneWidget);
    expect(find.text('City Tow'), findsOneWidget);
    expect(find.text(r'Estimated fees: $245.00'), findsOneWidget);

    api.found = false;
    await tester.tap(find.text('Search tow records'));
    await tester.pumpAndSettle();
    expect(find.text('No verified record'), findsOneWidget);

    api.fail = true;
    await tester.tap(find.text('Search tow records'));
    await tester.pumpAndSettle();
    expect(find.text('Tow lookup is temporarily unavailable.'), findsOneWidget);
  });

  testWidgets('sign scanner restores, captures, renders, and degrades safely',
      (WidgetTester tester) async {
    final FakeSignScannerApi api = FakeSignScannerApi();
    final FakeImagePicker picker = FakeImagePicker(
      lostImage: XFile.fromData(
        Uint8List.fromList(<int>[1, 2, 3]),
        name: 'recovered.png',
      ),
      pickedImage: XFile.fromData(
        Uint8List.fromList(<int>[4, 5, 6]),
        name: 'captured.webp',
      ),
    );
    await _pumpPage(
      tester,
      SignScannerPage(
        apiBaseUrl: 'https://api.test',
        api: api,
        imagePicker: picker,
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Towing risk 95/100'), findsOneWidget);
    expect(find.text('Parking is prohibited.'), findsOneWidget);
    expect(find.textContaining('Low confidence:'), findsOneWidget);

    await tester.tap(find.text('Camera'));
    await tester.pumpAndSettle();
    expect(picker.pickCalls, 1);

    api.fail = true;
    await tester.tap(find.text('Gallery'));
    await tester.pumpAndSettle();
    expect(
      find.text('The sign could not be analyzed. Try a clearer photo.'),
      findsOneWidget,
    );
  });

  testWidgets('map renders risk layers, decisions, filters, and failures',
      (WidgetTester tester) async {
    final FakeParkingMapApi api = FakeParkingMapApi(zone: towingZone);
    await _pumpPage(
      tester,
      ParkingMapPage(
        apiBaseUrl: 'https://api.test',
        tileUrl: 'https://tiles.test/{z}/{x}/{y}.png',
        api: api,
        tileProvider: TransparentTileProvider(),
      ),
    );
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('Safe'), findsOneWidget);
    expect(find.text('Tow hotspots'), findsOneWidget);
    await tester.tap(find.text('Tow hotspots'));
    await tester.pump();

    await tester.tap(find.text('Can I park here?'));
    await _pumpFrames(tester);
    expect(find.text('Tow zone'), findsOneWidget);
    expect(find.text('Known towing hotspot'), findsOneWidget);
    await tester.tapAt(const Offset(20, 20));
    await _pumpFrames(tester);

    api.zone = null;
    await tester.tap(find.text('Can I park here?'));
    await _pumpFrames(tester);
    expect(find.textContaining('No verified data covers'), findsOneWidget);
    await tester.tapAt(const Offset(20, 20));
    await _pumpFrames(tester);

    api.fail = true;
    await tester.tap(find.text('Can I park here?'));
    await _pumpFrames(tester);
    expect(find.textContaining('Unable to evaluate this location'),
        findsOneWidget);
  });
}

Future<void> _pumpPage(WidgetTester tester, Widget page) async {
  await tester.binding.setSurfaceSize(const Size(1200, 1600));
  addTearDown(() => tester.binding.setSurfaceSize(null));
  await tester.pumpWidget(
    MaterialApp(
      localizationsDelegates: AppLocalizations.localizationsDelegates,
      supportedLocales: AppLocalizations.supportedLocales,
      theme: ThemeData(splashFactory: InkRipple.splashFactory),
      home: Scaffold(body: page),
    ),
  );
  await tester.pump();
}

Future<void> _pumpFrames(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 350));
}

class FakeParkingAlertCoordinator extends ParkingAlertCoordinator {
  FakeParkingAlertCoordinator(AlertsApi api)
      : super(api, LocalAlertNotifier(), stopDetector: null);

  int startCalls = 0;
  int stopCalls = 0;
  bool startResult = true;

  @override
  Future<bool> start() async {
    startCalls += 1;
    return startResult;
  }

  @override
  Future<void> stop() async {
    stopCalls += 1;
  }
}

class FakeImagePicker extends ImagePicker {
  FakeImagePicker({this.lostImage, this.pickedImage});

  final XFile? lostImage;
  final XFile? pickedImage;
  int pickCalls = 0;

  @override
  Future<XFile?> pickImage({
    required ImageSource source,
    double? maxWidth,
    double? maxHeight,
    int? imageQuality,
    CameraDevice preferredCameraDevice = CameraDevice.rear,
    bool requestFullMetadata = true,
  }) async {
    pickCalls += 1;
    return pickedImage;
  }

  @override
  Future<LostDataResponse> retrieveLostData() async => lostImage == null
      ? LostDataResponse.empty()
      : LostDataResponse(
          files: <XFile>[lostImage!],
          type: RetrieveType.image,
        );
}

class TransparentTileProvider extends TileProvider {
  static final Uint8List _transparentPng = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  );

  @override
  ImageProvider<Object> getImage(
    TileCoordinates coordinates,
    TileLayer options,
  ) =>
      MemoryImage(_transparentPng);
}
