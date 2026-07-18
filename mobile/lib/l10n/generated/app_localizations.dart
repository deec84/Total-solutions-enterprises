import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'generated/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es')
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'ParkShield AI'**
  String get appTitle;

  /// No description provided for @appSectionTitle.
  ///
  /// In en, this message translates to:
  /// **'ParkShield AI · {section}'**
  String appSectionTitle(Object section);

  /// No description provided for @email.
  ///
  /// In en, this message translates to:
  /// **'Email'**
  String get email;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @confirm.
  ///
  /// In en, this message translates to:
  /// **'Confirm'**
  String get confirm;

  /// No description provided for @navigate.
  ///
  /// In en, this message translates to:
  /// **'Navigate'**
  String get navigate;

  /// No description provided for @sourceWithValue.
  ///
  /// In en, this message translates to:
  /// **'Source: {source}'**
  String sourceWithValue(Object source);

  /// No description provided for @confidencePercent.
  ///
  /// In en, this message translates to:
  /// **'Confidence: {percent}%'**
  String confidencePercent(Object percent);

  /// No description provided for @provenanceOfficialData.
  ///
  /// In en, this message translates to:
  /// **'Official Data'**
  String get provenanceOfficialData;

  /// No description provided for @provenanceAiPrediction.
  ///
  /// In en, this message translates to:
  /// **'AI Prediction'**
  String get provenanceAiPrediction;

  /// No description provided for @provenanceCommunityVerified.
  ///
  /// In en, this message translates to:
  /// **'Community Verified'**
  String get provenanceCommunityVerified;

  /// No description provided for @provenanceEstimated.
  ///
  /// In en, this message translates to:
  /// **'Estimated'**
  String get provenanceEstimated;

  /// No description provided for @riskVerySafe.
  ///
  /// In en, this message translates to:
  /// **'Very Safe'**
  String get riskVerySafe;

  /// No description provided for @riskVeryHigh.
  ///
  /// In en, this message translates to:
  /// **'Very High Risk'**
  String get riskVeryHigh;

  /// No description provided for @parkWithConfidence.
  ///
  /// In en, this message translates to:
  /// **'Park with confidence'**
  String get parkWithConfidence;

  /// No description provided for @enterValidEmail.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid email.'**
  String get enterValidEmail;

  /// No description provided for @passwordMinimum.
  ///
  /// In en, this message translates to:
  /// **'Password must contain at least 12 characters.'**
  String get passwordMinimum;

  /// No description provided for @signIn.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get signIn;

  /// No description provided for @forgotPassword.
  ///
  /// In en, this message translates to:
  /// **'Forgot password?'**
  String get forgotPassword;

  /// No description provided for @createAccount.
  ///
  /// In en, this message translates to:
  /// **'Create account'**
  String get createAccount;

  /// No description provided for @verifyEmail.
  ///
  /// In en, this message translates to:
  /// **'Verify email'**
  String get verifyEmail;

  /// No description provided for @authSignInError.
  ///
  /// In en, this message translates to:
  /// **'Unable to sign in. Check your credentials.'**
  String get authSignInError;

  /// No description provided for @authRequestError.
  ///
  /// In en, this message translates to:
  /// **'The request could not be completed. Please try again.'**
  String get authRequestError;

  /// No description provided for @checkEmailVerification.
  ///
  /// In en, this message translates to:
  /// **'Check your email to verify your account.'**
  String get checkEmailVerification;

  /// No description provided for @recoverPassword.
  ///
  /// In en, this message translates to:
  /// **'Recover password'**
  String get recoverPassword;

  /// No description provided for @recoveryInstructions.
  ///
  /// In en, this message translates to:
  /// **'Enter your email. If an account exists, we will send recovery instructions.'**
  String get recoveryInstructions;

  /// No description provided for @sendInstructions.
  ///
  /// In en, this message translates to:
  /// **'Send instructions'**
  String get sendInstructions;

  /// No description provided for @haveRecoveryToken.
  ///
  /// In en, this message translates to:
  /// **'I have a recovery token'**
  String get haveRecoveryToken;

  /// No description provided for @recoverySent.
  ///
  /// In en, this message translates to:
  /// **'If the account exists, instructions were sent.'**
  String get recoverySent;

  /// No description provided for @setNewPassword.
  ///
  /// In en, this message translates to:
  /// **'Set new password'**
  String get setNewPassword;

  /// No description provided for @recoveryToken.
  ///
  /// In en, this message translates to:
  /// **'Recovery token'**
  String get recoveryToken;

  /// No description provided for @enterRecoveryToken.
  ///
  /// In en, this message translates to:
  /// **'Enter the recovery token.'**
  String get enterRecoveryToken;

  /// No description provided for @newPassword.
  ///
  /// In en, this message translates to:
  /// **'New password'**
  String get newPassword;

  /// No description provided for @updatePassword.
  ///
  /// In en, this message translates to:
  /// **'Update password'**
  String get updatePassword;

  /// No description provided for @passwordUpdated.
  ///
  /// In en, this message translates to:
  /// **'Password updated. Sign in with your new password.'**
  String get passwordUpdated;

  /// No description provided for @verificationHelp.
  ///
  /// In en, this message translates to:
  /// **'Open your verification link, or paste its token below.'**
  String get verificationHelp;

  /// No description provided for @verificationToken.
  ///
  /// In en, this message translates to:
  /// **'Verification token'**
  String get verificationToken;

  /// No description provided for @verifyAccount.
  ///
  /// In en, this message translates to:
  /// **'Verify account'**
  String get verifyAccount;

  /// No description provided for @emailVerified.
  ///
  /// In en, this message translates to:
  /// **'Email verified. You can now sign in.'**
  String get emailVerified;

  /// No description provided for @navMap.
  ///
  /// In en, this message translates to:
  /// **'Map'**
  String get navMap;

  /// No description provided for @navAssistant.
  ///
  /// In en, this message translates to:
  /// **'Assistant'**
  String get navAssistant;

  /// No description provided for @navSaferParking.
  ///
  /// In en, this message translates to:
  /// **'Safer parking nearby'**
  String get navSaferParking;

  /// No description provided for @navScanSign.
  ///
  /// In en, this message translates to:
  /// **'Scan a sign'**
  String get navScanSign;

  /// No description provided for @navCommunityReport.
  ///
  /// In en, this message translates to:
  /// **'Community report'**
  String get navCommunityReport;

  /// No description provided for @navAlerts.
  ///
  /// In en, this message translates to:
  /// **'Alerts'**
  String get navAlerts;

  /// No description provided for @navTowRecovery.
  ///
  /// In en, this message translates to:
  /// **'Tow recovery'**
  String get navTowRecovery;

  /// No description provided for @navPrivacy.
  ///
  /// In en, this message translates to:
  /// **'Privacy and data'**
  String get navPrivacy;

  /// No description provided for @navMembership.
  ///
  /// In en, this message translates to:
  /// **'Membership'**
  String get navMembership;

  /// No description provided for @navAdministration.
  ///
  /// In en, this message translates to:
  /// **'Administration'**
  String get navAdministration;

  /// No description provided for @signOut.
  ///
  /// In en, this message translates to:
  /// **'Sign out'**
  String get signOut;

  /// No description provided for @membershipTitle.
  ///
  /// In en, this message translates to:
  /// **'Membership'**
  String get membershipTitle;

  /// No description provided for @membershipVerificationNotice.
  ///
  /// In en, this message translates to:
  /// **'Store purchases are credited only after server verification. ParkShield never accepts a client-declared purchase result or displays an invented price.'**
  String get membershipVerificationNotice;

  /// No description provided for @membershipPremium.
  ///
  /// In en, this message translates to:
  /// **'ParkShield Premium'**
  String get membershipPremium;

  /// No description provided for @membershipFree.
  ///
  /// In en, this message translates to:
  /// **'ParkShield Free'**
  String get membershipFree;

  /// No description provided for @purchasesDisabled.
  ///
  /// In en, this message translates to:
  /// **'Purchases are not available in this build. No charge can be initiated.'**
  String get purchasesDisabled;

  /// No description provided for @storeBridgeDisabled.
  ///
  /// In en, this message translates to:
  /// **'The server catalog is prepared, but this build is not connected to App Store or Google Play billing. No charge can be initiated.'**
  String get storeBridgeDisabled;

  /// No description provided for @storePresentsTerms.
  ///
  /// In en, this message translates to:
  /// **'Your device store presents the localized price and terms before confirmation.'**
  String get storePresentsTerms;

  /// No description provided for @continueInStore.
  ///
  /// In en, this message translates to:
  /// **'Continue in {store}'**
  String continueInStore(Object store);

  /// No description provided for @restorePurchases.
  ///
  /// In en, this message translates to:
  /// **'Restore store purchases'**
  String get restorePurchases;

  /// No description provided for @refreshMembership.
  ///
  /// In en, this message translates to:
  /// **'Refresh membership status'**
  String get refreshMembership;

  /// No description provided for @subscriptionDeletionNotice.
  ///
  /// In en, this message translates to:
  /// **'Deleting a ParkShield account does not cancel a subscription managed by Apple or Google. Cancel it in the same store account used to subscribe.'**
  String get subscriptionDeletionNotice;

  /// No description provided for @statusUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Status unavailable'**
  String get statusUnavailable;

  /// No description provided for @noStoreSubscription.
  ///
  /// In en, this message translates to:
  /// **'No store subscription'**
  String get noStoreSubscription;

  /// No description provided for @membershipStatus.
  ///
  /// In en, this message translates to:
  /// **'{store} · {status}'**
  String membershipStatus(Object status, Object store);

  /// No description provided for @membershipStatusThrough.
  ///
  /// In en, this message translates to:
  /// **'{store} · {status} · through {date}'**
  String membershipStatusThrough(Object date, Object status, Object store);

  /// No description provided for @membershipStatusFree.
  ///
  /// In en, this message translates to:
  /// **'free'**
  String get membershipStatusFree;

  /// No description provided for @membershipStatusActive.
  ///
  /// In en, this message translates to:
  /// **'active'**
  String get membershipStatusActive;

  /// No description provided for @membershipStatusGracePeriod.
  ///
  /// In en, this message translates to:
  /// **'grace period'**
  String get membershipStatusGracePeriod;

  /// No description provided for @membershipStatusPaused.
  ///
  /// In en, this message translates to:
  /// **'paused'**
  String get membershipStatusPaused;

  /// No description provided for @membershipStatusExpired.
  ///
  /// In en, this message translates to:
  /// **'expired'**
  String get membershipStatusExpired;

  /// No description provided for @membershipStatusRevoked.
  ///
  /// In en, this message translates to:
  /// **'revoked'**
  String get membershipStatusRevoked;

  /// No description provided for @membershipLoadError.
  ///
  /// In en, this message translates to:
  /// **'Membership status could not be loaded.'**
  String get membershipLoadError;

  /// No description provided for @purchaseNotCompleted.
  ///
  /// In en, this message translates to:
  /// **'The store purchase was not completed.'**
  String get purchaseNotCompleted;

  /// No description provided for @membershipVerified.
  ///
  /// In en, this message translates to:
  /// **'Membership verified by the store.'**
  String get membershipVerified;

  /// No description provided for @purchaseVerificationError.
  ///
  /// In en, this message translates to:
  /// **'The store purchase could not be verified. No access was granted.'**
  String get purchaseVerificationError;

  /// No description provided for @noPurchaseToRestore.
  ///
  /// In en, this message translates to:
  /// **'No store purchase was available to restore.'**
  String get noPurchaseToRestore;

  /// No description provided for @purchasesRestored.
  ///
  /// In en, this message translates to:
  /// **'Store purchases were restored and verified.'**
  String get purchasesRestored;

  /// No description provided for @restorePurchasesError.
  ///
  /// In en, this message translates to:
  /// **'Store purchases could not be restored.'**
  String get restorePurchasesError;

  /// No description provided for @privacyTitle.
  ///
  /// In en, this message translates to:
  /// **'Privacy and your data'**
  String get privacyTitle;

  /// No description provided for @privacyIntro.
  ///
  /// In en, this message translates to:
  /// **'Optional uses are off until you enable them. Essential security and parking requests are processed to provide the service.'**
  String get privacyIntro;

  /// No description provided for @consentProductAnalytics.
  ///
  /// In en, this message translates to:
  /// **'Product analytics'**
  String get consentProductAnalytics;

  /// No description provided for @consentPersonalizedRecommendations.
  ///
  /// In en, this message translates to:
  /// **'Personalized recommendations'**
  String get consentPersonalizedRecommendations;

  /// No description provided for @consentCommunityResearch.
  ///
  /// In en, this message translates to:
  /// **'Community research'**
  String get consentCommunityResearch;

  /// No description provided for @consentProductAnalyticsDescription.
  ///
  /// In en, this message translates to:
  /// **'Share de-identified product usage to improve reliability.'**
  String get consentProductAnalyticsDescription;

  /// No description provided for @consentPersonalizedRecommendationsDescription.
  ///
  /// In en, this message translates to:
  /// **'Use your prior choices to rank safer parking alternatives.'**
  String get consentPersonalizedRecommendationsDescription;

  /// No description provided for @consentCommunityResearchDescription.
  ///
  /// In en, this message translates to:
  /// **'Include de-identified reports in parking-safety research.'**
  String get consentCommunityResearchDescription;

  /// No description provided for @exportDataTitle.
  ///
  /// In en, this message translates to:
  /// **'Export your data'**
  String get exportDataTitle;

  /// No description provided for @exportDataDescription.
  ///
  /// In en, this message translates to:
  /// **'Creates a current JSON copy without passwords, MFA secrets, push tokens, or storage keys.'**
  String get exportDataDescription;

  /// No description provided for @createDataExport.
  ///
  /// In en, this message translates to:
  /// **'Create data export'**
  String get createDataExport;

  /// No description provided for @copyExportJson.
  ///
  /// In en, this message translates to:
  /// **'Copy export JSON'**
  String get copyExportJson;

  /// No description provided for @generatedDataExport.
  ///
  /// In en, this message translates to:
  /// **'Generated account data export'**
  String get generatedDataExport;

  /// No description provided for @deleteAccountTitle.
  ///
  /// In en, this message translates to:
  /// **'Delete account'**
  String get deleteAccountTitle;

  /// No description provided for @deleteAccountDescription.
  ///
  /// In en, this message translates to:
  /// **'This permanently removes the account, sessions, preferences, reports, appeals, and retained community evidence. It does not cancel an Apple or Google subscription; cancel that in the store. Pseudonymous billing evidence may be retained for reconciliation and legal obligations. This cannot be undone.'**
  String get deleteAccountDescription;

  /// No description provided for @currentPassword.
  ///
  /// In en, this message translates to:
  /// **'Current password'**
  String get currentPassword;

  /// No description provided for @mfaCodeOptional.
  ///
  /// In en, this message translates to:
  /// **'MFA code (if enabled)'**
  String get mfaCodeOptional;

  /// No description provided for @permanentlyDeleteAccount.
  ///
  /// In en, this message translates to:
  /// **'Permanently delete account'**
  String get permanentlyDeleteAccount;

  /// No description provided for @privacyLoadError.
  ///
  /// In en, this message translates to:
  /// **'Privacy choices could not be loaded.'**
  String get privacyLoadError;

  /// No description provided for @preferenceSaved.
  ///
  /// In en, this message translates to:
  /// **'{purpose} preference saved.'**
  String preferenceSaved(Object purpose);

  /// No description provided for @privacySaveError.
  ///
  /// In en, this message translates to:
  /// **'The privacy choice could not be saved.'**
  String get privacySaveError;

  /// No description provided for @dataExportReady.
  ///
  /// In en, this message translates to:
  /// **'Your data export is ready.'**
  String get dataExportReady;

  /// No description provided for @dataExportError.
  ///
  /// In en, this message translates to:
  /// **'Your data export could not be created.'**
  String get dataExportError;

  /// No description provided for @dataExportCopied.
  ///
  /// In en, this message translates to:
  /// **'Data export copied.'**
  String get dataExportCopied;

  /// No description provided for @enterCurrentPassword.
  ///
  /// In en, this message translates to:
  /// **'Enter your current password first.'**
  String get enterCurrentPassword;

  /// No description provided for @deleteAccountQuestion.
  ///
  /// In en, this message translates to:
  /// **'Delete your ParkShield account?'**
  String get deleteAccountQuestion;

  /// No description provided for @deleteAccountConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Your account and owned data will be permanently deleted.'**
  String get deleteAccountConfirmation;

  /// No description provided for @deletePermanently.
  ///
  /// In en, this message translates to:
  /// **'Delete permanently'**
  String get deletePermanently;

  /// No description provided for @deleteAccountError.
  ///
  /// In en, this message translates to:
  /// **'The account was not deleted. Verify your password, MFA code, and connection.'**
  String get deleteAccountError;

  /// No description provided for @alertsTitle.
  ///
  /// In en, this message translates to:
  /// **'Preventive alerts'**
  String get alertsTitle;

  /// No description provided for @alertsIntro.
  ///
  /// In en, this message translates to:
  /// **'When enabled, ParkShield may access location in the background to warn you after significant movement. Location checks are sent only for parking-risk evaluation.'**
  String get alertsIntro;

  /// No description provided for @automaticAlerts.
  ///
  /// In en, this message translates to:
  /// **'Automatic parking-risk alerts'**
  String get automaticAlerts;

  /// No description provided for @automaticAlertsPermission.
  ///
  /// In en, this message translates to:
  /// **'Requires Always Allow location permission. You can revoke it anytime.'**
  String get automaticAlertsPermission;

  /// No description provided for @quietHours.
  ///
  /// In en, this message translates to:
  /// **'Quiet hours'**
  String get quietHours;

  /// No description provided for @start.
  ///
  /// In en, this message translates to:
  /// **'Start'**
  String get start;

  /// No description provided for @end.
  ///
  /// In en, this message translates to:
  /// **'End'**
  String get end;

  /// No description provided for @timeZone.
  ///
  /// In en, this message translates to:
  /// **'Time zone'**
  String get timeZone;

  /// No description provided for @eastern.
  ///
  /// In en, this message translates to:
  /// **'Eastern'**
  String get eastern;

  /// No description provided for @central.
  ///
  /// In en, this message translates to:
  /// **'Central'**
  String get central;

  /// No description provided for @mountain.
  ///
  /// In en, this message translates to:
  /// **'Mountain'**
  String get mountain;

  /// No description provided for @pacific.
  ///
  /// In en, this message translates to:
  /// **'Pacific'**
  String get pacific;

  /// No description provided for @alaska.
  ///
  /// In en, this message translates to:
  /// **'Alaska'**
  String get alaska;

  /// No description provided for @hawaii.
  ///
  /// In en, this message translates to:
  /// **'Hawaii'**
  String get hawaii;

  /// No description provided for @saveQuietHours.
  ///
  /// In en, this message translates to:
  /// **'Save quiet hours'**
  String get saveQuietHours;

  /// No description provided for @alertsPermissionResume.
  ///
  /// In en, this message translates to:
  /// **'Enable Always Allow location permission to resume automatic alerts.'**
  String get alertsPermissionResume;

  /// No description provided for @alertsLoadError.
  ///
  /// In en, this message translates to:
  /// **'Alert preferences could not be loaded.'**
  String get alertsLoadError;

  /// No description provided for @alertsPermissionRequired.
  ///
  /// In en, this message translates to:
  /// **'Alerts remain off. Grant Always Allow location permission, then try again.'**
  String get alertsPermissionRequired;

  /// No description provided for @alertsActive.
  ///
  /// In en, this message translates to:
  /// **'Preventive parking alerts are active.'**
  String get alertsActive;

  /// No description provided for @alertsOff.
  ///
  /// In en, this message translates to:
  /// **'Preventive parking alerts are off.'**
  String get alertsOff;

  /// No description provided for @alertsUpdateError.
  ///
  /// In en, this message translates to:
  /// **'Alert settings could not be updated.'**
  String get alertsUpdateError;

  /// No description provided for @notificationRisk.
  ///
  /// In en, this message translates to:
  /// **'Parking risk {score}/100'**
  String notificationRisk(Object score);

  /// No description provided for @notificationChannel.
  ///
  /// In en, this message translates to:
  /// **'Parking risk alerts'**
  String get notificationChannel;

  /// No description provided for @notificationChannelDescription.
  ///
  /// In en, this message translates to:
  /// **'Preventive warnings when a parking location is risky.'**
  String get notificationChannelDescription;

  /// No description provided for @adminTitle.
  ///
  /// In en, this message translates to:
  /// **'Administration'**
  String get adminTitle;

  /// No description provided for @adminMfaNotice.
  ///
  /// In en, this message translates to:
  /// **'Privileged actions require a fresh authenticator code.'**
  String get adminMfaNotice;

  /// No description provided for @mfaCodeSixDigit.
  ///
  /// In en, this message translates to:
  /// **'6-digit MFA code'**
  String get mfaCodeSixDigit;

  /// No description provided for @enrollMfa.
  ///
  /// In en, this message translates to:
  /// **'Enroll MFA'**
  String get enrollMfa;

  /// No description provided for @openDashboard.
  ///
  /// In en, this message translates to:
  /// **'Open dashboard'**
  String get openDashboard;

  /// No description provided for @mfaSetupHelp.
  ///
  /// In en, this message translates to:
  /// **'Add this secret to your authenticator, then enter its code:'**
  String get mfaSetupHelp;

  /// No description provided for @confirmMfa.
  ///
  /// In en, this message translates to:
  /// **'Confirm MFA'**
  String get confirmMfa;

  /// No description provided for @metricUsers.
  ///
  /// In en, this message translates to:
  /// **'Users'**
  String get metricUsers;

  /// No description provided for @metricSessions.
  ///
  /// In en, this message translates to:
  /// **'Sessions'**
  String get metricSessions;

  /// No description provided for @metricPending.
  ///
  /// In en, this message translates to:
  /// **'Pending'**
  String get metricPending;

  /// No description provided for @metricPublished.
  ///
  /// In en, this message translates to:
  /// **'Published'**
  String get metricPublished;

  /// No description provided for @metricRejected.
  ///
  /// In en, this message translates to:
  /// **'Rejected'**
  String get metricRejected;

  /// No description provided for @auditVerified.
  ///
  /// In en, this message translates to:
  /// **'Audit chain verified'**
  String get auditVerified;

  /// No description provided for @auditFailure.
  ///
  /// In en, this message translates to:
  /// **'Audit integrity failure'**
  String get auditFailure;

  /// No description provided for @recordsChecked.
  ///
  /// In en, this message translates to:
  /// **'{count} records checked'**
  String recordsChecked(Object count);

  /// No description provided for @moderationQueue.
  ///
  /// In en, this message translates to:
  /// **'Moderation queue'**
  String get moderationQueue;

  /// No description provided for @evidencePercent.
  ///
  /// In en, this message translates to:
  /// **'{description}\nEvidence {percent}%'**
  String evidencePercent(Object description, Object percent);

  /// No description provided for @approve.
  ///
  /// In en, this message translates to:
  /// **'Approve'**
  String get approve;

  /// No description provided for @reject.
  ///
  /// In en, this message translates to:
  /// **'Reject'**
  String get reject;

  /// No description provided for @mfaEnabled.
  ///
  /// In en, this message translates to:
  /// **'MFA enabled.'**
  String get mfaEnabled;

  /// No description provided for @adminRequestError.
  ///
  /// In en, this message translates to:
  /// **'Administrative request failed. Verify role and MFA.'**
  String get adminRequestError;

  /// No description provided for @approveReport.
  ///
  /// In en, this message translates to:
  /// **'Approve report'**
  String get approveReport;

  /// No description provided for @rejectReport.
  ///
  /// In en, this message translates to:
  /// **'Reject report'**
  String get rejectReport;

  /// No description provided for @reason.
  ///
  /// In en, this message translates to:
  /// **'Reason'**
  String get reason;

  /// No description provided for @metricValue.
  ///
  /// In en, this message translates to:
  /// **'{label}: {value}'**
  String metricValue(Object label, Object value);

  /// No description provided for @communityTitle.
  ///
  /// In en, this message translates to:
  /// **'Community report'**
  String get communityTitle;

  /// No description provided for @communityIntro.
  ///
  /// In en, this message translates to:
  /// **'Reports are AI-screened and may require moderator review.'**
  String get communityIntro;

  /// No description provided for @reportType.
  ///
  /// In en, this message translates to:
  /// **'Report type'**
  String get reportType;

  /// No description provided for @newRestriction.
  ///
  /// In en, this message translates to:
  /// **'New restriction'**
  String get newRestriction;

  /// No description provided for @towingActivity.
  ///
  /// In en, this message translates to:
  /// **'Towing activity'**
  String get towingActivity;

  /// No description provided for @updatedPrice.
  ///
  /// In en, this message translates to:
  /// **'Updated price'**
  String get updatedPrice;

  /// No description provided for @parkingSign.
  ///
  /// In en, this message translates to:
  /// **'Parking sign'**
  String get parkingSign;

  /// No description provided for @whatObserved.
  ///
  /// In en, this message translates to:
  /// **'What did you observe?'**
  String get whatObserved;

  /// No description provided for @observationHint.
  ///
  /// In en, this message translates to:
  /// **'Include the restriction, time, price, or towing details.'**
  String get observationHint;

  /// No description provided for @addPhoto.
  ///
  /// In en, this message translates to:
  /// **'Add supporting photo'**
  String get addPhoto;

  /// No description provided for @photoAttached.
  ///
  /// In en, this message translates to:
  /// **'Photo attached'**
  String get photoAttached;

  /// No description provided for @submitReport.
  ///
  /// In en, this message translates to:
  /// **'Submit report'**
  String get submitReport;

  /// No description provided for @reportMinimumDetail.
  ///
  /// In en, this message translates to:
  /// **'Add at least 12 characters of useful detail.'**
  String get reportMinimumDetail;

  /// No description provided for @reportPublished.
  ///
  /// In en, this message translates to:
  /// **'Report verified and published.'**
  String get reportPublished;

  /// No description provided for @reportQueued.
  ///
  /// In en, this message translates to:
  /// **'Report received and queued for review.'**
  String get reportQueued;

  /// No description provided for @reportSubmitError.
  ///
  /// In en, this message translates to:
  /// **'The report could not be submitted.'**
  String get reportSubmitError;

  /// No description provided for @canIParkHere.
  ///
  /// In en, this message translates to:
  /// **'Can I park here?'**
  String get canIParkHere;

  /// No description provided for @mapEvaluationError.
  ///
  /// In en, this message translates to:
  /// **'Unable to evaluate this location. Read all posted signs.'**
  String get mapEvaluationError;

  /// No description provided for @mapUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Parking intelligence is temporarily unavailable.'**
  String get mapUnavailable;

  /// No description provided for @riskSafe.
  ///
  /// In en, this message translates to:
  /// **'Safe'**
  String get riskSafe;

  /// No description provided for @riskReadSigns.
  ///
  /// In en, this message translates to:
  /// **'Read signs'**
  String get riskReadSigns;

  /// No description provided for @riskHigh.
  ///
  /// In en, this message translates to:
  /// **'High risk'**
  String get riskHigh;

  /// No description provided for @riskDoNotPark.
  ///
  /// In en, this message translates to:
  /// **'Do not park'**
  String get riskDoNotPark;

  /// No description provided for @zoneGeneral.
  ///
  /// In en, this message translates to:
  /// **'General'**
  String get zoneGeneral;

  /// No description provided for @zoneResidents.
  ///
  /// In en, this message translates to:
  /// **'Residents'**
  String get zoneResidents;

  /// No description provided for @zonePrivate.
  ///
  /// In en, this message translates to:
  /// **'Private'**
  String get zonePrivate;

  /// No description provided for @zoneCommercial.
  ///
  /// In en, this message translates to:
  /// **'Commercial'**
  String get zoneCommercial;

  /// No description provided for @zoneTowHotspots.
  ///
  /// In en, this message translates to:
  /// **'Tow hotspots'**
  String get zoneTowHotspots;

  /// No description provided for @noVerifiedLocationData.
  ///
  /// In en, this message translates to:
  /// **'No verified data covers this location. Read every posted sign before parking.'**
  String get noVerifiedLocationData;

  /// No description provided for @noRestrictionSummary.
  ///
  /// In en, this message translates to:
  /// **'No restriction summary is available.'**
  String get noRestrictionSummary;

  /// No description provided for @estimatedTowingCost.
  ///
  /// In en, this message translates to:
  /// **'Estimated towing cost: {cost}'**
  String estimatedTowingCost(Object cost);

  /// No description provided for @knownTowingHotspot.
  ///
  /// In en, this message translates to:
  /// **'Known towing hotspot'**
  String get knownTowingHotspot;

  /// No description provided for @assistantTitle.
  ///
  /// In en, this message translates to:
  /// **'Parking Assistant'**
  String get assistantTitle;

  /// No description provided for @assistantIntro.
  ///
  /// In en, this message translates to:
  /// **'Ask about the current map location. Verified rules always outrank AI.'**
  String get assistantIntro;

  /// No description provided for @yourQuestion.
  ///
  /// In en, this message translates to:
  /// **'Your question'**
  String get yourQuestion;

  /// No description provided for @residentPermit.
  ///
  /// In en, this message translates to:
  /// **'I have a valid resident permit'**
  String get residentPermit;

  /// No description provided for @analyzeParking.
  ///
  /// In en, this message translates to:
  /// **'Analyze parking'**
  String get analyzeParking;

  /// No description provided for @assistantUnavailable.
  ///
  /// In en, this message translates to:
  /// **'The assistant is temporarily unavailable.'**
  String get assistantUnavailable;

  /// No description provided for @scoreValue.
  ///
  /// In en, this message translates to:
  /// **'Score {score}'**
  String scoreValue(Object score);

  /// No description provided for @understoodAs.
  ///
  /// In en, this message translates to:
  /// **'Understood as: {intent}'**
  String understoodAs(Object intent);

  /// No description provided for @lowConfidenceReview.
  ///
  /// In en, this message translates to:
  /// **'Low confidence: review current signs or request human verification.'**
  String get lowConfidenceReview;

  /// No description provided for @recommendationsTitle.
  ///
  /// In en, this message translates to:
  /// **'Safer parking nearby'**
  String get recommendationsTitle;

  /// No description provided for @recommendationsIntro.
  ///
  /// In en, this message translates to:
  /// **'Options balance walking distance, price, safety, towing history, ratings, and current availability.'**
  String get recommendationsIntro;

  /// No description provided for @maximumWalkingDistance.
  ///
  /// In en, this message translates to:
  /// **'Maximum walking distance'**
  String get maximumWalkingDistance;

  /// No description provided for @meters500.
  ///
  /// In en, this message translates to:
  /// **'500 meters'**
  String get meters500;

  /// No description provided for @kilometer1.
  ///
  /// In en, this message translates to:
  /// **'1 kilometer'**
  String get kilometer1;

  /// No description provided for @kilometers15.
  ///
  /// In en, this message translates to:
  /// **'1.5 kilometers'**
  String get kilometers15;

  /// No description provided for @kilometers3.
  ///
  /// In en, this message translates to:
  /// **'3 kilometers'**
  String get kilometers3;

  /// No description provided for @maximumHourlyPrice.
  ///
  /// In en, this message translates to:
  /// **'Maximum hourly price (optional)'**
  String get maximumHourlyPrice;

  /// No description provided for @findSaferParking.
  ///
  /// In en, this message translates to:
  /// **'Find safer parking'**
  String get findSaferParking;

  /// No description provided for @noVerifiedOptions.
  ///
  /// In en, this message translates to:
  /// **'No verified options match these filters.'**
  String get noVerifiedOptions;

  /// No description provided for @invalidHourlyPrice.
  ///
  /// In en, this message translates to:
  /// **'Enter a valid maximum hourly price.'**
  String get invalidHourlyPrice;

  /// No description provided for @recommendationsUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Parking recommendations are temporarily unavailable.'**
  String get recommendationsUnavailable;

  /// No description provided for @matchScore.
  ///
  /// In en, this message translates to:
  /// **'Match {score}'**
  String matchScore(Object score);

  /// No description provided for @walkSafety.
  ///
  /// In en, this message translates to:
  /// **'{meters} m walk · Safety {score}/100'**
  String walkSafety(Object meters, Object score);

  /// No description provided for @priceNotVerified.
  ///
  /// In en, this message translates to:
  /// **'Price not verified'**
  String get priceNotVerified;

  /// No description provided for @pricePerHour.
  ///
  /// In en, this message translates to:
  /// **'{price}/hour'**
  String pricePerHour(Object price);

  /// No description provided for @spacesAvailable.
  ///
  /// In en, this message translates to:
  /// **'{count} spaces reported available'**
  String spacesAvailable(Object count);

  /// No description provided for @sourceConfidence.
  ///
  /// In en, this message translates to:
  /// **'Source: {source} · {percent}% confidence'**
  String sourceConfidence(Object percent, Object source);

  /// No description provided for @recoveryTitle.
  ///
  /// In en, this message translates to:
  /// **'Find a towed vehicle'**
  String get recoveryTitle;

  /// No description provided for @recoveryIntro.
  ///
  /// In en, this message translates to:
  /// **'Search verified municipal and towing-provider records. Never pay from an unverified message or phone call.'**
  String get recoveryIntro;

  /// No description provided for @vehicleState.
  ///
  /// In en, this message translates to:
  /// **'Vehicle state'**
  String get vehicleState;

  /// No description provided for @stateHint.
  ///
  /// In en, this message translates to:
  /// **'FL'**
  String get stateHint;

  /// No description provided for @stateValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter a 2-letter state code'**
  String get stateValidation;

  /// No description provided for @licensePlate.
  ///
  /// In en, this message translates to:
  /// **'License plate'**
  String get licensePlate;

  /// No description provided for @plateValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter the license plate'**
  String get plateValidation;

  /// No description provided for @vinLastSix.
  ///
  /// In en, this message translates to:
  /// **'Last 6 VIN characters (optional)'**
  String get vinLastSix;

  /// No description provided for @vinValidation.
  ///
  /// In en, this message translates to:
  /// **'Enter exactly 6 characters'**
  String get vinValidation;

  /// No description provided for @searchTowRecords.
  ///
  /// In en, this message translates to:
  /// **'Search tow records'**
  String get searchTowRecords;

  /// No description provided for @towLookupUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Tow lookup is temporarily unavailable.'**
  String get towLookupUnavailable;

  /// No description provided for @verifiedRecordFound.
  ///
  /// In en, this message translates to:
  /// **'Verified record found'**
  String get verifiedRecordFound;

  /// No description provided for @noVerifiedRecord.
  ///
  /// In en, this message translates to:
  /// **'No verified record'**
  String get noVerifiedRecord;

  /// No description provided for @bringDocuments.
  ///
  /// In en, this message translates to:
  /// **'Bring: {documents}'**
  String bringDocuments(Object documents);

  /// No description provided for @paymentMethods.
  ///
  /// In en, this message translates to:
  /// **'Payment: {methods}'**
  String paymentMethods(Object methods);

  /// No description provided for @feesConfirmDirectly.
  ///
  /// In en, this message translates to:
  /// **'Fees: confirm directly'**
  String get feesConfirmDirectly;

  /// No description provided for @estimatedFees.
  ///
  /// In en, this message translates to:
  /// **'Estimated fees: {fees}'**
  String estimatedFees(Object fees);

  /// No description provided for @call.
  ///
  /// In en, this message translates to:
  /// **'Call'**
  String get call;

  /// No description provided for @scannerTitle.
  ///
  /// In en, this message translates to:
  /// **'Parking Sign Scanner'**
  String get scannerTitle;

  /// No description provided for @scannerIntro.
  ///
  /// In en, this message translates to:
  /// **'The selected image is analyzed in memory and is not retained by default.'**
  String get scannerIntro;

  /// No description provided for @camera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get camera;

  /// No description provided for @gallery.
  ///
  /// In en, this message translates to:
  /// **'Gallery'**
  String get gallery;

  /// No description provided for @scanPhotoError.
  ///
  /// In en, this message translates to:
  /// **'The sign could not be analyzed. Try a clearer photo.'**
  String get scanPhotoError;

  /// No description provided for @recoveredPhotoError.
  ///
  /// In en, this message translates to:
  /// **'The recovered photo could not be analyzed.'**
  String get recoveredPhotoError;

  /// No description provided for @towingRisk.
  ///
  /// In en, this message translates to:
  /// **'Towing risk {score}/100'**
  String towingRisk(Object score);

  /// No description provided for @detectedText.
  ///
  /// In en, this message translates to:
  /// **'Detected text: {text}'**
  String detectedText(Object text);

  /// No description provided for @scanLowConfidence.
  ///
  /// In en, this message translates to:
  /// **'Low confidence: read the physical sign or request human review.'**
  String get scanLowConfidence;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
