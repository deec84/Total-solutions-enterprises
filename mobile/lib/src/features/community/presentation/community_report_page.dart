import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:parkshield_mobile/src/core/localization/localization.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/community/data/community_report_api.dart';
import 'package:parkshield_mobile/src/features/community/domain/community_report.dart';

class CommunityReportPage extends StatefulWidget {
  const CommunityReportPage({
    required this.apiBaseUrl,
    required this.latitude,
    required this.longitude,
    this.api,
    this.imagePicker,
    super.key,
  });

  final String apiBaseUrl;
  final double latitude;
  final double longitude;
  final CommunityReportApi? api;
  final ImagePicker? imagePicker;

  @override
  State<CommunityReportPage> createState() => _CommunityReportPageState();
}

class _CommunityReportPageState extends State<CommunityReportPage> {
  final TextEditingController _description = TextEditingController();
  late final ImagePicker _picker;
  late final CommunityReportApi _api;
  String _category = 'restriction';
  XFile? _photo;
  bool _loading = false;
  String? _message;

  @override
  void initState() {
    super.initState();
    _picker = widget.imagePicker ?? ImagePicker();
    _api = widget.api ??
        CommunityReportApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
  }

  @override
  void dispose() {
    _api.close();
    _description.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text(context.l10n.communityTitle,
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(context.l10n.communityIntro),
          const SizedBox(height: 20),
          DropdownButtonFormField<String>(
            initialValue: _category,
            decoration: InputDecoration(labelText: context.l10n.reportType),
            items: <DropdownMenuItem<String>>[
              DropdownMenuItem(
                  value: 'restriction',
                  child: Text(context.l10n.newRestriction)),
              DropdownMenuItem(
                  value: 'towing', child: Text(context.l10n.towingActivity)),
              DropdownMenuItem(
                  value: 'price', child: Text(context.l10n.updatedPrice)),
              DropdownMenuItem(
                  value: 'sign', child: Text(context.l10n.parkingSign)),
            ],
            onChanged: _loading
                ? null
                : (String? value) => setState(() => _category = value!),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _description,
            enabled: !_loading,
            minLines: 3,
            maxLines: 6,
            maxLength: 1000,
            decoration: InputDecoration(
              labelText: context.l10n.whatObserved,
              hintText: context.l10n.observationHint,
            ),
          ),
          OutlinedButton.icon(
            onPressed: _loading ? null : _choosePhoto,
            icon: const Icon(Icons.add_a_photo_outlined),
            label: Text(_photo == null
                ? context.l10n.addPhoto
                : context.l10n.photoAttached),
          ),
          const SizedBox(height: 12),
          FilledButton(
            onPressed: _loading ? null : _submit,
            child: _loading
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : Text(context.l10n.submitReport),
          ),
          if (_message case final String message)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(message),
            ),
        ],
      );

  Future<void> _choosePhoto() async {
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 2048,
      maxHeight: 2048,
      imageQuality: 88,
      requestFullMetadata: false,
    );
    if (photo != null && mounted) {
      setState(() => _photo = photo);
    }
  }

  Future<void> _submit() async {
    if (_description.text.trim().length < 12) {
      setState(() => _message = context.l10n.reportMinimumDetail);
      return;
    }
    setState(() {
      _loading = true;
      _message = null;
    });
    try {
      final CommunityReport report = await _api.submit(
        category: _category,
        latitude: widget.latitude,
        longitude: widget.longitude,
        description: _description.text.trim(),
        photo: _photo,
      );
      if (mounted) {
        setState(() {
          _message = report.status == 'published'
              ? context.l10n.reportPublished
              : context.l10n.reportQueued;
          _description.clear();
          _photo = null;
        });
      }
    } on Exception {
      if (mounted) {
        setState(() => _message = context.l10n.reportSubmitError);
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }
}
