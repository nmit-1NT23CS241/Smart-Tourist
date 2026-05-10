package com.smarttourism.model

data class UserPreferences(
    val budget_min: Int,
    val budget_max: Int,
    val travel_type: String,
    val sustainability_pref: Int,
    val user_id: String
)

data class FeedbackRequest(
    val user_id: String,
    val destination_id: Int,
    val liked: Boolean,
    val budget_min: Int,
    val budget_max: Int,
    val travel_type: String,
    val sustainability_pref: Int
)

data class Recommendation(
    val id: Int,
    val name: String,
    val type: String,
    val estimated_cost: Int,
    val sustainability: Double,
    val crowd_level: String,
    val score: Double,
    val match_reason: String,
    val state: String,
    val description: String,
    val tags: List<String>,
)

data class ModelInfo(
    val interactions: Int,
    val exploration_rate: Double,
    val learning_mode: String
)

data class RecommendationResponse(
    val recommendations: List<Recommendation>,
    val model_info: ModelInfo
)

data class FeedbackResponse(
    val status: String,
    val reward_applied: Double,
    val buffer_size: Int
)