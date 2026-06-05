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
    val state: String,
    val district: String?,
    val region: String?,
    val type: String,
    val tags: List<String>,
    val trip_types: List<String>?,
    val description: String,
    val estimated_cost: Int,
    val budget_range: List<Int>?,
    val ideal_days: Double?,
    val best_seasons: List<String>?,
    val activities: List<String>?,
    val ideal_for: List<String>?,
    val food_scene: String?,
    val local_cuisine: List<String>?,
    val accommodation_types: List<String>?,
    val sustainability: Double,
    val crowd_level: String,
    val popularity: Int?,
    val safety_rating: Int?,
    val permits_required: Boolean?,
    val score: Double,
    val match_reason: String
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
    val destination: String?
)