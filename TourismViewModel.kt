package com.smarttourism.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.smarttourism.model.*
import com.smarttourism.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

data class UiState(
    val isLoading: Boolean = false,
    val recommendations: List<Recommendation> = emptyList(),
    val modelInfo: ModelInfo? = null,
    val error: String? = null,
    val feedbackSent: Boolean = false
)

class TourismViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState

    var budgetMin = MutableStateFlow(1000)
    var budgetMax = MutableStateFlow(10000)
    var travelType = MutableStateFlow("nature")
    var sustainabilityPref = MutableStateFlow(7)

    fun getRecommendations() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                val prefs = UserPreferences(
                    budget_min = budgetMin.value,
                    budget_max = budgetMax.value,
                    travel_type = travelType.value,
                    sustainability_pref = sustainabilityPref.value,
                    user_id = "user_001"
                )
                val response = RetrofitClient.api.getRecommendations(prefs)
                if (response.isSuccessful) {
                    val body = response.body()!!
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        recommendations = body.recommendations,
                        modelInfo = body.model_info
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Server error: ${response.code()}"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Connection error: ${e.message}"
                )
            }
        }
    }

    fun sendFeedback(destinationId: Int, liked: Boolean) {
        viewModelScope.launch {
            try {
                val fb = FeedbackRequest(
                    user_id = "user_001",
                    destination_id = destinationId,
                    liked = liked,
                    budget_min = budgetMin.value,
                    budget_max = budgetMax.value,
                    travel_type = travelType.value,
                    sustainability_pref = sustainabilityPref.value
                )
                RetrofitClient.api.sendFeedback(fb)
            } catch (_: Exception) {}
        }
    }
}    fun sendFeedback(destinationId: Int, liked: Boolean) {
        viewModelScope.launch {
            try {
                val fb = FeedbackRequest(
                    user_id = "user_001",
                    destination_id = destinationId,
                    liked = liked,
                    budget_min = budgetMin.value,
                    budget_max = budgetMax.value,
                    travel_type = travelType.value,
                    sustainability_pref = sustainabilityPref.value
                )
                RetrofitClient.api.sendFeedback(fb)
            } catch (_: Exception) {}
        }
    }
}
