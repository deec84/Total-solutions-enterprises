// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'ParkShield AI';

  @override
  String appSectionTitle(Object section) {
    return 'ParkShield AI · $section';
  }

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get cancel => 'Cancel';

  @override
  String get confirm => 'Confirm';

  @override
  String get navigate => 'Navigate';

  @override
  String sourceWithValue(Object source) {
    return 'Source: $source';
  }

  @override
  String confidencePercent(Object percent) {
    return 'Confidence: $percent%';
  }

  @override
  String get provenanceOfficialData => 'Official Data';

  @override
  String get provenanceAiPrediction => 'AI Prediction';

  @override
  String get provenanceCommunityVerified => 'Community Verified';

  @override
  String get provenanceEstimated => 'Estimated';

  @override
  String get riskVerySafe => 'Very Safe';

  @override
  String get riskVeryHigh => 'Very High Risk';

  @override
  String get parkWithConfidence => 'Park with confidence';

  @override
  String get enterValidEmail => 'Enter a valid email.';

  @override
  String get passwordMinimum => 'Password must contain at least 12 characters.';

  @override
  String get signIn => 'Sign in';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get createAccount => 'Create account';

  @override
  String get verifyEmail => 'Verify email';

  @override
  String get authSignInError => 'Unable to sign in. Check your credentials.';

  @override
  String get authRequestError =>
      'The request could not be completed. Please try again.';

  @override
  String get checkEmailVerification =>
      'Check your email to verify your account.';

  @override
  String get recoverPassword => 'Recover password';

  @override
  String get recoveryInstructions =>
      'Enter your email. If an account exists, we will send recovery instructions.';

  @override
  String get sendInstructions => 'Send instructions';

  @override
  String get haveRecoveryToken => 'I have a recovery token';

  @override
  String get recoverySent => 'If the account exists, instructions were sent.';

  @override
  String get setNewPassword => 'Set new password';

  @override
  String get recoveryToken => 'Recovery token';

  @override
  String get enterRecoveryToken => 'Enter the recovery token.';

  @override
  String get newPassword => 'New password';

  @override
  String get updatePassword => 'Update password';

  @override
  String get passwordUpdated =>
      'Password updated. Sign in with your new password.';

  @override
  String get verificationHelp =>
      'Open your verification link, or paste its token below.';

  @override
  String get verificationToken => 'Verification token';

  @override
  String get verifyAccount => 'Verify account';

  @override
  String get emailVerified => 'Email verified. You can now sign in.';

  @override
  String get navMap => 'Map';

  @override
  String get navAssistant => 'Assistant';

  @override
  String get navSaferParking => 'Safer parking nearby';

  @override
  String get navScanSign => 'Scan a sign';

  @override
  String get navCommunityReport => 'Community report';

  @override
  String get navAlerts => 'Alerts';

  @override
  String get navTowRecovery => 'Tow recovery';

  @override
  String get navPrivacy => 'Privacy and data';

  @override
  String get navMembership => 'Membership';

  @override
  String get navAdministration => 'Administration';

  @override
  String get signOut => 'Sign out';

  @override
  String get membershipTitle => 'Membership';

  @override
  String get membershipVerificationNotice =>
      'Store purchases are credited only after server verification. ParkShield never accepts a client-declared purchase result or displays an invented price.';

  @override
  String get membershipPremium => 'ParkShield Premium';

  @override
  String get membershipFree => 'ParkShield Free';

  @override
  String get purchasesDisabled =>
      'Purchases are not available in this build. No charge can be initiated.';

  @override
  String get storeBridgeDisabled =>
      'The server catalog is prepared, but this build is not connected to App Store or Google Play billing. No charge can be initiated.';

  @override
  String get storePresentsTerms =>
      'Your device store presents the localized price and terms before confirmation.';

  @override
  String continueInStore(Object store) {
    return 'Continue in $store';
  }

  @override
  String get restorePurchases => 'Restore store purchases';

  @override
  String get refreshMembership => 'Refresh membership status';

  @override
  String get subscriptionDeletionNotice =>
      'Deleting a ParkShield account does not cancel a subscription managed by Apple or Google. Cancel it in the same store account used to subscribe.';

  @override
  String get statusUnavailable => 'Status unavailable';

  @override
  String get noStoreSubscription => 'No store subscription';

  @override
  String membershipStatus(Object status, Object store) {
    return '$store · $status';
  }

  @override
  String membershipStatusThrough(Object date, Object status, Object store) {
    return '$store · $status · through $date';
  }

  @override
  String get membershipStatusFree => 'free';

  @override
  String get membershipStatusActive => 'active';

  @override
  String get membershipStatusGracePeriod => 'grace period';

  @override
  String get membershipStatusPaused => 'paused';

  @override
  String get membershipStatusExpired => 'expired';

  @override
  String get membershipStatusRevoked => 'revoked';

  @override
  String get membershipLoadError => 'Membership status could not be loaded.';

  @override
  String get purchaseNotCompleted => 'The store purchase was not completed.';

  @override
  String get membershipVerified => 'Membership verified by the store.';

  @override
  String get purchaseVerificationError =>
      'The store purchase could not be verified. No access was granted.';

  @override
  String get noPurchaseToRestore =>
      'No store purchase was available to restore.';

  @override
  String get purchasesRestored => 'Store purchases were restored and verified.';

  @override
  String get restorePurchasesError => 'Store purchases could not be restored.';

  @override
  String get privacyTitle => 'Privacy and your data';

  @override
  String get privacyIntro =>
      'Optional uses are off until you enable them. Essential security and parking requests are processed to provide the service.';

  @override
  String get consentProductAnalytics => 'Product analytics';

  @override
  String get consentPersonalizedRecommendations =>
      'Personalized recommendations';

  @override
  String get consentCommunityResearch => 'Community research';

  @override
  String get consentProductAnalyticsDescription =>
      'Share de-identified product usage to improve reliability.';

  @override
  String get consentPersonalizedRecommendationsDescription =>
      'Use your prior choices to rank safer parking alternatives.';

  @override
  String get consentCommunityResearchDescription =>
      'Include de-identified reports in parking-safety research.';

  @override
  String get exportDataTitle => 'Export your data';

  @override
  String get exportDataDescription =>
      'Creates a current JSON copy without passwords, MFA secrets, push tokens, or storage keys.';

  @override
  String get createDataExport => 'Create data export';

  @override
  String get copyExportJson => 'Copy export JSON';

  @override
  String get generatedDataExport => 'Generated account data export';

  @override
  String get deleteAccountTitle => 'Delete account';

  @override
  String get deleteAccountDescription =>
      'This permanently removes the account, sessions, preferences, reports, appeals, and retained community evidence. It does not cancel an Apple or Google subscription; cancel that in the store. Pseudonymous billing evidence may be retained for reconciliation and legal obligations. This cannot be undone.';

  @override
  String get currentPassword => 'Current password';

  @override
  String get mfaCodeOptional => 'MFA code (if enabled)';

  @override
  String get permanentlyDeleteAccount => 'Permanently delete account';

  @override
  String get privacyLoadError => 'Privacy choices could not be loaded.';

  @override
  String preferenceSaved(Object purpose) {
    return '$purpose preference saved.';
  }

  @override
  String get privacySaveError => 'The privacy choice could not be saved.';

  @override
  String get dataExportReady => 'Your data export is ready.';

  @override
  String get dataExportError => 'Your data export could not be created.';

  @override
  String get dataExportCopied => 'Data export copied.';

  @override
  String get enterCurrentPassword => 'Enter your current password first.';

  @override
  String get deleteAccountQuestion => 'Delete your ParkShield account?';

  @override
  String get deleteAccountConfirmation =>
      'Your account and owned data will be permanently deleted.';

  @override
  String get deletePermanently => 'Delete permanently';

  @override
  String get deleteAccountError =>
      'The account was not deleted. Verify your password, MFA code, and connection.';

  @override
  String get alertsTitle => 'Preventive alerts';

  @override
  String get alertsIntro =>
      'When enabled, ParkShield may access location in the background to warn you after significant movement. Location checks are sent only for parking-risk evaluation.';

  @override
  String get automaticAlerts => 'Automatic parking-risk alerts';

  @override
  String get automaticAlertsPermission =>
      'Requires Always Allow location permission. You can revoke it anytime.';

  @override
  String get quietHours => 'Quiet hours';

  @override
  String get start => 'Start';

  @override
  String get end => 'End';

  @override
  String get timeZone => 'Time zone';

  @override
  String get eastern => 'Eastern';

  @override
  String get central => 'Central';

  @override
  String get mountain => 'Mountain';

  @override
  String get pacific => 'Pacific';

  @override
  String get alaska => 'Alaska';

  @override
  String get hawaii => 'Hawaii';

  @override
  String get saveQuietHours => 'Save quiet hours';

  @override
  String get alertsPermissionResume =>
      'Enable Always Allow location permission to resume automatic alerts.';

  @override
  String get alertsLoadError => 'Alert preferences could not be loaded.';

  @override
  String get alertsPermissionRequired =>
      'Alerts remain off. Grant Always Allow location permission, then try again.';

  @override
  String get alertsActive => 'Preventive parking alerts are active.';

  @override
  String get alertsOff => 'Preventive parking alerts are off.';

  @override
  String get alertsUpdateError => 'Alert settings could not be updated.';

  @override
  String notificationRisk(Object score) {
    return 'Parking risk $score/100';
  }

  @override
  String get notificationChannel => 'Parking risk alerts';

  @override
  String get notificationChannelDescription =>
      'Preventive warnings when a parking location is risky.';

  @override
  String get adminTitle => 'Administration';

  @override
  String get adminMfaNotice =>
      'Privileged actions require a fresh authenticator code.';

  @override
  String get mfaCodeSixDigit => '6-digit MFA code';

  @override
  String get enrollMfa => 'Enroll MFA';

  @override
  String get openDashboard => 'Open dashboard';

  @override
  String get mfaSetupHelp =>
      'Add this secret to your authenticator, then enter its code:';

  @override
  String get confirmMfa => 'Confirm MFA';

  @override
  String get metricUsers => 'Users';

  @override
  String get metricSessions => 'Sessions';

  @override
  String get metricPending => 'Pending';

  @override
  String get metricPublished => 'Published';

  @override
  String get metricRejected => 'Rejected';

  @override
  String get auditVerified => 'Audit chain verified';

  @override
  String get auditFailure => 'Audit integrity failure';

  @override
  String recordsChecked(Object count) {
    return '$count records checked';
  }

  @override
  String get moderationQueue => 'Moderation queue';

  @override
  String evidencePercent(Object description, Object percent) {
    return '$description\nEvidence $percent%';
  }

  @override
  String get approve => 'Approve';

  @override
  String get reject => 'Reject';

  @override
  String get mfaEnabled => 'MFA enabled.';

  @override
  String get adminRequestError =>
      'Administrative request failed. Verify role and MFA.';

  @override
  String get approveReport => 'Approve report';

  @override
  String get rejectReport => 'Reject report';

  @override
  String get reason => 'Reason';

  @override
  String metricValue(Object label, Object value) {
    return '$label: $value';
  }

  @override
  String get communityTitle => 'Community report';

  @override
  String get communityIntro =>
      'Reports are AI-screened and may require moderator review.';

  @override
  String get reportType => 'Report type';

  @override
  String get newRestriction => 'New restriction';

  @override
  String get towingActivity => 'Towing activity';

  @override
  String get updatedPrice => 'Updated price';

  @override
  String get parkingSign => 'Parking sign';

  @override
  String get whatObserved => 'What did you observe?';

  @override
  String get observationHint =>
      'Include the restriction, time, price, or towing details.';

  @override
  String get addPhoto => 'Add supporting photo';

  @override
  String get photoAttached => 'Photo attached';

  @override
  String get submitReport => 'Submit report';

  @override
  String get reportMinimumDetail =>
      'Add at least 12 characters of useful detail.';

  @override
  String get reportPublished => 'Report verified and published.';

  @override
  String get reportQueued => 'Report received and queued for review.';

  @override
  String get reportSubmitError => 'The report could not be submitted.';

  @override
  String get canIParkHere => 'Can I park here?';

  @override
  String get mapEvaluationError =>
      'Unable to evaluate this location. Read all posted signs.';

  @override
  String get mapUnavailable =>
      'Parking intelligence is temporarily unavailable.';

  @override
  String get riskSafe => 'Safe';

  @override
  String get riskReadSigns => 'Read signs';

  @override
  String get riskHigh => 'High risk';

  @override
  String get riskDoNotPark => 'Do not park';

  @override
  String get zoneGeneral => 'General';

  @override
  String get zoneResidents => 'Residents';

  @override
  String get zonePrivate => 'Private';

  @override
  String get zoneCommercial => 'Commercial';

  @override
  String get zoneTowHotspots => 'Tow hotspots';

  @override
  String get noVerifiedLocationData =>
      'No verified data covers this location. Read every posted sign before parking.';

  @override
  String get noRestrictionSummary => 'No restriction summary is available.';

  @override
  String estimatedTowingCost(Object cost) {
    return 'Estimated towing cost: $cost';
  }

  @override
  String get knownTowingHotspot => 'Known towing hotspot';

  @override
  String get assistantTitle => 'Parking Assistant';

  @override
  String get assistantIntro =>
      'Ask about the current map location. Verified rules always outrank AI.';

  @override
  String get yourQuestion => 'Your question';

  @override
  String get residentPermit => 'I have a valid resident permit';

  @override
  String get analyzeParking => 'Analyze parking';

  @override
  String get assistantUnavailable =>
      'The assistant is temporarily unavailable.';

  @override
  String scoreValue(Object score) {
    return 'Score $score';
  }

  @override
  String understoodAs(Object intent) {
    return 'Understood as: $intent';
  }

  @override
  String get lowConfidenceReview =>
      'Low confidence: review current signs or request human verification.';

  @override
  String get recommendationsTitle => 'Safer parking nearby';

  @override
  String get recommendationsIntro =>
      'Options balance walking distance, price, safety, towing history, ratings, and current availability.';

  @override
  String get maximumWalkingDistance => 'Maximum walking distance';

  @override
  String get meters500 => '500 meters';

  @override
  String get kilometer1 => '1 kilometer';

  @override
  String get kilometers15 => '1.5 kilometers';

  @override
  String get kilometers3 => '3 kilometers';

  @override
  String get maximumHourlyPrice => 'Maximum hourly price (optional)';

  @override
  String get findSaferParking => 'Find safer parking';

  @override
  String get noVerifiedOptions => 'No verified options match these filters.';

  @override
  String get invalidHourlyPrice => 'Enter a valid maximum hourly price.';

  @override
  String get recommendationsUnavailable =>
      'Parking recommendations are temporarily unavailable.';

  @override
  String matchScore(Object score) {
    return 'Match $score';
  }

  @override
  String walkSafety(Object meters, Object score) {
    return '$meters m walk · Safety $score/100';
  }

  @override
  String get priceNotVerified => 'Price not verified';

  @override
  String pricePerHour(Object price) {
    return '$price/hour';
  }

  @override
  String spacesAvailable(Object count) {
    return '$count spaces reported available';
  }

  @override
  String sourceConfidence(Object percent, Object source) {
    return 'Source: $source · $percent% confidence';
  }

  @override
  String get recoveryTitle => 'Find a towed vehicle';

  @override
  String get recoveryIntro =>
      'Search verified municipal and towing-provider records. Never pay from an unverified message or phone call.';

  @override
  String get vehicleState => 'Vehicle state';

  @override
  String get stateHint => 'FL';

  @override
  String get stateValidation => 'Enter a 2-letter state code';

  @override
  String get licensePlate => 'License plate';

  @override
  String get plateValidation => 'Enter the license plate';

  @override
  String get vinLastSix => 'Last 6 VIN characters (optional)';

  @override
  String get vinValidation => 'Enter exactly 6 characters';

  @override
  String get searchTowRecords => 'Search tow records';

  @override
  String get towLookupUnavailable => 'Tow lookup is temporarily unavailable.';

  @override
  String get verifiedRecordFound => 'Verified record found';

  @override
  String get noVerifiedRecord => 'No verified record';

  @override
  String bringDocuments(Object documents) {
    return 'Bring: $documents';
  }

  @override
  String paymentMethods(Object methods) {
    return 'Payment: $methods';
  }

  @override
  String get feesConfirmDirectly => 'Fees: confirm directly';

  @override
  String estimatedFees(Object fees) {
    return 'Estimated fees: $fees';
  }

  @override
  String get call => 'Call';

  @override
  String get scannerTitle => 'Parking Sign Scanner';

  @override
  String get scannerIntro =>
      'The selected image is analyzed in memory and is not retained by default.';

  @override
  String get camera => 'Camera';

  @override
  String get gallery => 'Gallery';

  @override
  String get scanPhotoError =>
      'The sign could not be analyzed. Try a clearer photo.';

  @override
  String get recoveredPhotoError =>
      'The recovered photo could not be analyzed.';

  @override
  String towingRisk(Object score) {
    return 'Towing risk $score/100';
  }

  @override
  String detectedText(Object text) {
    return 'Detected text: $text';
  }

  @override
  String get scanLowConfidence =>
      'Low confidence: read the physical sign or request human review.';
}
