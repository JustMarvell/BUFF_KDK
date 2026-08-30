package com.whnyh.app.data

data class Faculty(
    val id: Int,
    val name: String,
    val address: String?,
    val lng: Double,
    val lat: Double
)

data class BoardingHouse(
    val id: Int,
    val name: String,
    val description: String?,
    val address: String?,
    val price_min: Int,
    val price_max: Int,
    val room_type: String?,
    val facilities: List<String>?,
    val photos: List<String>?,
    val contact: String?,
    val owner_name: String?,
    val lng: Double,
    val lat: Double,
    val distance_m: Double?,
    val road_condition: String? = null,
    val suitability_score: Double? = null
)

data class RoadSegmentFeature(
    val type: String,
    val geometry: GeoJsonGeometry,
    val properties: RoadSegmentProperties
)

data class GeoJsonGeometry(
    val type: String
    // coordinates deliberately omitted here - shape differs by type
    // (Point/LineString/MultiLineString). We'll parse those separately
    // once we get to drawing them on the map.
)

data class RoadSegmentProperties(
    val id: Int,
    val name: String?,
    val condition: String,
    val notes: String?
)

data class RoadSegmentCollection(
    val type: String,
    val features: List<RoadSegmentFeature>
)

data class RouteResponse(
    val distance_m: Double,
    val duration_s: Double,
    val geometry: RouteGeometry,
    val road_condition_overlay: List<RoadOverlaySegment>,
    val overall_condition: String,
    val condition_breakdown: Map<String, Int>
)

data class RoadOverlaySegment(
    val id: Int,
    val name: String?,
    val condition: String,
    val notes: String?,
    val geometry: com.google.gson.JsonObject
)

data class RouteGeometry(
    val type: String,
    val coordinates: List<List<Double>>
)