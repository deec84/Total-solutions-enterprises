import XCTest
@testable import ParkShieldFoundation

final class ParkingContractTests: XCTestCase {
    func testParkingOutcomeDecodesFromBackendContract() throws {
        let body = #"{"outcome":"DO_NOT_PARK","coverage_status":"VERIFIED_COVERAGE","reasons":[{"code":"TOWING_RISK","message":"Towing risk."}],"evaluated_at":"2026-01-01T00:00:00Z","evidence":null}"#.data(using: .utf8)!
        let value = try JSONDecoder().decode(ParkingDecision.self, from: body)
        XCTAssertEqual(value.outcome, .DO_NOT_PARK)
        XCTAssertEqual(value.coverageStatus, .VERIFIED_COVERAGE)
    }
}
