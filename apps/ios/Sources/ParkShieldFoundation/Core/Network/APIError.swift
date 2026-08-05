import Foundation

struct APIError: Decodable, Equatable, Sendable {
    let version: String
    let code: String
    let message: String
    let correlationID: String
    let details: [APIErrorDetail]?

    enum CodingKeys: String, CodingKey {
        case version, code, message, details
        case correlationID = "correlation_id"
    }
}

struct APIErrorDetail: Decodable, Equatable, Sendable {
    let field: String
    let code: String
}

enum APIErrorContract {
    static let version = "1"
    private static let allowedDetailCodes: Set<String> = ["MISSING_FIELD", "INVALID_FIELD"]
    private static let correlationIDPattern = "^[A-Za-z0-9._:-]{1,128}$"
    private static let fieldPattern = "^[A-Za-z0-9_.\\[\\]-]{1,128}$"

    static func isValid(_ error: APIError) -> Bool {
        guard error.version == version,
              !error.code.isEmpty,
              !error.message.isEmpty,
              error.correlationID.range(of: correlationIDPattern, options: .regularExpression) != nil
        else { return false }

        return (error.details ?? []).allSatisfy {
            $0.field.range(of: fieldPattern, options: .regularExpression) != nil &&
                allowedDetailCodes.contains($0.code)
        }
    }
}
