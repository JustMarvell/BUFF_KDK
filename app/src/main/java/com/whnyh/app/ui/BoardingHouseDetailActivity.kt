package com.whnyh.app.ui

import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.whnyh.kdk.R
import com.whnyh.app.data.BoardingHouse
import com.whnyh.app.data.Faculty
import com.whnyh.app.data.RetrofitClient
import com.whnyh.app.data.RoadOverlaySegment
import com.whnyh.app.data.RouteResponse
import kotlinx.coroutines.launch
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.XYTileSource
import org.osmdroid.util.BoundingBox
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.CustomZoomButtonsController
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline

class BoardingHouseDetailActivity : AppCompatActivity() {

    companion object {
        const val EXTRA_BOARDING_HOUSE_ID = "boarding_house_id"
    }

    private lateinit var map: MapView
    private lateinit var facultySpinner: Spinner
    private lateinit var profileSpinner: Spinner
    private lateinit var routeSummary: TextView

    private var faculties: List<Faculty> = emptyList()
    private var boardingHouse: BoardingHouse? = null
    private val profiles = listOf("driving", "walking", "cycling")

    override fun onCreate(savedInstanceState: Bundle?) {
        Configuration.getInstance().load(
            applicationContext,
            android.preference.PreferenceManager.getDefaultSharedPreferences(applicationContext)
        )
        Configuration.getInstance().userAgentValue = packageName

        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_boarding_house_detail)

        val id = intent.getIntExtra(EXTRA_BOARDING_HOUSE_ID, -1)
        if (id == -1) {
            finish()
            return
        }

        map = findViewById(R.id.detail_map)
        map.setTileSource(cartoVoyagerTileSource())
        map.setMultiTouchControls(true)
        map.zoomController.setVisibility(CustomZoomButtonsController.Visibility.SHOW_AND_FADEOUT)

        facultySpinner = findViewById(R.id.detail_faculty_spinner)
        profileSpinner = findViewById(R.id.detail_profile_spinner)
        routeSummary = findViewById(R.id.route_summary)

        val profileAdapter = ArrayAdapter(this, android.R.layout.simple_spinner_item, profiles)
        profileAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        profileSpinner.adapter = profileAdapter

