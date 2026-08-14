import CoreLocation
import Foundation

/** Requests exactly one foreground location and retains neither it nor location history. */
public final class IOSForegroundLocationProvider: NSObject, ForegroundLocationProvider, CLLocationManagerDelegate, @unchecked Sendable {
    private let manager = CLLocationManager(); private var continuation: CheckedContinuation<LocationState, Never>?
    public override init() { super.init(); manager.delegate = self; manager.desiredAccuracy = kCLLocationAccuracyNearestTenMeters }
    public func current() async -> LocationState {
        switch manager.authorizationStatus { case .denied, .restricted: return .permissionDenied; case .notDetermined: manager.requestWhenInUseAuthorization(); return await wait(); default: return await wait() }
    }
    private func wait() async -> LocationState { await withCheckedContinuation { continuation in self.continuation = continuation; self.manager.requestLocation() } }
    public func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) { if manager.authorizationStatus == .denied || manager.authorizationStatus == .restricted { resume(.permissionDenied) } else if manager.authorizationStatus != .notDetermined { manager.requestLocation() } }
    public func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) { guard let item = locations.last else { resume(.unavailable); return }; resume(.available(ForegroundLocation(latitude: item.coordinate.latitude, longitude: item.coordinate.longitude, accuracyMeters: item.horizontalAccuracy, locatedAt: item.timestamp))) }
    public func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) { resume(.unavailable) }
    private func resume(_ state: LocationState) { continuation?.resume(returning: state); continuation = nil }
}
