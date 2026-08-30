package com.whnyh.app.data

import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query

interface ApiService {

    @GET("api/faculties/")
    suspend fun getFaculties(): List<Faculty>

    @GET("api/boarding-houses/")
    suspend fun getBoardingHouses(
        @Query("faculty_id") facultyId: Int? = null,
        @Query("min_price") minPrice: Int? = null,
        @Query("max_price") maxPrice: Int? = null,
        @Query("room_type") roomType: String? = null
    ): List<BoardingHouse>

    @GET("api/boarding-houses/recommended/")
    suspend fun getRecommended(
        @Query("faculty_id") facultyId: Int,
        @Query("limit") limit: Int = 10
    ): List<BoardingHouse>

    @GET("api/boarding-houses/{id}/")
    suspend fun getBoardingHouse(@Path("id") id: Int): BoardingHouse

    @GET("api/road-segments/")
    suspend fun getRoadSegments(): RoadSegmentCollection

    @GET("api/route/")
    suspend fun getRoute(
        @Query("boarding_house_id") boardingHouseId: Int,
        @Query("faculty_id") facultyId: Int,
        @Query("profile") profile: String = "driving"
    ): RouteResponse
}