import Foundation

public struct TokenPair: Codable, Equatable, Sendable {
    let accessToken: String; let refreshToken: String; let expiresIn: Int; let tokenType: String
    enum CodingKeys: String, CodingKey { case accessToken = "access_token", refreshToken = "refresh_token", expiresIn = "expires_in", tokenType = "token_type" }
}

public struct AuthenticatedUser: Codable, Equatable, Sendable {
    let id: String; let email: String; let role: String; let isVerified: Bool
    enum CodingKeys: String, CodingKey { case id, email, role; case isVerified = "is_verified" }
}

public enum AuthFailure: Error, Equatable, Sendable { case remote(code: String, correlationID: String?), sessionInvalid, transport, secureStorage }

public protocol AuthenticationRepository: Sendable {
    func login(email: String, password: String) async -> Result<TokenPair, AuthFailure>
    func refresh(refreshToken: String) async -> Result<TokenPair, AuthFailure>
    func logout(refreshToken: String) async -> Result<Void, AuthFailure>
    func profile(accessToken: String) async -> Result<AuthenticatedUser, AuthFailure>
}
