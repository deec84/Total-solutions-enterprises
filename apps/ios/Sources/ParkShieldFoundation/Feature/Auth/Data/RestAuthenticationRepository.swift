import Foundation

struct RestAuthenticationRepository: AuthenticationRepository {
    let client: any APIClient
    func login(email: String, password: String) async -> Result<TokenPair, AuthFailure> { await pair("/api/v1/auth/login", ["email": email, "password": password]) }
    func refresh(refreshToken: String) async -> Result<TokenPair, AuthFailure> { await pair("/api/v1/auth/refresh", ["refresh_token": refreshToken]) }
    func logout(refreshToken: String) async -> Result<Void, AuthFailure> {
        await execute(APIRequest(method: "POST", path: "/api/v1/auth/logout", body: json(["refresh_token": refreshToken]))) { result in
            if case .success(let status, _) = result, status == 204 { return .success(()) }; return .failure(self.failure(result))
        }
    }
    func profile(accessToken: String) async -> Result<AuthenticatedUser, AuthFailure> {
        await execute(APIRequest(method: "GET", path: "/api/v1/auth/me", headers: ["Authorization": "Bearer \(accessToken)"])) { result in
            guard case .success(_, let data) = result, let user = try? JSONDecoder().decode(AuthenticatedUser.self, from: data) else { return .failure(self.failure(result)) }; return .success(user)
        }
    }
    private func pair(_ path: String, _ payload: [String: String]) async -> Result<TokenPair, AuthFailure> {
        await execute(APIRequest(method: "POST", path: path, body: json(payload))) { result in
            guard case .success(_, let data) = result, let pair = try? JSONDecoder().decode(TokenPair.self, from: data) else { return .failure(self.failure(result)) }; return .success(pair)
        }
    }
    private func execute<T>(_ request: APIRequest, map: (APIResult) -> Result<T, AuthFailure>) async -> Result<T, AuthFailure> { do { return map(try await client.execute(request)) } catch { return .failure(.transport) } }
    private func json(_ value: [String: String]) -> Data? { try? JSONEncoder().encode(value) }
    private func failure(_ result: APIResult) -> AuthFailure { if case .failure(_, let error) = result { if error?.code == "SESSION_INVALID" { return .sessionInvalid }; if let error { return .remote(code: error.code, correlationID: error.correlationID) } }; return .transport }
}
