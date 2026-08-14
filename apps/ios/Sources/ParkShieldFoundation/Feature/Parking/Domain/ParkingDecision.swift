import Foundation

public enum ParkingOutcome: String, Codable, Sendable { case PARK, CAUTION, DO_NOT_PARK, INDETERMINATE }
public enum CoverageStatus: String, Codable, Sendable { case VERIFIED_COVERAGE, NO_VERIFIED_COVERAGE, STALE_DATA, LOCATION_PRECISION_INSUFFICIENT, UNVERIFIABLE_SOURCE, LOCATION_CONSENT_REQUIRED, LOCATION_STALE }
public struct ParkingReason: Codable, Sendable { public let code: String; public let message: String }
public struct ParkingEvidence: Codable, Sendable { public let provenance: String; public let confidence: Double; public let observedAt: Date; public let expiresAt: Date?; public let sourceID: String?; public let importBatchID: String?; public let restrictionSummary: String?
    enum CodingKeys: String, CodingKey { case provenance, confidence; case observedAt = "observed_at"; case expiresAt = "expires_at"; case sourceID = "source_id"; case importBatchID = "import_batch_id"; case restrictionSummary = "restriction_summary" }
}
public struct ParkingDecision: Codable, Sendable { public let outcome: ParkingOutcome; public let coverageStatus: CoverageStatus; public let reasons: [ParkingReason]; public let evidence: ParkingEvidence?
    enum CodingKeys: String, CodingKey { case outcome, reasons, evidence; case coverageStatus = "coverage_status" }
}
public struct ForegroundLocation: Sendable { public let latitude: Double; public let longitude: Double; public let accuracyMeters: Double; public let locatedAt: Date }
public enum LocationState: Sendable { case permissionDenied, unavailable, available(ForegroundLocation) }
public enum ParkingFailure: Error, Sendable, Equatable { case offline, service, sessionInvalid }
public protocol ParkingDecisionRepository: Sendable { func evaluate(location: ForegroundLocation, accessToken: String) async -> Result<ParkingDecision, ParkingFailure> }
public protocol ForegroundLocationProvider: Sendable { func current() async -> LocationState }
