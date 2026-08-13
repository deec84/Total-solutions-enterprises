import XCTest
@testable import ParkShieldFoundation

final class ParkingContractTests: XCTestCase {
    func testParkingOutcomeDecodesFromBackendContract() throws {
        let body = #"{"outcome":"DO_NOT_PARK","coverage_status":"VERIFIED_COVERAGE","reasons":[{"code":"TOWING_RISK","message":"Towing risk."}],"evaluated_at":"2026-01-01T00:00:00Z","evidence":null}"#.data(using: .utf8)!
        let value = try JSONDecoder().decode(ParkingDecision.self, from: body)
        XCTAssertEqual(value.outcome, .DO_NOT_PARK)
        XCTAssertEqual(value.coverageStatus, .VERIFIED_COVERAGE)
    }

    func testAllTypedOutcomesDecodeWithoutClientDecisionRules() throws {
        for outcome in ["PARK", "CAUTION", "DO_NOT_PARK", "INDETERMINATE"] {
            let body = """{"outcome":"\(outcome)","coverage_status":"NO_VERIFIED_COVERAGE","reasons":[{"code":"NO_VERIFIED_COVERAGE","message":"No verified coverage."}],"evaluated_at":"2026-01-01T00:00:00Z","evidence":null}""".data(using: .utf8)!
            XCTAssertEqual(try JSONDecoder().decode(ParkingDecision.self, from: body).outcome.rawValue, outcome)
        }
    }
}
