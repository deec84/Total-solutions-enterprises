import Foundation

/** Decodes a backend decision; it contains no client-side parking rules. */
public struct RestParkingDecisionRepository: ParkingDecisionRepository {
    let client: any APIClient
    public init(client: any APIClient) { self.client = client }
    public func evaluate(location: ForegroundLocation, accessToken: String) async -> Result<ParkingDecision, ParkingFailure> {
        var parts = URLComponents(); parts.queryItems = [URLQueryItem(name: "latitude", value: String(location.latitude)), URLQueryItem(name: "longitude", value: String(location.longitude)), URLQueryItem(name: "accuracy_meters", value: String(location.accuracyMeters)), URLQueryItem(name: "located_at", value: ISO8601DateFormatter().string(from: location.locatedAt)), URLQueryItem(name: "location_consent", value: "true")]
        do {
            let query = parts.percentEncodedQuery ?? ""
            let response = try await client.execute(APIRequest(method: "GET", path: "/api/v1/parking/decision/evaluate?\(query)", headers: ["Authorization": "Bearer \(accessToken)"]))
            switch response {
            case .success(_, let body):
                let decoder = JSONDecoder(); decoder.dateDecodingStrategy = .iso8601
                guard let decision = try? decoder.decode(ParkingDecision.self, from: body) else { return .failure(.service) }
                return .success(decision)
            case .failure(_, let error): return .failure(error?.code == "SESSION_INVALID" ? .sessionInvalid : .service)
            }
        } catch { return .failure(.offline) }
    }
}
