package com.whnyh.app.ui

import android.os.Bundle
import android.util.Log
import android.view.View
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import com.whnyh.kdk.R
import com.whnyh.app.data.BoardingHouse
import com.whnyh.app.data.Faculty
import com.whnyh.app.data.RetrofitClient
import kotlinx.coroutines.launch
import org.osmdroid.tileprovider.tilesource.XYTileSource
import org.osmdroid.util.BoundingBox
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.CustomZoomButtonsController
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

class MapFragment : Fragment(R.layout.fragment_map) {

    companion object {
        private const val UNIMA_LAT = 1.26667
        private const val UNIMA_LNG = 124.88306
        private const val DEFAULT_ZOOM = 16.0
    }

    private lateinit var map: MapView

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        map = view.findViewById(R.id.map)
        map.setTileSource(cartoVoyagerTileSource())
        map.setMultiTouchControls(true)
        map.zoomController.setVisibility(CustomZoomButtonsController.Visibility.SHOW_AND_FADEOUT)
        map.controller.setZoom(DEFAULT_ZOOM)
        map.controller.setCenter(GeoPoint(UNIMA_LAT, UNIMA_LNG))

        loadData()
    }

    private fun loadData() {
        // viewLifecycleOwner (not just `this`) matters here - it's tied
        // to the fragment's *view* lifecycle, so an in-flight request
        // gets cancelled correctly if the user switches tabs quickly.
        viewLifecycleOwner.lifecycleScope.launch {
            try {
                val faculties = RetrofitClient.api.getFaculties()
                val boardingHouses = RetrofitClient.api.getBoardingHouses()

                addFacultyMarkers(faculties)
                addBoardingHouseMarkers(boardingHouses)

                val allPoints = faculties.map { GeoPoint(it.lat, it.lng) } +
                        boardingHouses.map { GeoPoint(it.lat, it.lng) }
                if (allPoints.isNotEmpty()) {
                    val boundingBox = BoundingBox.fromGeoPoints(allPoints)
                    map.post {
                        map.zoomToBoundingBox(boundingBox, true, 100)
                    }
                }
            } catch (e: Exception) {
                Log.e("kdk", "API call failed", e)
            }
        }
    }

    private fun addFacultyMarkers(faculties: List<Faculty>) {
        faculties.forEach { faculty ->
            val marker = Marker(map)
            marker.position = GeoPoint(faculty.lat, faculty.lng)
            marker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            marker.title = faculty.name
            marker.snippet = faculty.address ?: ""
            map.overlays.add(marker)
        }
    }

    private fun addBoardingHouseMarkers(boardingHouses: List<BoardingHouse>) {
        boardingHouses.forEach { bh ->
            val marker = Marker(map)
            marker.position = GeoPoint(bh.lat, bh.lng)
            marker.setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
            marker.title = bh.name
            marker.snippet = "Rp ${bh.price_min}\u2013${bh.price_max}"
            map.overlays.add(marker)
        }
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