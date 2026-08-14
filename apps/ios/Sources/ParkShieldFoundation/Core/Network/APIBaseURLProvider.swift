import Foundation

public protocol APIBaseURLProvider: Sendable { func baseURL() throws -> URL }
public enum APIBaseURLConfigurationError: Error, Sendable { case invalid }
public struct StaticAPIBaseURLProvider: APIBaseURLProvider {
    let value: String; let allowedHosts: Set<String>
    public init(value: String, allowedHosts: Set<String> = ["api.invalid"]) { self.value = value; self.allowedHosts = allowedHosts }
    public func baseURL() throws -> URL {
        guard let url = URL(string: value), url.scheme == "https", let host = url.host, allowedHosts.contains(host) else { throw APIBaseURLConfigurationError.invalid }
        return url
    }
}

public enum PilotAPIConfiguration {
    public static func provider(bundle: Bundle = .main) throws -> any APIBaseURLProvider {
        let value = bundle.object(forInfoDictionaryKey: "PARKSHIELD_API_BASE_URL") as? String ?? "https://api.invalid/"
        let hosts = (bundle.object(forInfoDictionaryKey: "PARKSHIELD_API_ALLOWED_HOSTS") as? String ?? "api.invalid").split(separator: ",").map { String($0).trimmingCharacters(in: .whitespaces) }
        return StaticAPIBaseURLProvider(value: value, allowedHosts: Set(hosts))
    }
}