        loadBoardingHouse(id)
        loadFacultiesForSpinner(id)
    }

    private fun loadBoardingHouse(id: Int) {
        lifecycleScope.launch {
            try {
                val bh = RetrofitClient.api.getBoardingHouse(id)
                boardingHouse = bh
                bindBoardingHouse(bh)

                map.controller.setZoom(15.0)
                map.controller.setCenter(GeoPoint(bh.lat, bh.lng))
                addBoardingHouseMarker(bh)
            } catch (e: Exception) {
                Log.e("KostFinder", "Failed to load boarding house", e)
                Toast.makeText(this@BoardingHouseDetailActivity, "Failed to load listing", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun bindBoardingHouse(bh: BoardingHouse) {
        findViewById<TextView>(R.id.detail_name).text = bh.name
        findViewById<TextView>(R.id.detail_address).text = bh.address ?: ""
        findViewById<TextView>(R.id.detail_price).text = "Rp ${bh.price_min}\u2013${bh.price_max}/mo"
        findViewById<TextView>(R.id.detail_meta).text =
            listOfNotNull(bh.room_type, bh.facilities?.joinToString(", ")).joinToString(" \u00b7 ")
        findViewById<TextView>(R.id.detail_description).text = bh.description ?: ""
        findViewById<TextView>(R.id.detail_contact).text = bh.contact?.let { "Contact: $it" } ?: ""
    }

    private fun loadFacultiesForSpinner(boardingHouseId: Int) {
        lifecycleScope.launch {
            try {
                faculties = RetrofitClient.api.getFaculties()
                val labels = listOf("Select your faculty\u2026") + faculties.map { it.name }
                val adapter = ArrayAdapter(this@BoardingHouseDetailActivity, android.R.layout.simple_spinner_item, labels)
                adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
                facultySpinner.adapter = adapter

                facultySpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                    override fun onItemSelected(parent: AdapterView<*>?, v: View?, position: Int, id: Long) {
                        if (position == 0) return
                        val faculty = faculties[position - 1]
                        fetchRoute(boardingHouseId, faculty.id, profiles[profileSpinner.selectedItemPosition])
                    }
                    override fun onNothingSelected(parent: AdapterView<*>?) {}
                }

                profileSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
                    override fun onItemSelected(parent: AdapterView<*>?, v: View?, position: Int, id: Long) {
                        if (facultySpinner.selectedItemPosition == 0) return
                        val faculty = faculties[facultySpinner.selectedItemPosition - 1]
                        fetchRoute(boardingHouseId, faculty.id, profiles[position])
                    }
                    override fun onNothingSelected(parent: AdapterView<*>?) {}
                }
            } catch (e: Exception) {
                Log.e("KostFinder", "Failed to load faculties", e)
            }
        }
    }

    private fun fetchRoute(boardingHouseId: Int, facultyId: Int, profile: String) {
        lifecycleScope.launch {
            try {
                routeSummary.visibility = View.VISIBLE
                routeSummary.text = "Calculating route\u2026"

                val route = RetrofitClient.api.getRoute(boardingHouseId, facultyId, profile)
                showRouteOnMap(route, facultyId)

                val distanceKm = "%.2f".format(route.distance_m / 1000)
                val minutes = (route.duration_s / 60).toInt()
                routeSummary.text = "$distanceKm km \u00b7 $minutes min by $profile \u00b7 road condition: ${route.overall_condition}"
            } catch (e: Exception) {
                Log.e("KostFinder", "Failed to fetch route", e)
                routeSummary.text = "Could not calculate route"
            }
        }
    }

    private fun showRouteOnMap(route: RouteResponse, facultyId: Int) {
        map.overlays.clear()
        boardingHouse?.let { addBoardingHouseMarker(it) }

        val allPoints = mutableListOf<GeoPoint>()
        boardingHouse?.let { allPoints.add(GeoPoint(it.lat, it.lng)) }

        faculties.find { it.id == facultyId }?.let { faculty ->
            val marker = Marker(map)
            marker.position = GeoPoint(faculty.lat, faculty.lng)
            marker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            marker.title = faculty.name
            map.overlays.add(marker)
            allPoints.add(marker.position)
        }

        val routePoints = route.geometry.coordinates.map { GeoPoint(it[1], it[0]) }
        val polyline = Polyline(map)
        polyline.setPoints(routePoints)
        polyline.outlinePaint.color = Color.parseColor("#2F5D50")
        polyline.outlinePaint.strokeWidth = 7f
        map.overlays.add(polyline)
        allPoints.addAll(routePoints)

        renderRoadConditionOverlay(route.road_condition_overlay)

        map.invalidate()
        if (allPoints.isNotEmpty()) {
            val box = BoundingBox.fromGeoPoints(allPoints)
            map.post { map.zoomToBoundingBox(box, true, 80) }
        }
    }

    // Mirrors the web app's MapView.jsx: road segments can be a Point
    // (single-spot issue), LineString, or MultiLineString (branch) - so
    // we branch on geometry type the same way here.
    private fun renderRoadConditionOverlay(overlay: List<RoadOverlaySegment>) {
        overlay.forEach { seg ->
            val color = when (seg.condition) {
                "poor" -> Color.parseColor("#C1483E")
                "fair" -> Color.parseColor("#D9A441")
                else -> Color.parseColor("#3C8F5C")
            }
            when (val type = seg.geometry.get("type")?.asString) {
                "Point" -> {
                    val coords = seg.geometry.getAsJsonArray("coordinates")
                    val marker = Marker(map)
                    marker.position = GeoPoint(coords[1].asDouble, coords[0].asDouble)
                    marker.title = seg.name ?: "Reported spot"
                    marker.snippet = "Condition: ${seg.condition}"
                    map.overlays.add(marker)
                }
                "LineString" -> {
                    val coords = seg.geometry.getAsJsonArray("coordinates")
                    val points = coords.map { pt -> pt.asJsonArray.let { GeoPoint(it[1].asDouble, it[0].asDouble) } }
                    val line = Polyline(map)
                    line.setPoints(points)
                    line.outlinePaint.color = color
                    line.outlinePaint.strokeWidth = 8f
                    map.overlays.add(line)
                }
                "MultiLineString" -> {
                    val lines = seg.geometry.getAsJsonArray("coordinates")
                    lines.forEach { lineEl ->
                        val points = lineEl.asJsonArray.map { pt -> pt.asJsonArray.let { GeoPoint(it[1].asDouble, it[0].asDouble) } }
                        val line = Polyline(map)
                        line.setPoints(points)
                        line.outlinePaint.color = color
                        line.outlinePaint.strokeWidth = 8f
                        map.overlays.add(line)
                    }
                }
                else -> Log.w("KostFinder", "Unhandled road segment geometry type: $type")
            }
        }
    }

    private fun addBoardingHouseMarker(bh: BoardingHouse) {
        val marker = Marker(map)
        marker.position = GeoPoint(bh.lat, bh.lng)
        marker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
        marker.title = bh.name
        map.overlays.add(marker)
    }

    private fun cartoVoyagerTileSource(): XYTileSource {
        return XYTileSource(
            "CartoVoyager",
            0, 20, 256, ".png?key=cb1_2iwa_1_e4fa6c20614118fac484d0eb",
            arrayOf(
                "https://a.basemaps.cartocdn.com/rastertiles/voyager/",
                "https://b.basemaps.cartocdn.com/rastertiles/voyager/",
                "https://c.basemaps.cartocdn.com/rastertiles/voyager/",
                "https://d.basemaps.cartocdn.com/rastertiles/voyager/"
            )
        )
    }

    override fun onResume() {
        super.onResume()
        map.onResume()
    }

    override fun onPause() {
        super.onPause()
        map.onPause()
    }
}