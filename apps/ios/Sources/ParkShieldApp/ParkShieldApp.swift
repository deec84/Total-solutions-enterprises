import SwiftUI
#if canImport(ParkShieldFoundation)
import ParkShieldFoundation
#endif

@main
struct ParkShieldApp: App {
    private let controller = SessionController(
        repository: RestAuthenticationRepository(client: URLSessionAPIClient(baseURL: try! StaticAPIBaseURLProvider(value: "https://api.invalid/").baseURL())),
        sessions: SecureSessionStore(store: KeychainSecureValueStore())
    )
    var body: some Scene {
        WindowGroup {
            AuthRoot(controller: controller)
        }
    }
}

private struct AuthRoot: View {
    let controller: SessionController
    @State private var state: SessionState = .restoring
    var body: some View {
        Group {
            switch state {
            case .restoring: ProgressView("Restoring session").accessibilityLabel("Restoring session")
            case .signedIn: VStack(spacing: ParkShieldTokens.Spacing.large) { Text("You are signed in"); Button("Sign out") { Task { state = await controller.logout() } } }
            case .signedOut: LoginView { email, password in state = await controller.login(email: email, password: password) }
            case .failed(let error): LoginView(error: error) { email, password in state = await controller.login(email: email, password: password) }
            }
        }.task { state = await controller.restore() }
    }
}

private struct LoginView: View {
    var error: AuthFailure? = nil
    let signIn: (String, String) async -> Void
    @State private var email = ""; @State private var password = ""; @State private var loading = false
    var body: some View {
        VStack(spacing: ParkShieldTokens.Spacing.medium) {
            Text("Welcome to ParkShield AI").font(.title)
            TextField("Email", text: $email).accessibilityLabel("Email")
            SecureField("Password", text: $password).accessibilityLabel("Password")
            if let error { Text(message(error)).foregroundStyle(ParkShieldTokens.danger).accessibilityLabel("Login error") }
            Button(loading ? "Signing in" : "Sign in") { loading = true; Task { await signIn(email, password); password = ""; loading = false } }.disabled(loading || email.isEmpty || password.isEmpty)
        }.padding(ParkShieldTokens.Spacing.large)
    }
    private func message(_ error: AuthFailure) -> String { switch error { case .sessionInvalid: return "Your session has ended. Please sign in again."; case .remote(let code, _): return code == "RATE_LIMITED" ? "Too many attempts. Please wait and try again." : "Email or password is incorrect."; case .transport: return "Unable to sign in right now."; case .secureStorage: return "Secure storage is unavailable." } }
}
