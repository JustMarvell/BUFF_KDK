package com.whnyh.kdk

import android.os.Bundle
import android.preference.PreferenceManager
import androidx.appcompat.app.AppCompatActivity
import org.osmdroid.config.Configuration
import org.osmdroid.tileprovider.tilesource.XYTileSource
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.CustomZoomButtonsController
import org.osmdroid.views.MapView

class MainActivity : AppCompatActivity() {

    companion object {
        // Universitas Negeri Manado (UNIMA)
        // default center used in the Django admin and web app.
        private const val UNIMA_LAT = 1.26667
        private const val UNIMA_LNG = 124.88306
        private const val DEFAULT_ZOOM = 16.0
    }

    private lateinit var map: MapView

    override fun onCreate(savedInstanceState: Bundle?) {
        // osmdroid must load its configuration before any MapView is created.
        // android.preference.PreferenceManager is deprecated but still fully
        // functional - the deprecation warning here is expected and harmless.
        Configuration.getInstance().load(
            applicationContext,
            PreferenceManager.getDefaultSharedPreferences(applicationContext)
        )
        // OSM's tile usage policy requires a proper User-Agent identifying
        // your app - without this, tile requests can get blocked, same as
        // the 403 you hit on the web app.
        Configuration.getInstance().userAgentValue = packageName

        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        map = findViewById(R.id.map)
        // Use CARTO's free tiles instead of OSM's own tile server - same
        // fix we applied on the web app, for the same reason (OSM's
        // volunteer-run tile server actively blocks unapproved apps).
        map.setTileSource(cartoVoyagerTileSource())
        map.setMultiTouchControls(true)
        map.zoomController.setVisibility(CustomZoomButtonsController.Visibility.SHOW_AND_FADEOUT)

        map.controller.setZoom(DEFAULT_ZOOM)
        map.controller.setCenter(GeoPoint(UNIMA_LAT, UNIMA_LNG))
    }

    private fun cartoVoyagerTileSource(): XYTileSource {
        return XYTileSource(
            "CartoVoyager",
            0, 20, 256, ".png",
            arrayOf(
                "https://a.basemaps.cartocdn.com/rastertiles/voyager/",
                "https://b.basemaps.cartocdn.com/rastertiles/voyager/",
                "https://c.basemaps.cartocdn.com/rastertiles/voyager/",
                "https://d.basemaps.cartocdn.com/rastertiles/voyager/"
            )
        )
    }

    // osmdroid needs explicit lifecycle hooks to manage tile caching/battery correctly
    override fun onResume() {
        super.onResume()
        map.onResume()
    }

    override fun onPause() {
        super.onPause()
        map.onPause()
    }
}