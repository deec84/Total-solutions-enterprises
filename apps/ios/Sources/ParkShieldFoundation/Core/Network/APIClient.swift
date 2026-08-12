import Foundation

public protocol APIClient: Sendable {
    func execute(_ request: APIRequest) async throws -> APIResult
}

public struct APIRequest: Sendable {
    let method: String
    let path: String
    let body: Data?
    let headers: [String: String]

    public init(method: String, path: String, body: Data? = nil, headers: [String: String] = [:]) {
        self.method = method; self.path = path; self.body = body; self.headers = headers
    }
}

public enum APITransportError: Error, Sendable { case invalidURL, requestFailed }

public struct URLSessionAPIClient: APIClient {
    let baseURL: URL
    let session: URLSession
    public init(baseURL: URL, session: URLSession = .shared) { self.baseURL = baseURL; self.session = session }

    public func execute(_ request: APIRequest) async throws -> APIResult {
        guard let url = URL(string: request.path.trimmingCharacters(in: CharacterSet(charactersIn: "/")), relativeTo: baseURL) else { throw APITransportError.invalidURL }
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = request.method; urlRequest.httpBody = request.body; urlRequest.timeoutInterval = 15
        urlRequest.setValue("application/json", forHTTPHeaderField: "Accept")
        if request.body != nil { urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type") }
        request.headers.forEach { urlRequest.setValue($0.value, forHTTPHeaderField: $0.key) }
        let (data, response) = try await session.data(for: urlRequest)
        guard let http = response as? HTTPURLResponse else { throw APITransportError.requestFailed }
        if (200..<300).contains(http.statusCode) { return .success(statusCode: http.statusCode, body: data) }
        let error = try? JSONDecoder().decode(APIError.self, from: data)
        return .failure(statusCode: http.statusCode, error: error.flatMap { APIErrorContract.isValid($0) ? $0 : nil })
    }
}

public enum APIResult: Sendable {
    case success(statusCode: Int, body: Data)
    case failure(statusCode: Int, error: APIError?)
}
