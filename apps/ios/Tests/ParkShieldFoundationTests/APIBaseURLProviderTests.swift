import Testing
@testable import ParkShieldFoundation

@Test func acceptsInjectedPlaceholderBaseURL() throws { #expect(try StaticAPIBaseURLProvider(value: "https://api.invalid/").baseURL().host == "api.invalid") }
@Test func rejectsNonPlaceholderBaseURL() { #expect(throws: APIBaseURLConfigurationError.self) { try StaticAPIBaseURLProvider(value: "https://example.com/").baseURL() } }
