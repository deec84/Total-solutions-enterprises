import Foundation
import Testing
@testable import ParkShieldFoundation

@Test func loginPersistsCredentialsOnlyInSecureStore() async {
    let store = MemorySecureStore()
    let controller = SessionController(repository: FakeRepository(login: .success(pair)), sessions: SecureSessionStore(store: store))
    #expect(await controller.login(email: "person@example.test", password: "password") == .signedIn)
    #expect(await store.value("refresh-token-v1") == "refresh-new")
    #expect(await store.value("access-token-v1") == "access-new")
}

@Test func concurrentRefreshIsSingleFlight() async {
    let store = MemorySecureStore(["refresh-token-v1": "refresh-old"])
    let repository = FakeRepository(refresh: .success(pair), delayRefresh: true)
    let controller = SessionController(repository: repository, sessions: SecureSessionStore(store: store))
    async let first = controller.refresh(); async let second = controller.refresh()
    #expect(await first == .signedIn); #expect(await second == .signedIn)
    #expect(await repository.refreshCalls == 1)
}

@Test func sessionInvalidClearsCredentialsAndFailsClosed() async {
    let store = MemorySecureStore(["refresh-token-v1": "refresh-old", "access-token-v1": "access-old"])
    let controller = SessionController(repository: FakeRepository(refresh: .failure(.sessionInvalid)), sessions: SecureSessionStore(store: store))
    #expect(await controller.refresh() == .signedOut)
    #expect(await store.isEmpty)
}

@Test func logoutAlwaysClearsLocalCredentials() async {
    let store = MemorySecureStore(["refresh-token-v1": "refresh-old", "access-token-v1": "access-old"])
    let controller = SessionController(repository: FakeRepository(logout: .failure(.transport)), sessions: SecureSessionStore(store: store))
    #expect(await controller.logout() == .signedOut)
    #expect(await store.isEmpty)
}

@Test func secureStoreFailureDoesNotRetainCredentials() async {
    let store = MemorySecureStore(failWrites: true)
    let controller = SessionController(repository: FakeRepository(login: .success(pair)), sessions: SecureSessionStore(store: store))
    #expect(await controller.login(email: "person@example.test", password: "password") == .failed(.secureStorage))
    #expect(await store.isEmpty)
}

private let pair = TokenPair(accessToken: "access-new", refreshToken: "refresh-new", expiresIn: 900, tokenType: "bearer")

private actor MemorySecureStore: SecureValueStore {
    private var values: [String: String]
    private let failWrites: Bool
    init(_ values: [String: String] = [:], failWrites: Bool = false) { self.values = values; self.failWrites = failWrites }
    func read(for key: String) async throws -> String? { values[key] }
    func write(_ value: String, for key: String) async throws { if failWrites { throw SecureStorageError.unavailable }; values[key] = value }
    func removeValue(for key: String) async throws { values.removeValue(forKey: key) }
    func value(_ key: String) -> String? { values[key] }
    var isEmpty: Bool { values.isEmpty }
}

private actor FakeRepository: AuthenticationRepository {
    let loginResult: Result<TokenPair, AuthFailure>
    let refreshResult: Result<TokenPair, AuthFailure>
    let logoutResult: Result<Void, AuthFailure>
    let delayRefresh: Bool
    private(set) var refreshCalls = 0
    init(login: Result<TokenPair, AuthFailure> = .failure(.transport), refresh: Result<TokenPair, AuthFailure> = .failure(.transport), logout: Result<Void, AuthFailure> = .success(()), delayRefresh: Bool = false) { loginResult = login; refreshResult = refresh; logoutResult = logout; self.delayRefresh = delayRefresh }
    func login(email: String, password: String) async -> Result<TokenPair, AuthFailure> { loginResult }
    func refresh(refreshToken: String) async -> Result<TokenPair, AuthFailure> { refreshCalls += 1; if delayRefresh { try? await Task.sleep(for: .milliseconds(50)) }; return refreshResult }
    func logout(refreshToken: String) async -> Result<Void, AuthFailure> { logoutResult }
    func profile(accessToken: String) async -> Result<AuthenticatedUser, AuthFailure> { .failure(.transport) }
}
