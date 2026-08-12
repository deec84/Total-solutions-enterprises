import Foundation

public protocol APIBaseURLProvider: Sendable { func baseURL() throws -> URL }
public enum APIBaseURLConfigurationError: Error, Sendable { case invalid }
public struct StaticAPIBaseURLProvider: APIBaseURLProvider {
    let value: String
    public init(value: String) { self.value = value }
    public func baseURL() throws -> URL {
        guard let url = URL(string: value), url.scheme == "https", url.host?.hasSuffix(".invalid") == true else { throw APIBaseURLConfigurationError.invalid }
        return url
    }
}
