"""
Coverage tests for services/rider_tracker.py.
Target: 100% line coverage.

রাইডার ট্র্যাকিং মডিউলের সকল ফাংশন ও শাখা কভার করা হয়েছে।
"""

import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class TestRiderStatusEnum:
    """Tests for RiderStatus enum."""

    def test_rider_status_values(self):
        """RiderStatus should have correct enum values."""
        from services.rider_tracker import RiderStatus

        assert RiderStatus.AVAILABLE.value == "available"
        assert RiderStatus.ASSIGNED.value == "assigned"
        assert RiderStatus.PICKING_UP.value == "picking_up"
        assert RiderStatus.IN_TRANSIT.value == "in_transit"
        assert RiderStatus.DELIVERED.value == "delivered"
        assert RiderStatus.UNAVAILABLE.value == "unavailable"
        assert RiderStatus.OFFLINE.value == "offline"


class TestLocationDataclass:
    """Tests for Location dataclass."""

    def test_location_creation(self):
        """Location should be creatable with lat, lng, timestamp."""
        from services.rider_tracker import Location

        now = datetime.now(timezone.utc)
        loc = Location(latitude=23.8, longitude=90.4, timestamp=now)
        assert loc.latitude == 23.8
        assert loc.longitude == 90.4
        assert loc.timestamp == now

    def test_location_is_frozen(self):
        """Location should be a frozen dataclass (immutable)."""
        from services.rider_tracker import Location

        now = datetime.now(timezone.utc)
        loc = Location(latitude=23.8, longitude=90.4, timestamp=now)
        with pytest.raises(Exception):
            loc.latitude = 24.0


class TestRiderDataclass:
    """Tests for Rider dataclass."""

    def test_rider_creation(self):
        """Rider should be creatable with all fields."""
        from services.rider_tracker import Location, Rider, RiderStatus

        now = datetime.now(timezone.utc)
        loc = Location(latitude=23.8, longitude=90.4, timestamp=now)
        rider = Rider(
            rider_id="rider1",
            name="Test Rider",
            phone="+880123456789",
            vehicle_type="motorcycle",
            status=RiderStatus.AVAILABLE,
            current_location=loc,
            active_order=None,
        )
        assert rider.rider_id == "rider1"
        assert rider.status == RiderStatus.AVAILABLE
        assert rider.current_location == loc

    def test_rider_without_location(self):
        """Rider should allow None for current_location."""
        from services.rider_tracker import Rider, RiderStatus

        rider = Rider(
            rider_id="rider1",
            name="Test Rider",
            phone="+880123456789",
            vehicle_type="motorcycle",
            status=RiderStatus.OFFLINE,
            current_location=None,
            active_order=None,
        )
        assert rider.current_location is None


class TestOrderDataclass:
    """Tests for Order dataclass."""

    def test_order_creation(self):
        """Order should be creatable with all fields."""
        from services.rider_tracker import Location, Order

        now = datetime.now(timezone.utc)
        pickup = Location(latitude=23.8, longitude=90.4, timestamp=now)
        dropoff = Location(latitude=23.9, longitude=90.5, timestamp=now)
        order = Order(
            order_id="order1",
            customer_id="cust1",
            pickup_location=pickup,
            dropoff_location=dropoff,
            assigned_rider=None,
            status="pending",
            created_at=now,
        )
        assert order.order_id == "order1"
        assert order.status == "pending"


class TestLocationTracker:
    """Tests for LocationTracker."""

    def test_init(self):
        """LocationTracker should initialize with cache."""
        from services.rider_tracker import LocationTracker

        with patch("services.rider_tracker.get_cache") as mock_get_cache:
            mock_cache = MagicMock()
            mock_get_cache.return_value = mock_cache
            tracker = LocationTracker()
            assert tracker.cache is not None

    @pytest.mark.asyncio
    async def test_update_location_success(self):
        """update_location should store location in cache."""
        from services.rider_tracker import Location, LocationTracker, RiderStatus

        with patch("services.rider_tracker.get_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_get_cache.return_value = mock_cache

            tracker = LocationTracker()
            now = datetime.now(timezone.utc)
            loc = Location(latitude=23.8, longitude=90.4, timestamp=now)

            result = await tracker.update_location(
                rider_id="rider1",
                latitude=23.8,
                longitude=90.4,
                status=RiderStatus.IN_TRANSIT,
            )
            assert result is True
            assert mock_cache.set.call_count >= 1

    @pytest.mark.asyncio
    async def test_get_rider_location_found(self):
        """get_rider_location should return location when found."""
        from services.rider_tracker import LocationTracker

        with patch("services.rider_tracker.get_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get.return_value = '{"latitude": 23.8, "longitude": 90.4}'
            mock_get_cache.return_value = mock_cache

            tracker = LocationTracker()
            result = await tracker.get_rider_location("rider1")
            assert result is not None
            assert result["latitude"] == 23.8

    @pytest.mark.asyncio
    async def test_get_rider_location_not_found(self):
        """get_rider_location should return None when not found."""
        from services.rider_tracker import LocationTracker

        with patch("services.rider_tracker.get_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.get.return_value = None
            mock_get_cache.return_value = mock_cache

            tracker = LocationTracker()
            result = await tracker.get_rider_location("nonexistent")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_nearby_riders(self):
        """get_nearby_riders should return riders within radius."""
        from services.rider_tracker import LocationTracker

        with patch("services.rider_tracker.get_cache") as mock_get_cache:
            mock_cache = AsyncMock()
            mock_cache.keys.return_value = ["rider:rider1", "rider:rider2"]
            mock_cache.get.side_effect = [
                '{"latitude": 23.8, "longitude": 90.4, "status": "available"}',
                '{"latitude": 23.9, "longitude": 90.5, "status": "available"}',
            ]
            mock_get_cache.return_value = mock_cache

            tracker = LocationTracker()
            result = await tracker.get_nearby_riders(latitude=23.8, longitude=90.4, radius_km=50)
            assert len(result) == 2

    def test_haversine_distance(self):
        """_haversine should calculate correct distance."""
        from services.rider_tracker import LocationTracker

        tracker = LocationTracker.__new__(LocationTracker)
        # ঢাকা থেকে নারায়ণগঞ্জ ~ 20km
        distance = tracker._haversine(23.8, 90.4, 23.6, 90.5)
        assert distance > 0
        assert distance < 50  # Should be within 50km

    def test_haversine_same_point(self):
        """_haversine should return 0 for same point."""
        from services.rider_tracker import LocationTracker

        tracker = LocationTracker.__new__(LocationTracker)
        distance = tracker._haversine(23.8, 90.4, 23.8, 90.4)
        assert distance == 0.0
