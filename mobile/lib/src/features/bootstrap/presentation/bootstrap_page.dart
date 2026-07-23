import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/core/analytics/product_analytics.dart';
import 'package:parkshield_mobile/src/features/admin/presentation/admin_page.dart';
import 'package:parkshield_mobile/src/features/alerts/presentation/alerts_page.dart';
import 'package:parkshield_mobile/src/features/community/presentation/community_report_page.dart';
import 'package:parkshield_mobile/src/features/billing/presentation/membership_page.dart';
import 'package:parkshield_mobile/src/features/map/presentation/parking_map_page.dart';
import 'package:parkshield_mobile/src/features/parking_ai/presentation/parking_assistant_page.dart';
import 'package:parkshield_mobile/src/features/recommendations/presentation/parking_recommendations_page.dart';
import 'package:parkshield_mobile/src/features/recovery/presentation/tow_recovery_page.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/presentation/sign_scanner_page.dart';
import 'package:parkshield_mobile/src/features/privacy/presentation/privacy_page.dart';

class BootstrapPage extends StatefulWidget {
  const BootstrapPage({
    required this.apiBaseUrl,
    required this.mapTileUrl,
    required this.userRole,
    required this.analytics,
    this.onLogout,
    this.onAccountDeleted,
    super.key,
  });

  final String apiBaseUrl;
  final String mapTileUrl;
  final String userRole;
  final ProductAnalyticsController analytics;
  final Future<void> Function()? onLogout;
  final VoidCallback? onAccountDeleted;

  @override
  State<BootstrapPage> createState() => _BootstrapPageState();
}

class _BootstrapPageState extends State<BootstrapPage> {
  int _index = 0;
  double _latitude = 25.7617;
  double _longitude = -80.1918;

  @override
  Widget build(BuildContext context) {
    final bool isPrivileged =
        widget.userRole == 'admin' || widget.userRole == 'moderator';
    final List<Widget> pages = <Widget>[
      ParkingMapPage(
        apiBaseUrl: widget.apiBaseUrl,
        tileUrl: widget.mapTileUrl,
        onCenterChanged: (LatLng center) {
          _latitude = center.latitude;
          _longitude = center.longitude;
        },
      ),
      ParkingAssistantPage(
        apiBaseUrl: widget.apiBaseUrl,
        latitude: _latitude,
        longitude: _longitude,
      ),
      ParkingRecommendationsPage(
        apiBaseUrl: widget.apiBaseUrl,
        latitude: _latitude,
        longitude: _longitude,
      ),
      SignScannerPage(apiBaseUrl: widget.apiBaseUrl),
      CommunityReportPage(
        apiBaseUrl: widget.apiBaseUrl,
        latitude: _latitude,
        longitude: _longitude,
      ),
      AlertsPage(apiBaseUrl: widget.apiBaseUrl),
      TowRecoveryPage(apiBaseUrl: widget.apiBaseUrl),
      PrivacyPage(
        apiBaseUrl: widget.apiBaseUrl,
        onAccountDeleted: widget.onAccountDeleted,
        onProductAnalyticsConsentChanged: widget.analytics.updateConsent,
      ),
      MembershipPage(apiBaseUrl: widget.apiBaseUrl),
      if (isPrivileged) AdminPage(apiBaseUrl: widget.apiBaseUrl),
    ];
    final List<String> titles = <String>[
      context.l10n.navMap,
      context.l10n.navAssistant,
      context.l10n.navSaferParking,
      context.l10n.navScanSign,
      context.l10n.navCommunityReport,
      context.l10n.navAlerts,
      context.l10n.navTowRecovery,
      context.l10n.navPrivacy,
      context.l10n.navMembership,
      if (isPrivileged) context.l10n.navAdministration,
    ];
    final List<NavigationDrawerDestination> destinations =
        <NavigationDrawerDestination>[
      NavigationDrawerDestination(
        icon: const Icon(Icons.map_outlined),
        selectedIcon: const Icon(Icons.map),
        label: Text(context.l10n.navMap),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.auto_awesome_outlined),
        selectedIcon: const Icon(Icons.auto_awesome),
        label: Text(context.l10n.navAssistant),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.local_parking_outlined),
        selectedIcon: const Icon(Icons.local_parking),
        label: Text(context.l10n.navSaferParking),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.document_scanner_outlined),
        selectedIcon: const Icon(Icons.document_scanner),
        label: Text(context.l10n.navScanSign),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.campaign_outlined),
        selectedIcon: const Icon(Icons.campaign),
        label: Text(context.l10n.navCommunityReport),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.notifications_active_outlined),
        selectedIcon: const Icon(Icons.notifications_active),
        label: Text(context.l10n.navAlerts),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.car_crash_outlined),
        selectedIcon: const Icon(Icons.car_crash),
        label: Text(context.l10n.navTowRecovery),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.privacy_tip_outlined),
        selectedIcon: const Icon(Icons.privacy_tip),
        label: Text(context.l10n.navPrivacy),
      ),
      NavigationDrawerDestination(
        icon: const Icon(Icons.workspace_premium_outlined),
        selectedIcon: const Icon(Icons.workspace_premium),
        label: Text(context.l10n.navMembership),
      ),
      if (isPrivileged)
        NavigationDrawerDestination(
          icon: const Icon(Icons.admin_panel_settings_outlined),
          selectedIcon: const Icon(Icons.admin_panel_settings),
          label: Text(context.l10n.navAdministration),
        ),
    ];
    return Scaffold(
      appBar: AppBar(
        title: Text(context.l10n.appSectionTitle(titles[_index])),
        actions: <Widget>[
          if (widget.onLogout != null)
            IconButton(
              onPressed: widget.onLogout,
              tooltip: context.l10n.signOut,
              icon: const Icon(Icons.logout),
            ),
        ],
      ),
      body: IndexedStack(
        index: _index,
        children: pages,
      ),
      drawer: NavigationDrawer(
        selectedIndex: _index,
        onDestinationSelected: (int value) {
          Navigator.of(context).pop();
          setState(() => _index = value);
          widget.analytics.track(
            ProductEvent.screenViewed,
            <String, Object>{'screen': _analyticsScreen(value, isPrivileged)},
          );
        },
        children: <Widget>[
          const Padding(
            padding: EdgeInsets.fromLTRB(28, 24, 16, 12),
            child: Text('ParkShield AI',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          ),
          ...destinations,
        ],
      ),
    );
  }

  String _analyticsScreen(int index, bool isPrivileged) {
    const List<String> screens = <String>[
      'map',
      'assistant',
      'recommendations',
      'sign_scanner',
      'community_report',
      'alerts',
      'tow_recovery',
      'privacy',
      'membership',
    ];
    if (isPrivileged && index == screens.length) return 'administration';
    return screens[index];
  }
}
