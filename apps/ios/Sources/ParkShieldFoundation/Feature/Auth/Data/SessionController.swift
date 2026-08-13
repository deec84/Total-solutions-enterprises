import Foundation

public enum SessionState: Equatable, Sendable { case signedOut, restoring, signedIn, failed(AuthFailure) }

public actor SessionController {
    private let repository: any AuthenticationRepository
    private let sessions: SecureSessionStore
    private var refreshTask: Task<SessionState, Never>?
    private(set) var state: SessionState = .signedOut
    public init(repository: any AuthenticationRepository, sessions: SecureSessionStore) { self.repository = repository; self.sessions = sessions }
    public func restore() async -> SessionState { state = .restoring; return await refresh() }
    public func login(email: String, password: String) async -> SessionState { switch await repository.login(email: email, password: password) { case .success(let pair): return await persist(pair); case .failure(let error): state = .failed(error); return state } }
    public func refresh() async -> SessionState { if let task = refreshTask { return await task.value }; let task = Task { await self.refreshStored() }; refreshTask = task; let result = await task.value; refreshTask = nil; return result }
    public func logout() async -> SessionState { if case .success(let token?) = await sessions.refreshToken() { _ = await repository.logout(refreshToken: token) }; await sessions.clear(); state = .signedOut; return state }
    public func accessToken() async -> Result<String?, AuthFailure> { await sessions.accessToken() }
    private func refreshStored() async -> SessionState { switch await sessions.refreshToken() { case .failure(let error): state = .failed(error); case .success(nil): state = .signedOut; case .success(.some(let token)): switch await repository.refresh(refreshToken: token) { case .success(let pair): return await persist(pair); case .failure(let error): await sessions.clear(); state = error == .sessionInvalid ? .signedOut : .failed(error) } }; return state }
    private func persist(_ pair: TokenPair) async -> SessionState { switch await sessions.save(pair) { case .success: state = .signedIn; case .failure(let error): state = .failed(error) }; return state }
}
