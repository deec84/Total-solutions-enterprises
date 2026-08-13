import SwiftUI
#if canImport(ParkShieldFoundation)
import ParkShieldFoundation
#endif

enum ParkingUIState { case ready, loading, decision(ParkingDecision), location(String), failure(ParkingFailure) }

struct ParkingExperience: View {
    let controller: SessionController
    let repository: any ParkingDecisionRepository
    let provider: any ForegroundLocationProvider
    let signOut: () async -> Void
    @State private var state: ParkingUIState = .ready
    var body: some View {
        VStack(spacing: ParkShieldTokens.Spacing.medium) {
            content
            Button("Check parking") { Task { await check() } }.disabled(isLoading).accessibilityHint("Requests your current foreground location")
            Button("Sign out") { Task { await signOut() } }
        }.padding(ParkShieldTokens.Spacing.large)
    }
    @ViewBuilder private var content: some View {
        switch state {
        case .ready: Text("Check parking at your current location")
        case .loading: ProgressView("Checking parking").accessibilityLabel("Checking parking")
        case .location(let message): Text(message).accessibilityLabel("Parking status: \(message)")
        case .failure(let failure): Text(failure == .offline ? "No connection. Check your network and try again." : "Parking service is unavailable. Please try again.")
        case .decision(let decision): DecisionView(decision: decision)
        }
    }
    private var isLoading: Bool { if case .loading = state { return true }; return false }
    private func check() async {
        state = .loading
        switch await provider.current() {
        case .permissionDenied: state = .location("Location permission was denied. You can enable it in system settings.")
        case .unavailable: state = .location("Your location is unavailable. Try again when GPS is ready.")
        case .available(let location):
            guard case .success(let token?) = await controller.accessToken() else { await signOut(); return }
            switch await repository.evaluate(location: location, accessToken: token) {
            case .success(let decision): state = .decision(decision)
            case .failure(.sessionInvalid): await signOut()
            case .failure(let error): state = .failure(error)
            }
        }
    }
}

private struct DecisionView: View {
    let decision: ParkingDecision
    var body: some View {
        VStack(spacing: ParkShieldTokens.Spacing.small) {
            Text(headline).font(.title2).accessibilityLabel("Parking decision: \(headline)")
            ForEach(Array(decision.reasons.enumerated()), id: \.offset) { _, reason in Text(reason.message) }
            if let evidence = decision.evidence { Text("Source: \(evidence.provenance). Confidence: \(Int(evidence.confidence * 100))%.") }
            if decision.outcome != .PARK || decision.coverageStatus != .VERIFIED_COVERAGE { Text("Review current parking signs before parking.").fontWeight(.semibold) }
        }
    }
    private var headline: String { switch decision.outcome { case .PARK: return "Parking may be allowed"; case .CAUTION: return "Use caution"; case .DO_NOT_PARK: return "Do not park"; case .INDETERMINATE: return "Parking cannot be determined" } }
}
