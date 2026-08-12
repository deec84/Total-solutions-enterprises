import Foundation
import Testing
@testable import ParkShieldFoundation

@Test func restLoginMapsTokenPairAndUsesVersionedPath() async {
    let client = RecordingClient(result: .success(statusCode: 200, body: Data("{\"access_token\":\"access\",\"refresh_token\":\"refresh\",\"expires_in\":900,\"token_type\":\"bearer\"}".utf8)))
    let result = await RestAuthenticationRepository(client: client).login(email: "person@example.test", password: "password")
    if case .success(let pair) = result { #expect(pair.refreshToken == "refresh") } else { Issue.record("Expected token pair") }
    #expect(await client.path == "/api/v1/auth/login")
}

@Test func restRefreshMapsSessionInvalid() async {
    let payload = Data("{\"version\":\"1\",\"code\":\"SESSION_INVALID\",\"message\":\"Session is invalid.\",\"correlation_id\":\"correlation-test\"}".utf8)
    let client = RecordingClient(result: .failure(statusCode: 401, error: try! JSONDecoder().decode(APIError.self, from: payload)))
    #expect(await RestAuthenticationRepository(client: client).refresh(refreshToken: "refresh") == .failure(.sessionInvalid))
}

private actor RecordingClient: APIClient {
    let result: APIResult; private(set) var path: String?
    init(result: APIResult) { self.result = result }
    func execute(_ request: APIRequest) async throws -> APIResult { path = request.path; return result }
}
