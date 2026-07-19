// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get appTitle => 'ParkShield AI';

  @override
  String appSectionTitle(Object section) {
    return 'ParkShield AI · $section';
  }

  @override
  String get email => 'Correo electrónico';

  @override
  String get password => 'Contraseña';

  @override
  String get cancel => 'Cancelar';

  @override
  String get confirm => 'Confirmar';

  @override
  String get navigate => 'Navegar';

  @override
  String sourceWithValue(Object source) {
    return 'Fuente: $source';
  }

  @override
  String confidencePercent(Object percent) {
    return 'Confianza: $percent%';
  }

  @override
  String get provenanceOfficialData => 'Datos oficiales';

  @override
  String get provenanceAiPrediction => 'Predicción de IA';

  @override
  String get provenanceCommunityVerified => 'Verificado por la comunidad';

  @override
  String get provenanceEstimated => 'Estimado';

  @override
  String get riskVerySafe => 'Muy seguro';

  @override
  String get riskVeryHigh => 'Riesgo muy alto';

  @override
  String get parkWithConfidence => 'Estaciona con confianza';

  @override
  String get enterValidEmail => 'Ingresa un correo electrónico válido.';

  @override
  String get passwordMinimum =>
      'La contraseña debe contener al menos 12 caracteres.';

  @override
  String get signIn => 'Iniciar sesión';

  @override
  String get forgotPassword => '¿Olvidaste tu contraseña?';

  @override
  String get createAccount => 'Crear cuenta';

  @override
  String get verifyEmail => 'Verificar correo';

  @override
  String get authSignInError =>
      'No se pudo iniciar sesión. Revisa tus credenciales.';

  @override
  String get authRequestError =>
      'No se pudo completar la solicitud. Inténtalo de nuevo.';

  @override
  String get checkEmailVerification =>
      'Revisa tu correo para verificar la cuenta.';

  @override
  String get recoverPassword => 'Recuperar contraseña';

  @override
  String get recoveryInstructions =>
      'Ingresa tu correo. Si existe una cuenta, enviaremos instrucciones de recuperación.';

  @override
  String get sendInstructions => 'Enviar instrucciones';

  @override
  String get haveRecoveryToken => 'Tengo un token de recuperación';

  @override
  String get recoverySent =>
      'Si la cuenta existe, se enviaron las instrucciones.';

  @override
  String get setNewPassword => 'Establecer nueva contraseña';

  @override
  String get recoveryToken => 'Token de recuperación';

  @override
  String get enterRecoveryToken => 'Ingresa el token de recuperación.';

  @override
  String get newPassword => 'Nueva contraseña';

  @override
  String get updatePassword => 'Actualizar contraseña';

  @override
  String get passwordUpdated =>
      'Contraseña actualizada. Inicia sesión con la nueva contraseña.';

  @override
  String get verificationHelp =>
      'Abre tu enlace de verificación o pega el token a continuación.';

  @override
  String get verificationToken => 'Token de verificación';

  @override
  String get verifyAccount => 'Verificar cuenta';

  @override
  String get emailVerified => 'Correo verificado. Ya puedes iniciar sesión.';

  @override
  String get navMap => 'Mapa';

  @override
  String get navAssistant => 'Asistente';

  @override
  String get navSaferParking => 'Estacionamiento más seguro';

  @override
  String get navScanSign => 'Escanear letrero';

  @override
  String get navCommunityReport => 'Reporte comunitario';

  @override
  String get navAlerts => 'Alertas';

  @override
  String get navTowRecovery => 'Recuperar vehículo';

  @override
  String get navPrivacy => 'Privacidad y datos';

  @override
  String get navMembership => 'Membresía';

  @override
  String get navAdministration => 'Administración';

  @override
  String get signOut => 'Cerrar sesión';

  @override
  String get membershipTitle => 'Membresía';

  @override
  String get membershipVerificationNotice =>
      'Las compras se acreditan solo después de verificarlas en el servidor. ParkShield nunca acepta una compra declarada por el cliente ni muestra un precio inventado.';

  @override
  String get membershipPremium => 'ParkShield Premium';

  @override
  String get membershipFree => 'ParkShield Gratis';

  @override
  String get purchasesDisabled =>
      'Las compras no están disponibles en esta compilación. No se puede iniciar ningún cobro.';

  @override
  String get storeBridgeDisabled =>
      'El catálogo del servidor está preparado, pero esta compilación no está conectada con la facturación de App Store o Google Play. No se puede iniciar ningún cobro.';

  @override
  String get storePresentsTerms =>
      'La tienda de tu dispositivo muestra el precio y las condiciones localizadas antes de confirmar.';

  @override
  String continueInStore(Object store) {
    return 'Continuar en $store';
  }

  @override
  String get restorePurchases => 'Restaurar compras de la tienda';

  @override
  String get refreshMembership => 'Actualizar estado de membresía';

  @override
  String get subscriptionDeletionNotice =>
      'Eliminar una cuenta de ParkShield no cancela una suscripción administrada por Apple o Google. Cancélala en la misma cuenta de la tienda usada para suscribirte.';

  @override
  String get statusUnavailable => 'Estado no disponible';

  @override
  String get noStoreSubscription => 'Sin suscripción de tienda';

  @override
  String membershipStatus(Object status, Object store) {
    return '$store · $status';
  }

  @override
  String membershipStatusThrough(Object date, Object status, Object store) {
    return '$store · $status · hasta $date';
  }

  @override
  String get membershipStatusFree => 'gratis';

  @override
  String get membershipStatusActive => 'activa';

  @override
  String get membershipStatusGracePeriod => 'período de gracia';

  @override
  String get membershipStatusPaused => 'pausada';

  @override
  String get membershipStatusExpired => 'vencida';

  @override
  String get membershipStatusRevoked => 'revocada';

  @override
  String get membershipLoadError =>
      'No se pudo cargar el estado de la membresía.';

  @override
  String get purchaseNotCompleted => 'La compra en la tienda no se completó.';

  @override
  String get membershipVerified => 'Membresía verificada por la tienda.';

  @override
  String get purchaseVerificationError =>
      'No se pudo verificar la compra. No se concedió acceso.';

  @override
  String get noPurchaseToRestore =>
      'No había compras de tienda para restaurar.';

  @override
  String get purchasesRestored => 'Las compras se restauraron y verificaron.';

  @override
  String get restorePurchasesError => 'No se pudieron restaurar las compras.';

  @override
  String get privacyTitle => 'Privacidad y tus datos';

  @override
  String get privacyIntro =>
      'Los usos opcionales permanecen desactivados hasta que los habilites. La seguridad esencial y las solicitudes de estacionamiento se procesan para prestar el servicio.';

  @override
  String get consentProductAnalytics => 'Analítica del producto';

  @override
  String get consentPersonalizedRecommendations =>
      'Recomendaciones personalizadas';

  @override
  String get consentCommunityResearch => 'Investigación comunitaria';

  @override
  String get consentProductAnalyticsDescription =>
      'Comparte el uso desidentificado del producto para mejorar la confiabilidad.';

  @override
  String get consentPersonalizedRecommendationsDescription =>
      'Usa tus decisiones previas para ordenar alternativas de estacionamiento más seguras.';

  @override
  String get consentCommunityResearchDescription =>
      'Incluye reportes desidentificados en investigaciones de seguridad de estacionamiento.';

  @override
  String get exportDataTitle => 'Exportar tus datos';

  @override
  String get exportDataDescription =>
      'Crea una copia JSON actual sin contraseñas, secretos MFA, tokens push ni claves de almacenamiento.';

  @override
  String get createDataExport => 'Crear exportación de datos';

  @override
  String get copyExportJson => 'Copiar JSON exportado';

  @override
  String get generatedDataExport =>
      'Exportación generada de datos de la cuenta';

  @override
  String get deleteAccountTitle => 'Eliminar cuenta';

  @override
  String get deleteAccountDescription =>
      'Esto elimina permanentemente la cuenta, sesiones, preferencias, reportes, apelaciones y evidencia comunitaria conservada. No cancela una suscripción de Apple o Google; cancélala en la tienda. La evidencia de facturación seudónima puede conservarse para conciliación y obligaciones legales. Esta acción no se puede deshacer.';

  @override
  String get currentPassword => 'Contraseña actual';

  @override
  String get mfaCodeOptional => 'Código MFA (si está habilitado)';

  @override
  String get permanentlyDeleteAccount => 'Eliminar cuenta permanentemente';

  @override
  String get privacyLoadError =>
      'No se pudieron cargar las opciones de privacidad.';

  @override
  String preferenceSaved(Object purpose) {
    return 'Se guardó la preferencia de $purpose.';
  }

  @override
  String get privacySaveError => 'No se pudo guardar la opción de privacidad.';

  @override
  String get dataExportReady => 'Tu exportación de datos está lista.';

  @override
  String get dataExportError => 'No se pudo crear tu exportación de datos.';

  @override
  String get dataExportCopied => 'Exportación de datos copiada.';

  @override
  String get enterCurrentPassword => 'Primero ingresa tu contraseña actual.';

  @override
  String get deleteAccountQuestion => '¿Eliminar tu cuenta de ParkShield?';

  @override
  String get deleteAccountConfirmation =>
      'Tu cuenta y tus datos se eliminarán permanentemente.';

  @override
  String get deletePermanently => 'Eliminar permanentemente';

  @override
  String get deleteAccountError =>
      'La cuenta no se eliminó. Revisa tu contraseña, código MFA y conexión.';

  @override
  String get alertsTitle => 'Alertas preventivas';

  @override
  String get alertsIntro =>
      'Cuando están habilitadas, ParkShield puede acceder a la ubicación en segundo plano para advertirte después de un movimiento significativo. Las comprobaciones solo se envían para evaluar el riesgo de estacionamiento.';

  @override
  String get automaticAlerts => 'Alertas automáticas de riesgo';

  @override
  String get automaticAlertsPermission =>
      'Requiere permiso de ubicación Siempre. Puedes revocarlo cuando quieras.';

  @override
  String get quietHours => 'Horas de silencio';

  @override
  String get start => 'Inicio';

  @override
  String get end => 'Fin';

  @override
  String get timeZone => 'Zona horaria';

  @override
  String get eastern => 'Este';

  @override
  String get central => 'Central';

  @override
  String get mountain => 'Montaña';

  @override
  String get pacific => 'Pacífico';

  @override
  String get alaska => 'Alaska';

  @override
  String get hawaii => 'Hawái';

  @override
  String get saveQuietHours => 'Guardar horas de silencio';

  @override
  String get alertsPermissionResume =>
      'Habilita el permiso de ubicación Siempre para reanudar las alertas automáticas.';

  @override
  String get alertsLoadError =>
      'No se pudieron cargar las preferencias de alertas.';

  @override
  String get alertsPermissionRequired =>
      'Las alertas siguen apagadas. Otorga permiso de ubicación Siempre e inténtalo de nuevo.';

  @override
  String get alertsActive => 'Las alertas preventivas están activas.';

  @override
  String get alertsOff => 'Las alertas preventivas están desactivadas.';

  @override
  String get alertsUpdateError =>
      'No se pudo actualizar la configuración de alertas.';

  @override
  String notificationRisk(Object score) {
    return 'Riesgo de estacionamiento $score/100';
  }

  @override
  String get notificationChannel => 'Alertas de riesgo de estacionamiento';

  @override
  String get notificationChannelDescription =>
      'Advertencias preventivas cuando una ubicación de estacionamiento es riesgosa.';

  @override
  String get adminTitle => 'Administración';

  @override
  String get adminMfaNotice =>
      'Las acciones privilegiadas requieren un código nuevo del autenticador.';

  @override
  String get mfaCodeSixDigit => 'Código MFA de 6 dígitos';

  @override
  String get enrollMfa => 'Inscribir MFA';

  @override
  String get openDashboard => 'Abrir panel';

  @override
  String get mfaSetupHelp =>
      'Agrega este secreto a tu autenticador y luego ingresa su código:';

  @override
  String get confirmMfa => 'Confirmar MFA';

  @override
  String get metricUsers => 'Usuarios';

  @override
  String get metricSessions => 'Sesiones';

  @override
  String get metricPending => 'Pendientes';

  @override
  String get metricPublished => 'Publicados';

  @override
  String get metricRejected => 'Rechazados';

  @override
  String get auditVerified => 'Cadena de auditoría verificada';

  @override
  String get auditFailure => 'Falla de integridad de auditoría';

  @override
  String recordsChecked(Object count) {
    return '$count registros comprobados';
  }

  @override
  String get moderationQueue => 'Cola de moderación';

  @override
  String evidencePercent(Object description, Object percent) {
    return '$description\nEvidencia $percent%';
  }

  @override
  String get approve => 'Aprobar';

  @override
  String get reject => 'Rechazar';

  @override
  String get mfaEnabled => 'MFA habilitado.';

  @override
  String get adminRequestError =>
      'La solicitud administrativa falló. Revisa el rol y MFA.';

  @override
  String get approveReport => 'Aprobar reporte';

  @override
  String get rejectReport => 'Rechazar reporte';

  @override
  String get reason => 'Motivo';

  @override
  String metricValue(Object label, Object value) {
    return '$label: $value';
  }

  @override
  String get communityTitle => 'Reporte comunitario';

  @override
  String get communityIntro =>
      'Los reportes son examinados por IA y pueden requerir revisión de un moderador.';

  @override
  String get reportType => 'Tipo de reporte';

  @override
  String get newRestriction => 'Nueva restricción';

  @override
  String get towingActivity => 'Actividad de remolque';

  @override
  String get updatedPrice => 'Precio actualizado';

  @override
  String get parkingSign => 'Letrero de estacionamiento';

  @override
  String get whatObserved => '¿Qué observaste?';

  @override
  String get observationHint =>
      'Incluye la restricción, hora, precio o detalles del remolque.';

  @override
  String get addPhoto => 'Agregar foto de apoyo';

  @override
  String get photoAttached => 'Foto adjunta';

  @override
  String get submitReport => 'Enviar reporte';

  @override
  String get reportMinimumDetail =>
      'Agrega al menos 12 caracteres de información útil.';

  @override
  String get reportPublished => 'Reporte verificado y publicado.';

  @override
  String get reportQueued => 'Reporte recibido y puesto en cola para revisión.';

  @override
  String get reportSubmitError => 'No se pudo enviar el reporte.';

  @override
  String get canIParkHere => '¿Puedo estacionar aquí?';

  @override
  String get mapEvaluationError =>
      'No se pudo evaluar esta ubicación. Lee todos los letreros publicados.';

  @override
  String get mapUnavailable =>
      'La inteligencia de estacionamiento no está disponible temporalmente.';

  @override
  String get riskSafe => 'Seguro';

  @override
  String get riskReadSigns => 'Lee los letreros';

  @override
  String get riskHigh => 'Alto riesgo';

  @override
  String get riskDoNotPark => 'No estaciones';

  @override
  String get zoneGeneral => 'General';

  @override
  String get zoneResidents => 'Residentes';

  @override
  String get zonePrivate => 'Privado';

  @override
  String get zoneCommercial => 'Comercial';

  @override
  String get zoneTowHotspots => 'Zonas de remolque';

  @override
  String get noVerifiedLocationData =>
      'No hay datos verificados para esta ubicación. Lee todos los letreros antes de estacionar.';

  @override
  String get noRestrictionSummary =>
      'No hay un resumen de restricciones disponible.';

  @override
  String estimatedTowingCost(Object cost) {
    return 'Costo estimado de remolque: $cost';
  }

  @override
  String get knownTowingHotspot => 'Zona conocida de remolque';

  @override
  String get assistantTitle => 'Asistente de estacionamiento';

  @override
  String get assistantIntro =>
      'Pregunta por la ubicación actual del mapa. Las reglas verificadas siempre tienen prioridad sobre la IA.';

  @override
  String get yourQuestion => 'Tu pregunta';

  @override
  String get residentPermit => 'Tengo un permiso de residente válido';

  @override
  String get analyzeParking => 'Analizar estacionamiento';

  @override
  String get assistantUnavailable =>
      'El asistente no está disponible temporalmente.';

  @override
  String scoreValue(Object score) {
    return 'Puntuación $score';
  }

  @override
  String understoodAs(Object intent) {
    return 'Interpretado como: $intent';
  }

  @override
  String get lowConfidenceReview =>
      'Baja confianza: revisa los letreros actuales o solicita verificación humana.';

  @override
  String get recommendationsTitle => 'Estacionamiento más seguro cercano';

  @override
  String get recommendationsIntro =>
      'Las opciones equilibran distancia a pie, precio, seguridad, historial de remolques, calificaciones y disponibilidad actual.';

  @override
  String get maximumWalkingDistance => 'Distancia máxima a pie';

  @override
  String get meters500 => '500 metros';

  @override
  String get kilometer1 => '1 kilómetro';

  @override
  String get kilometers15 => '1,5 kilómetros';

  @override
  String get kilometers3 => '3 kilómetros';

  @override
  String get maximumHourlyPrice => 'Precio máximo por hora (opcional)';

  @override
  String get findSaferParking => 'Buscar estacionamiento más seguro';

  @override
  String get noVerifiedOptions =>
      'Ninguna opción verificada coincide con estos filtros.';

  @override
  String get invalidHourlyPrice => 'Ingresa un precio máximo por hora válido.';

  @override
  String get recommendationsUnavailable =>
      'Las recomendaciones no están disponibles temporalmente.';

  @override
  String matchScore(Object score) {
    return 'Coincidencia $score';
  }

  @override
  String walkSafety(Object meters, Object score) {
    return '$meters m a pie · Seguridad $score/100';
  }

  @override
  String get priceNotVerified => 'Precio no verificado';

  @override
  String pricePerHour(Object price) {
    return '$price/hora';
  }

  @override
  String spacesAvailable(Object count) {
    return '$count espacios reportados como disponibles';
  }

  @override
  String sourceConfidence(Object percent, Object source) {
    return 'Fuente: $source · $percent% de confianza';
  }

  @override
  String get recoveryTitle => 'Encontrar un vehículo remolcado';

  @override
  String get recoveryIntro =>
      'Busca registros municipales y de proveedores de remolque verificados. Nunca pagues desde un mensaje o llamada no verificados.';

  @override
  String get vehicleState => 'Estado del vehículo';

  @override
  String get stateHint => 'FL';

  @override
  String get stateValidation => 'Ingresa un código estatal de 2 letras';

  @override
  String get licensePlate => 'Matrícula';

  @override
  String get plateValidation => 'Ingresa la matrícula';

  @override
  String get vinLastSix => 'Últimos 6 caracteres del VIN (opcional)';

  @override
  String get vinValidation => 'Ingresa exactamente 6 caracteres';

  @override
  String get searchTowRecords => 'Buscar registros de remolque';

  @override
  String get towLookupUnavailable =>
      'La búsqueda de remolque no está disponible temporalmente.';

  @override
  String get verifiedRecordFound => 'Registro verificado encontrado';

  @override
  String get noVerifiedRecord => 'Sin registro verificado';

  @override
  String bringDocuments(Object documents) {
    return 'Lleva: $documents';
  }

  @override
  String paymentMethods(Object methods) {
    return 'Pago: $methods';
  }

  @override
  String get feesConfirmDirectly => 'Tarifas: confirmar directamente';

  @override
  String estimatedFees(Object fees) {
    return 'Tarifas estimadas: $fees';
  }

  @override
  String get call => 'Llamar';

  @override
  String get scannerTitle => 'Escáner de letreros';

  @override
  String get scannerIntro =>
      'La imagen seleccionada se analiza en memoria y no se conserva de forma predeterminada.';

  @override
  String get camera => 'Cámara';

  @override
  String get gallery => 'Galería';

  @override
  String get scanPhotoError =>
      'No se pudo analizar el letrero. Prueba con una foto más clara.';

  @override
  String get recoveredPhotoError => 'No se pudo analizar la foto recuperada.';

  @override
  String towingRisk(Object score) {
    return 'Riesgo de remolque $score/100';
  }

  @override
  String detectedText(Object text) {
    return 'Texto detectado: $text';
  }

  @override
  String get scanLowConfidence =>
      'Baja confianza: lee el letrero físico o solicita revisión humana.';
}
