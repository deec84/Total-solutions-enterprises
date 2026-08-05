// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ParkShieldFoundation",
    platforms: [.iOS(.v17), .macOS(.v14)],
    products: [
        .library(name: "ParkShieldFoundation", targets: ["ParkShieldFoundation"]),
        .executable(name: "ParkShieldApp", targets: ["ParkShieldApp"]),
    ],
    targets: [
        .target(name: "ParkShieldFoundation"),
        .executableTarget(name: "ParkShieldApp", dependencies: ["ParkShieldFoundation"]),
        .testTarget(
            name: "ParkShieldFoundationTests",
            dependencies: ["ParkShieldFoundation"],
            resources: [.process("Resources")]
        ),
    ]
)
