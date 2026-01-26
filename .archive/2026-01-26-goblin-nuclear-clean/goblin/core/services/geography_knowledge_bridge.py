"""
Geography Knowledge Bridge - Links Map Layers to Knowledge Articles

Connects the map layer system (TILE coordinates) with the /knowledge base,
providing bidirectional lookups between geographic locations and knowledge
articles.

Part of Alpha v1.0.0.67+ - Geographic Knowledge Integration
Version: 1.0.0
Author: uDOS System
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

try:
    from ..services.logging_manager import get_logger

    logger = get_logger("geography-knowledge")
except ImportError:
    # Standalone testing
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("geography-knowledge")


@dataclass
class KnowledgeLink:
    """Link between a geographic location and knowledge article."""

    coordinate: str  # Full coordinate (e.g., EARTH-OC-L100-AB34-CD15)
    guide_path: str  # Path to knowledge article
    title: str
    tags: List[str] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)

    @property
    def realm(self) -> str:
        """Extract realm from coordinate."""
        return self.coordinate.split("-")[0]

    @property
    def layer(self) -> int:
        """Extract layer from coordinate."""
        parts = self.coordinate.split("-")
        for part in parts:
            if part.startswith("L") and part[1:].isdigit():
                return int(part[1:])
        return 100  # Default


@dataclass
class POIInfo:
    """Point of Interest information."""

    id: str
    name: str
    coordinate: str
    type: str  # landmark, transport, natural, historical, etc.
    tags: List[str] = field(default_factory=list)
    description: str = ""
    cell: str = ""
    hazards: List[str] = field(default_factory=list)


@dataclass
class CityInfo:
    """City information with knowledge links."""

    id: str
    name: str
    country: str
    continent: str
    coordinate: str
    grid_cell: str
    layer: int

    knowledge_link: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    climate_tag: str = ""
    terrain_tags: List[str] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)

    districts: List[Dict[str, Any]] = field(default_factory=list)
    pois: List[POIInfo] = field(default_factory=list)

    timezone: str = ""
    population: int = 0
    emergency: str = ""


@dataclass
class CelestialInfo:
    """Celestial body information with knowledge links."""

    id: str
    name: str
    layer: int
    coordinate: str
    type: str  # planet, moon, dwarf_planet, etc.

    knowledge_link: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    related_articles: List[str] = field(default_factory=list)

    notable_locations: List[Dict[str, Any]] = field(default_factory=list)


class GeographyKnowledgeBridge:
    """
    Bridge between map layer system and knowledge base.

    Provides:
    - Coordinate → Knowledge article lookup
    - Tag-based article discovery
    - Related knowledge suggestions
    - POI and landmark information
    """

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize the bridge."""
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent

        self.project_root = project_root
        self.data_path = project_root / "core" / "data" / "spatial"
        self.knowledge_path = project_root / "knowledge" / "places"

        # Caches
        self._cities_cache: Dict[str, CityInfo] = {}
        self._celestial_cache: Dict[str, CelestialInfo] = {}
        self._coordinate_index: Dict[str, KnowledgeLink] = {}
        self._tag_index: Dict[str, List[str]] = {}

        # Load data
        self._load_data()
        logger.info("[LOCAL] Geography knowledge bridge initialized")

    def _load_data(self):
        """Load all geographic data with knowledge links."""
        self._load_cities()
        self._load_celestial()
        self._build_indices()

    def _load_cities(self):
        """Load city data with knowledge links."""
        cities_file = self.data_path / "cities-knowledge-linked.json"

        if not cities_file.exists():
            logger.warning(f"[LOCAL] Cities file not found: {cities_file}")
            return

        try:
            with open(cities_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for city_data in data.get("cities", []):
                city = self._parse_city(city_data)
                self._cities_cache[city.id] = city

                # Index by coordinate
                if city.coordinate:
                    self._coordinate_index[city.coordinate] = KnowledgeLink(
                        coordinate=city.coordinate,
                        guide_path=city.knowledge_link or "",
                        title=f"{city.name} City Guide",
                        tags=city.tags,
                        related_articles=city.related_articles,
                    )

            logger.info(f"[LOCAL] Loaded {len(self._cities_cache)} cities")

        except Exception as e:
            logger.error(f"[LOCAL] Error loading cities: {e}")

    def _parse_city(self, data: Dict) -> CityInfo:
        """Parse city data into CityInfo object."""
        coords = data.get("coordinates", {})
        knowledge = data.get("knowledge", {})
        quick_facts = data.get("quick_facts", {})

        city = CityInfo(
            id=data.get("id", ""),
            name=data.get("name", ""),
            country=data.get("country", ""),
            continent=data.get("continent", ""),
            coordinate=coords.get("full_coordinate", ""),
            grid_cell=coords.get("base_cell", ""),
            layer=coords.get("layer", 100),
            knowledge_link=knowledge.get("guide_path"),
            tags=knowledge.get("tags", []),
            climate_tag=knowledge.get("climate_tag", ""),
            terrain_tags=knowledge.get("terrain_tags", []),
            related_articles=knowledge.get("related_articles", []),
            timezone=quick_facts.get("timezone", ""),
            population=quick_facts.get("population", 0),
            emergency=quick_facts.get("emergency", ""),
        )

        # Parse districts
        for district_data in data.get("districts", []):
            city.districts.append(district_data)

            # Parse POIs
            for poi_data in district_data.get("pois", []):
                poi = POIInfo(
                    id=poi_data.get("id", ""),
                    name=poi_data.get("name", ""),
                    coordinate=poi_data.get("full_coordinate", ""),
                    type=poi_data.get("type", ""),
                    tags=poi_data.get("tags", []),
                    description=poi_data.get("description", ""),
                    cell=poi_data.get("cell", ""),
                    hazards=poi_data.get("hazards", []),
                )
                city.pois.append(poi)

        return city

    def _load_celestial(self):
        """Load celestial body data with knowledge links."""
        celestial_file = self.data_path / "celestial-knowledge-linked.json"

        if not celestial_file.exists():
            logger.warning(f"[LOCAL] Celestial file not found: {celestial_file}")
            return

        try:
            with open(celestial_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load planets
            for planet_data in data.get("planets", []):
                celestial = self._parse_celestial(planet_data)
                self._celestial_cache[celestial.id] = celestial

                if celestial.coordinate:
                    self._coordinate_index[celestial.coordinate] = KnowledgeLink(
                        coordinate=celestial.coordinate,
                        guide_path=celestial.knowledge_link or "",
                        title=f"{celestial.name} Guide",
                        tags=celestial.tags,
                        related_articles=celestial.related_articles,
                    )

                # Index moons
                for moon_data in planet_data.get("moons", []):
                    moon = self._parse_celestial(moon_data)
                    self._celestial_cache[moon.id] = moon
                    if moon.coordinate:
                        self._coordinate_index[moon.coordinate] = KnowledgeLink(
                            coordinate=moon.coordinate,
                            guide_path=moon.knowledge_link or "",
                            title=f"{moon.name} Guide",
                            tags=moon.tags,
                        )

            # Load dwarf planets
            for dwarf_data in data.get("dwarf_planets", []):
                celestial = self._parse_celestial(dwarf_data)
                self._celestial_cache[celestial.id] = celestial

            logger.info(f"[LOCAL] Loaded {len(self._celestial_cache)} celestial bodies")

        except Exception as e:
            logger.error(f"[LOCAL] Error loading celestial data: {e}")

    def _parse_celestial(self, data: Dict) -> CelestialInfo:
        """Parse celestial data into CelestialInfo object."""
        knowledge = data.get("knowledge", {})

        return CelestialInfo(
            id=data.get("id", ""),
            name=data.get("name", ""),
            layer=data.get("layer", 0),
            coordinate=data.get("coordinate", ""),
            type=data.get("type", ""),
            knowledge_link=knowledge.get("guide_path"),
            tags=knowledge.get("tags", []),
            related_articles=knowledge.get("related_articles", []),
            notable_locations=data.get("notable_locations", []),
        )

    def _build_indices(self):
        """Build search indices."""
        # Build tag index
        for coord, link in self._coordinate_index.items():
            for tag in link.tags:
                if tag not in self._tag_index:
                    self._tag_index[tag] = []
                self._tag_index[tag].append(coord)

        logger.info(f"[LOCAL] Built index with {len(self._tag_index)} tags")

    # ========== Public API ==========

    def get_knowledge_for_coordinate(self, coordinate: str) -> Optional[KnowledgeLink]:
        """
        Get knowledge article link for a coordinate.

        Args:
            coordinate: Full coordinate (e.g., EARTH-OC-L100-AB34-CD15)

        Returns:
            KnowledgeLink or None
        """
        # Exact match
        if coordinate in self._coordinate_index:
            return self._coordinate_index[coordinate]

        # Try parent coordinates (zoom out)
        parts = coordinate.split("-")
        while len(parts) > 2:
            parts.pop()
            parent = "-".join(parts)
            if parent in self._coordinate_index:
                return self._coordinate_index[parent]

        return None

    def get_city_info(self, city_id: str) -> Optional[CityInfo]:
        """Get city information by ID."""
        return self._cities_cache.get(city_id)

    def get_city_by_name(self, name: str) -> Optional[CityInfo]:
        """Get city information by name (case-insensitive)."""
        name_lower = name.lower()
        for city in self._cities_cache.values():
            if city.name.lower() == name_lower:
                return city
        return None

    def get_celestial_info(self, body_id: str) -> Optional[CelestialInfo]:
        """Get celestial body information by ID."""
        return self._celestial_cache.get(body_id)

    def search_by_tag(self, tag: str) -> List[str]:
        """
        Get all coordinates with a specific tag.

        Args:
            tag: Tag to search for (e.g., "coastal", "earthquake-prone")

        Returns:
            List of coordinates
        """
        return self._tag_index.get(tag.lower(), [])

    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[str]:
        """
        Search for coordinates matching tags.

        Args:
            tags: List of tags to match
            match_all: If True, require all tags; if False, any tag

        Returns:
            List of matching coordinates
        """
        if not tags:
            return []

        tag_sets = [set(self._tag_index.get(tag.lower(), [])) for tag in tags]

        if match_all:
            # Intersection - all tags required
            result = tag_sets[0]
            for tag_set in tag_sets[1:]:
                result = result.intersection(tag_set)
        else:
            # Union - any tag matches
            result = set()
            for tag_set in tag_sets:
                result = result.update(tag_set)

        return list(result) if result else []

    def get_related_knowledge(self, coordinate: str) -> List[str]:
        """
        Get related knowledge articles for a coordinate.

        Returns list of knowledge article paths.
        """
        link = self.get_knowledge_for_coordinate(coordinate)
        if link:
            return link.related_articles
        return []

    def get_pois_in_city(
        self, city_id: str, poi_type: Optional[str] = None
    ) -> List[POIInfo]:
        """
        Get POIs for a city, optionally filtered by type.

        Args:
            city_id: City ID
            poi_type: Optional filter (landmark, transport, natural, etc.)

        Returns:
            List of POIInfo
        """
        city = self._cities_cache.get(city_id)
        if not city:
            return []

        if poi_type:
            return [p for p in city.pois if p.type == poi_type]
        return city.pois

    def get_cities_by_climate(self, climate: str) -> List[CityInfo]:
        """Get all cities with a specific climate tag."""
        return [c for c in self._cities_cache.values() if c.climate_tag == climate]

    def get_cities_by_terrain(self, terrain: str) -> List[CityInfo]:
        """Get all cities with a specific terrain tag."""
        return [c for c in self._cities_cache.values() if terrain in c.terrain_tags]

    def list_all_cities(self) -> List[CityInfo]:
        """Get all cities."""
        return list(self._cities_cache.values())

    def list_all_celestial(self) -> List[CelestialInfo]:
        """Get all celestial bodies."""
        return list(self._celestial_cache.values())

    def format_city_summary(self, city_id: str) -> str:
        """
        Format a city summary for display.

        Returns formatted string.
        """
        city = self.get_city_info(city_id)
        if not city:
            return f"City not found: {city_id}"

        lines = [
            f"📍 {city.name}, {city.country}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Grid: {city.grid_cell} | Layer: {city.layer}",
            f"Coord: {city.coordinate}",
            f"",
            f"⏰ Timezone: {city.timezone}",
            f"🌡️ Climate: {city.climate_tag}",
            f"👥 Population: {city.population:,}" if city.population else "",
            f"🚨 Emergency: {city.emergency}" if city.emergency else "",
            f"",
            f"Tags: {', '.join(city.tags)}",
        ]

        if city.knowledge_link:
            lines.append(f"")
            lines.append(f"📚 Guide: {city.knowledge_link}")

        return "\n".join(line for line in lines if line or line == "")

    def format_celestial_summary(self, body_id: str) -> str:
        """Format a celestial body summary for display."""
        body = self.get_celestial_info(body_id)
        if not body:
            return f"Celestial body not found: {body_id}"

        lines = [
            f"🌌 {body.name}",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Type: {body.type}",
            f"Layer: {body.layer}",
            f"Coord: {body.coordinate}",
            f"",
            f"Tags: {', '.join(body.tags)}",
        ]

        if body.knowledge_link:
            lines.append(f"")
            lines.append(f"📚 Guide: {body.knowledge_link}")

        if body.notable_locations:
            lines.append(f"")
            lines.append(f"Notable Locations: {len(body.notable_locations)}")

        return "\n".join(lines)


# Singleton instance
_bridge_instance: Optional[GeographyKnowledgeBridge] = None


def get_geography_bridge() -> GeographyKnowledgeBridge:
    """Get or create singleton GeographyKnowledgeBridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = GeographyKnowledgeBridge()
    return _bridge_instance


# ========== Test ==========
if __name__ == "__main__":
    print("=" * 60)
    print("GEOGRAPHY KNOWLEDGE BRIDGE TEST")
    print("=" * 60)

    bridge = get_geography_bridge()

    # Test city lookup
    print("\n--- City Lookup ---")
    sydney = bridge.get_city_by_name("Sydney")
    if sydney:
        print(bridge.format_city_summary(sydney.id))

    # Test coordinate lookup
    print("\n--- Coordinate Lookup ---")
    link = bridge.get_knowledge_for_coordinate("EARTH-OC-L100-AB34-CD15")
    if link:
        print(f"Coordinate: {link.coordinate}")
        print(f"Guide: {link.guide_path}")
        print(f"Tags: {link.tags}")

    # Test celestial lookup
    print("\n--- Celestial Lookup ---")
    mars = bridge.get_celestial_info("mars")
    if mars:
        print(bridge.format_celestial_summary("mars"))

    # Test tag search
    print("\n--- Tag Search: coastal ---")
    coastal_cities = bridge.search_by_tag("coastal")
    print(f"Found {len(coastal_cities)} coastal locations")

    print("\n--- All Cities ---")
    for city in bridge.list_all_cities():
        print(f"  {city.name} ({city.country}) - {city.grid_cell}")
