import Foundation

protocol APIBaseURLProvider: Sendable { func baseURL() throws -> URL }
enum APIBaseURLConfigurationError: Error, Sendable { case invalid }
struct StaticAPIBaseURLProvider: APIBaseURLProvider {
    let value: String
    func baseURL() throws -> URL {
        guard let url = URL(string: value), url.scheme == "https", url.host?.hasSuffix(".invalid") == true else { throw APIBaseURLConfigurationError.invalid }
        return url
    }
}
