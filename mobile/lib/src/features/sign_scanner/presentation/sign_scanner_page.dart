import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/data/sign_scanner_api.dart';
import 'package:parkshield_mobile/src/features/sign_scanner/domain/sign_scan_result.dart';

class SignScannerPage extends StatefulWidget {
  const SignScannerPage({
    required this.apiBaseUrl,
    this.api,
    this.imagePicker,
    super.key,
  });

  final String apiBaseUrl;
  final SignScannerApi? api;
  final ImagePicker? imagePicker;

  @override
  State<SignScannerPage> createState() => _SignScannerPageState();
}

class _SignScannerPageState extends State<SignScannerPage> {
  late final ImagePicker _picker;
  late final SignScannerApi _api;
  SignScanResult? _result;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _picker = widget.imagePicker ?? ImagePicker();
    _api = widget.api ??
        SignScannerApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
    _recoverLostImage();
  }

  @override
  void dispose() {
    _api.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Parking Sign Scanner',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
              'The selected image is analyzed in memory and is not retained by default.'),
          const SizedBox(height: 20),
          Row(
            children: <Widget>[
              Expanded(
                child: FilledButton.icon(
                  onPressed: _loading ? null : () => _pick(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: const Text('Camera'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: _loading ? null : () => _pick(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Gallery'),
                ),
              ),
            ],
          ),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(child: CircularProgressIndicator()),
            ),
          if (_error case final String message)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Text(message,
                  style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
          if (_result case final SignScanResult result)
            _ScanResultCard(result: result),
        ],
      );

  Future<void> _pick(ImageSource source) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        maxWidth: 2048,
        maxHeight: 2048,
        imageQuality: 88,
        requestFullMetadata: false,
      );
      if (file == null) return;
      await _scan(file);
    } on Exception {
      if (mounted) {
        setState(() =>
            _error = 'The sign could not be analyzed. Try a clearer photo.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _recoverLostImage() async {
    final LostDataResponse response = await _picker.retrieveLostData();
    if (response.isEmpty || response.files == null || response.files!.isEmpty) {
      return;
    }
    if (mounted) setState(() => _loading = true);
    try {
      await _scan(response.files!.first);
    } on Exception {
      if (mounted) {
        setState(() => _error = 'The recovered photo could not be analyzed.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _scan(XFile file) async {
    final SignScanResult result = await _api.scan(
      bytes: await file.readAsBytes(),
      filename: file.name,
      contentType: file.mimeType ?? _contentType(file.name),
    );
    if (mounted) setState(() => _result = result);
  }

  String _contentType(String name) {
    final String lower = name.toLowerCase();
    if (lower.endsWith('.png')) return 'image/png';
    if (lower.endsWith('.webp')) return 'image/webp';
    return 'image/jpeg';
  }
}

class _ScanResultCard extends StatelessWidget {
  const _ScanResultCard({required this.result});

  final SignScanResult result;

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(top: 20),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'Towing risk ${result.towingRiskScore}/100',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              Text(result.summary),
              if (result.restrictions.isNotEmpty) ...<Widget>[
                const Divider(height: 28),
                ...result.restrictions.map((String item) => Text('• $item')),
              ],
              const Divider(height: 28),
              Text('Detected text: ${result.detectedText}'),
              Text('Confidence: ${(result.confidence * 100).round()}%'),
              if (result.requiresHumanReview)
                const Text(
                  'Low confidence: read the physical sign or request human review.',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              const SizedBox(height: 12),
              Text(result.disclaimer,
                  style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
      );
}
