import Foundation
import Testing
@testable import ParkShieldFoundation

@Test func acceptsPublicV1ValidationError() throws {
    let fixtureURL = try #require(Bundle.module.url(forResource: "validation-failed.v1", withExtension: "json"))
    let error = try JSONDecoder().decode(APIError.self, from: Data(contentsOf: fixtureURL))

    #expect(APIErrorContract.isValid(error))
    #expect(error.code == "VALIDATION_FAILED")
}

@Test func rejectsNonAllowlistedDetails() {
    let error = APIError(
        version: "1",
        code: "VALIDATION_FAILED",
        message: "Invalid request.",
        correlationID: "fixture",
        details: [APIErrorDetail(field: "password", code: "RAW_MESSAGE")]
    )
    #expect(!APIErrorContract.isValid(error))
}
