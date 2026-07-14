package com.smarttourism.network

import com.smarttourism.model.*
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ApiService {
    @POST("recommend")
    suspend fun getRecommendations(@Body prefs: UserPreferences): Response<RecommendationResponse>

    @POST("feedback")
    suspend fun sendFeedback(@Body feedback: FeedbackRequest): Response<FeedbackResponse>
}
