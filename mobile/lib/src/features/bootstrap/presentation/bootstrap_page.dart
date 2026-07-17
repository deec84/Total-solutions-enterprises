import 'package:flutter/material.dart';
import 'package:latlong2/latlong.dart';
import 'package:parkshield_mobile/src/features/admin/presentation/admin_page.dart';
import 'package:parkshield_mobile/src/features/alerts/presentation/alerts_page.dart';
import 'package:parkshield_mobile/src/features/community/presentation/community_report_page.dart';
import 'package:parkshield_mobile/src/features/map/presentation/parking_map_page.dart';
import 'package:parkshield_mobile/src/features/parking_ai/presentation/parking_assistant_page.dart';
import 'package:parkshield_mobile/src/features/recommendations/presentation/parking_recommendations_page.dart';
import 'package:parkshield_mobile/src/features/recovery/presentation/tow_recovery_page.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/presentation/sign_scanner_page.dart';

class BootstrapPage extends StatefulWidget {
  const BootstrapPage({
    required this.apiBaseUrl,
    required this.mapTileUrl,
    required this.userRole,
    this.onLogout,
    super.key,
  });

  final String apiBaseUrl;
  final String mapTileUrl;
  final String userRole;
  final Future<void> Function()? onLogout;

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
      if (isPrivileged) AdminPage(apiBaseUrl: widget.apiBaseUrl),
    ];
    final List<String> titles = <String>[
      'Map',
      'Assistant',
      'Safer parking',
      'Scan a sign',
      'Community report',
      'Alerts',
      'Tow recovery',
      if (isPrivileged) 'Administration',
    ];
    final List<NavigationDrawerDestination> destinations =
        <NavigationDrawerDestination>[
      const NavigationDrawerDestination(
        icon: Icon(Icons.map_outlined),
        selectedIcon: Icon(Icons.map),
        label: Text('Map'),
      ),
      const NavigationDrawerDestination(
        icon: Icon(Icons.auto_awesome_outlined),
        selectedIcon: Icon(Icons.auto_awesome),
        label: Text('Assistant'),
      ),
      const NavigationDrawerDestination(
        icon: Icon(Icons.local_parking_outlined),
        selectedIcon: Icon(Icons.local_parking),
        label: Text('Safer parking nearby'),
      ),
      const NavigationDrawerDestination(
        icon: Icon(Icons.document_scanner_outlined),
        selectedIcon: Icon(Icons.document_scanner),
        label: Text('Scan a sign'),
      ),
      const NavigationDrawerDestination(
        icon: Icon(Icons.campaign_outlined),
        selectedIcon: Icon(Icons.campaign),
        label: Text('Community report'),
      ),
      const NavigationDrawerDestination(
        icon: Icon(Icons.notifications_active_outlined),
        selectedIcon: Icon(Icons.notifications_active),
        label: Text('Alerts'),
      ),
      const NavigationDrawerDestination(
        icon: Icon(Icons.car_crash_outlined),
        selectedIcon: Icon(Icons.car_crash),
        label: Text('Tow recovery'),
      ),
      if (isPrivileged)
        const NavigationDrawerDestination(
          icon: Icon(Icons.admin_panel_settings_outlined),
          selectedIcon: Icon(Icons.admin_panel_settings),
          label: Text('Administration'),
        ),
    ];
    return Scaffold(
      appBar: AppBar(
        title: Text('ParkShield AI · ${titles[_index]}'),
        actions: <Widget>[
          if (widget.onLogout != null)
            IconButton(
              onPressed: widget.onLogout,
              tooltip: 'Sign out',
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
}
