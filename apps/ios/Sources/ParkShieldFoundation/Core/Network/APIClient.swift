import Foundation

protocol APIClient: Sendable {
    func execute(_ request: APIRequest) async throws -> APIResult
}

struct APIRequest: Sendable {
    let method: String
    let path: String
    let body: Data?
}

enum APIResult: Sendable {
    case success(statusCode: Int, body: Data)
    case failure(statusCode: Int, error: APIError?)
}
