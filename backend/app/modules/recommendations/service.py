"""Explainable multi-factor recommendation ranking."""

from app.modules.recommendations.domain import (
    ParkingCandidate,
    ParkingFacilityRepository,
    ParkingRecommendation,
)


class ParkingRecommendationService:
    def __init__(self, repository: ParkingFacilityRepository) -> None:
        self._repository = repository

    async def nearby(
        self,
        longitude: float,
        latitude: float,
        radius_meters: int = 1500,
        max_hourly_price_cents: int | None = None,
        limit: int = 10,
    ) -> tuple[ParkingRecommendation, ...]:
        candidates = await self._repository.nearby(
            longitude,
            latitude,
            radius_meters,
            min(max(limit * 5, 20), 100),
        )
        if max_hourly_price_cents is not None:
            candidates = tuple(
                item
                for item in candidates
                if item.facility.hourly_price_cents is not None
                and item.facility.hourly_price_cents <= max_hourly_price_cents
            )
        ranked = sorted(
            (self._rank(item, radius_meters, max_hourly_price_cents) for item in candidates),
            key=lambda item: (
                -item.ranking_score,
                item.walking_distance_meters,
                item.facility.name,
            ),
        )
        return tuple(ranked[:limit])

    @staticmethod
    def _rank(
        candidate: ParkingCandidate,
        radius_meters: int,
        max_hourly_price_cents: int | None,
    ) -> ParkingRecommendation:
        facility = candidate.facility
        safety = facility.safety_score / 100
        distance = max(0.0, 1 - candidate.walking_distance_meters / radius_meters)
        price_reference = max_hourly_price_cents or 5000
        price = (
            0.5
            if facility.hourly_price_cents is None
            else max(0.0, 1 - facility.hourly_price_cents / max(price_reference, 1))
        )
        towing = max(0.0, 1 - facility.towing_incidents_per_1000 / 50)
        rating = 0.5 if facility.rating is None else facility.rating / 5
        availability = (
            facility.available_spaces / facility.capacity
            if facility.available_spaces is not None
            and facility.capacity is not None
            and facility.capacity > 0
            else 0.5
        )
        weighted = (
            safety * 0.40
            + distance * 0.20
            + price * 0.15
            + towing * 0.15
            + rating * 0.05
            + min(max(availability, 0), 1) * 0.05
        )
        reasons = [f"Safety score {facility.safety_score}/100."]
        reasons.append(f"About {round(candidate.walking_distance_meters)} meters away.")
        if facility.hourly_price_cents is None:
            reasons.append("Current price is not verified; confirm before parking.")
        elif facility.hourly_price_cents == 0:
            reasons.append("Listed as free parking.")
        else:
            reasons.append(f"Listed at ${facility.hourly_price_cents / 100:.2f} per hour.")
        if facility.towing_incidents_per_1000 <= 5:
            reasons.append("Low historical towing frequency.")
        elif facility.towing_incidents_per_1000 >= 25:
            reasons.append("Elevated historical towing frequency.")
        return ParkingRecommendation(
            facility=facility,
            walking_distance_meters=round(candidate.walking_distance_meters),
            ranking_score=round(min(max(weighted, 0), 1) * 100),
            reasons=tuple(reasons),
        )
