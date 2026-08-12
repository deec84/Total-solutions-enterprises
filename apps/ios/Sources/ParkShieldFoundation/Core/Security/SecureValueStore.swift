import Foundation
import Security

public protocol SecureValueStore: Sendable {
    func read(for key: String) async throws -> String?
    func write(_ value: String, for key: String) async throws
    func removeValue(for key: String) async throws
}

public enum SecureStorageError: Error, Equatable, Sendable { case unavailable, corrupted }

/// Keychain-backed credential storage; no credential values are logged or exposed outside this boundary.
public struct KeychainSecureValueStore: SecureValueStore {
    private let service = "ai.parkshield.session.v1"

    public init() {}

    public func read(for key: String) async throws -> String? {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: key, kSecReturnData as String: true, kSecMatchLimit as String: kSecMatchLimitOne]
        var result: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess, let data = result as? Data, let value = String(data: data, encoding: .utf8) else { throw status == errSecDecode ? SecureStorageError.corrupted : SecureStorageError.unavailable }
        return value
    }

    public func write(_ value: String, for key: String) async throws {
        guard let data = value.data(using: .utf8) else { throw SecureStorageError.corrupted }
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: key]
        let attributes: [String: Any] = [kSecValueData as String: data, kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let update = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if update == errSecItemNotFound {
            var insert = query
            attributes.forEach { insert[$0.key] = $0.value }
            guard SecItemAdd(insert as CFDictionary, nil) == errSecSuccess else { throw SecureStorageError.unavailable }
        } else if update != errSecSuccess { throw SecureStorageError.unavailable }
    }

    public func removeValue(for key: String) async throws {
        let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword, kSecAttrService as String: service, kSecAttrAccount as String: key]
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else { throw SecureStorageError.unavailable }
    }
}
