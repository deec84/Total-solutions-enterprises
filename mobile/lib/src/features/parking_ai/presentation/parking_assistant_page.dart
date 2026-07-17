import 'package:flutter/material.dart';
import 'package:parkshield_mobile/src/features/auth/data/secure_token_store.dart';
import 'package:parkshield_mobile/src/features/parking_ai/data/parking_assistant_api.dart';
import 'package:parkshield_mobile/src/features/parking_ai/domain/parking_assessment.dart';

class ParkingAssistantPage extends StatefulWidget {
  const ParkingAssistantPage({
    required this.apiBaseUrl,
    required this.latitude,
    required this.longitude,
    this.api,
    super.key,
  });

  final String apiBaseUrl;
  final double latitude;
  final double longitude;
  final ParkingAssistantApi? api;

  @override
  State<ParkingAssistantPage> createState() => _ParkingAssistantPageState();
}

class _ParkingAssistantPageState extends State<ParkingAssistantPage> {
  final TextEditingController _question =
      TextEditingController(text: 'Can I park here?');
  late final ParkingAssistantApi _api;
  ParkingAssessment? _assessment;
  bool _hasResidentPermit = false;
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _api = widget.api ??
        ParkingAssistantApi(
          baseUrl: widget.apiBaseUrl,
          tokenStore: SecureTokenStore(),
        );
  }

  @override
  void dispose() {
    _api.close();
    _question.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(20),
        children: <Widget>[
          Text('Parking Assistant',
              style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          const Text(
              'Ask about the current map location. Verified rules always outrank AI.'),
          const SizedBox(height: 20),
          TextField(
            controller: _question,
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Your question',
              border: OutlineInputBorder(),
            ),
          ),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            title: const Text('I have a valid resident permit'),
            value: _hasResidentPermit,
            onChanged: (bool value) =>
                setState(() => _hasResidentPermit = value),
          ),
          FilledButton.icon(
            onPressed: _loading ? null : _ask,
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Analyze parking'),
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
          if (_assessment case final ParkingAssessment assessment)
            _AssessmentCard(assessment: assessment),
        ],
      );

  Future<void> _ask() async {
    if (_question.text.trim().length < 2) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final ParkingAssessment assessment = await _api.ask(
        question: _question.text.trim(),
        latitude: widget.latitude,
        longitude: widget.longitude,
        hasResidentPermit: _hasResidentPermit,
      );
      if (mounted) {
        setState(() => _assessment = assessment);
      }
    } on Exception {
      if (mounted) {
        setState(() => _error = 'The assistant is temporarily unavailable.');
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }
}

class _AssessmentCard extends StatelessWidget {
  const _AssessmentCard({required this.assessment});

  final ParkingAssessment assessment;

  @override
  Widget build(BuildContext context) => Card(
        margin: const EdgeInsets.only(top: 20),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text('Score ${assessment.parkingScore}',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(assessment.answer),
              Text('Understood as: '
                  '${assessment.interpretedIntent.replaceAll('_', ' ')}'),
              const Divider(height: 28),
              ...assessment.reasons.map(
                (String reason) => Padding(
                  padding: const EdgeInsets.only(bottom: 6),
                  child: Text('• $reason'),
                ),
              ),
              Text('Source: ${assessment.provenance}'),
              Text('Confidence: ${(assessment.confidence * 100).round()}%'),
              if (assessment.requiresHumanReview)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Text(
                    'Low confidence: review current signs or request human verification.',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              const SizedBox(height: 12),
              Text(assessment.disclaimer,
                  style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
        ),
      );
}
