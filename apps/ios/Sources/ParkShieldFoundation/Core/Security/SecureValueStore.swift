protocol SecureValueStore: Sendable {
    func read(for key: String) async throws -> String?
    func write(_ value: String, for key: String) async throws
    func removeValue(for key: String) async throws
}
