import Foundation

public struct SecureSessionStore: Sendable {
    private let store: any SecureValueStore
    public init(store: any SecureValueStore) { self.store = store }
    func save(_ pair: TokenPair) async -> Result<Void, AuthFailure> { do { try await store.write(pair.refreshToken, for: "refresh-token-v1"); try await store.write(pair.accessToken, for: "access-token-v1"); return .success(()) } catch { await clear(); return .failure(.secureStorage) } }
    func refreshToken() async -> Result<String?, AuthFailure> { do { return .success(try await store.read(for: "refresh-token-v1")) } catch { return .failure(.secureStorage) } }
    func accessToken() async -> Result<String?, AuthFailure> { do { return .success(try await store.read(for: "access-token-v1")) } catch { return .failure(.secureStorage) } }
    func clear() async { try? await store.removeValue(for: "access-token-v1"); try? await store.removeValue(for: "refresh-token-v1") }
}
