package com.smarttourism.ui

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material.icons.filled.ThumbUp
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.smarttourism.model.Recommendation
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecommendationsScreen(viewModel: TourismViewModel, onBack: () -> Unit) {
    val uiState by viewModel.uiState.collectAsState()
    var avoidCrowds by remember { mutableStateOf(false) }

    val filteredRecommendations = remember(uiState.recommendations, avoidCrowds) {
        if (avoidCrowds) {
            uiState.recommendations.filter { it.crowd_level != "High" }
        } else {
            uiState.recommendations
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("SafarAI Recommendations", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    // Avoid Crowds filter chip
                    if (uiState.recommendations.isNotEmpty()) {
                        FilterChip(
                            selected = avoidCrowds,
                            onClick = { avoidCrowds = !avoidCrowds },
                            label = {
                                Text(
                                    "Avoid Crowds",
                                    fontSize = 12.sp,
                                    fontWeight = if (avoidCrowds) FontWeight.Bold else FontWeight.Normal
                                )
                            },
                            modifier = Modifier.padding(end = 8.dp),
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = Color(0xFF2E7D6E),
                                selectedLabelColor = Color.White,
                                containerColor = Color(0xFFEEEEEE),
                                labelColor = Color(0xFF555555)
                            )
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF2E7D6E),
                    titleContentColor = Color.White,
                    navigationIconContentColor = Color.White,
                    actionIconContentColor = Color.White
                )
            )
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFFF5F5F0))
                .padding(padding)
        ) {
            when {
                uiState.isLoading -> {
                    Column(
                        modifier = Modifier.align(Alignment.Center),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        CircularProgressIndicator(color = Color(0xFF2E7D6E))
                        Spacer(modifier = Modifier.height(12.dp))
                        Text("RL model finding best destinations...", color = Color(0xFF6B6B80))
                    }
                }
                uiState.error != null -> {
                    Column(
                        modifier = Modifier.align(Alignment.Center).padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text("⚠️ ${uiState.error}", color = Color(0xFFB00020), textAlign = TextAlign.Center)
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = { viewModel.getRecommendations() },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D6E))
                        ) { Text("Retry") }
                    }
                }
                else -> {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        uiState.modelInfo?.let { info ->
                            item {
                                ModelInfoBanner(info.interactions, info.learning_mode, info.exploration_rate)
                            }
                        }
                        if (filteredRecommendations.isEmpty()) {
                            item {
                                Box(
                                    modifier = Modifier.fillMaxWidth().padding(40.dp),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Text(
                                        "No destinations match your crowd preference.\nTry turning off the filter.",
                                        textAlign = TextAlign.Center,
                                        color = Color(0xFF6B6B80),
                                        fontSize = 14.sp
                                    )
                                }
                            }
                        } else {
                            items(filteredRecommendations) { rec ->
                                RecommendationCard(
                                    recommendation = rec,
                                    onLike = { viewModel.sendFeedback(rec.id, true) },
                                    onDislike = { viewModel.sendFeedback(rec.id, false) }
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ModelInfoBanner(interactions: Int, learningMode: String, explorationRate: Double) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9))
    ) {
        Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("🤖", fontSize = 20.sp)
            Spacer(modifier = Modifier.width(10.dp))
            Column {
                Text(
                    "RL Model — ${learningMode.replaceFirstChar { it.uppercase() }}",
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    color = Color(0xFF1B5E20)
                )
                Text(
                    "$interactions interactions • exploration ${(explorationRate * 100).roundToInt()}%",
                    fontSize = 11.sp,
                    color = Color(0xFF388E3C)
                )
            }
        }
    }
}

@Composable
fun RecommendationCard(recommendation: Recommendation, onLike: () -> Unit, onDislike: () -> Unit) {
    val typeEmoji = mapOf(
        "nature" to "🌿", "heritage" to "🏛️", "beach" to "🏖️",
        "culture" to "🎭", "adventure" to "🧗"
    )
    val crowdColor = when (recommendation.crowd_level) {
        "Low" -> Color(0xFF2E7D32)
        "Medium" -> Color(0xFFF57F17)
        else -> Color(0xFFC62828)
    }
    var feedbackGiven by remember { mutableStateOf<Boolean?>(null) }
    var expanded by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        elevation = CardDefaults.cardElevation(2.dp)
    ) {
        Column(modifier = Modifier.padding(18.dp)) {

            // Header row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(typeEmoji[recommendation.type] ?: "📍", fontSize = 18.sp)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            recommendation.name,
                            fontWeight = FontWeight.Bold,
                            fontSize = 16.sp,
                            color = Color(0xFF1A1A2E)
                        )
                    }
                    Text(
                        "📍 ${recommendation.state}",
                        fontSize = 12.sp,
                        color = Color(0xFF6B6B80),
                        modifier = Modifier.padding(start = 24.dp, top = 2.dp)
                    )
                }
                Box(
                    modifier = Modifier
                        .background(Color(0xFF2E7D6E), RoundedCornerShape(8.dp))
                        .padding(horizontal = 10.dp, vertical = 6.dp)
                ) {
                    Text(
                        "${(recommendation.score * 100).roundToInt()}%",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
            HorizontalDivider(color = Color(0xFFF0F0F0))
            Spacer(modifier = Modifier.height(12.dp))

            // Stats row
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                StatItem("💰", "₹${"%,d".format(recommendation.estimated_cost)}", "Cost")
                StatItem("🌱", "${recommendation.sustainability}/10", "Eco")
                StatItem("👥", recommendation.crowd_level, "Crowd", crowdColor)
                recommendation.weather?.let {
                    StatItem("🌡️", "${it.temp_c}°C", "Now")
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "✓ ${recommendation.match_reason}",
                fontSize = 12.sp,
                color = Color(0xFF2E7D6E),
                fontWeight = FontWeight.Medium
            )

            // Expand toggle
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { expanded = !expanded }
                    .padding(vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    if (expanded) "Show less" else "Show more details",
                    fontSize = 12.sp,
                    color = Color(0xFF2E7D6E),
                    fontWeight = FontWeight.Medium
                )
                Icon(
                    if (expanded) Icons.Default.KeyboardArrowUp else Icons.Default.KeyboardArrowDown,
                    contentDescription = null,
                    tint = Color(0xFF2E7D6E),
                    modifier = Modifier.size(16.dp)
                )
            }

            // Expanded content
            AnimatedVisibility(visible = expanded) {
                Column {
                    HorizontalDivider(color = Color(0xFFF0F0F0))
                    Spacer(modifier = Modifier.height(10.dp))

                    Text("About", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color(0xFF1A1A2E))
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(recommendation.description, fontSize = 13.sp, color = Color(0xFF555555), lineHeight = 20.sp)

                    // Weather section
                    recommendation.weather?.let { w ->
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("Current Weather", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color(0xFF1A1A2E))
                        Spacer(modifier = Modifier.height(6.dp))
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(10.dp),
                            colors = CardDefaults.cardColors(
                                containerColor = if (w.is_suitable) Color(0xFFE8F5E9) else Color(0xFFFFEBEE)
                            )
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(
                                        w.description,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 13.sp,
                                        color = if (w.is_suitable) Color(0xFF2E7D6E) else Color(0xFFB00020)
                                    )
                                    Text(
                                        if (w.is_suitable) "Good to visit" else "Conditions poor",
                                        fontSize = 11.sp,
                                        color = if (w.is_suitable) Color(0xFF2E7D6E) else Color(0xFFB00020),
                                        fontWeight = FontWeight.Medium
                                    )
                                }
                                Spacer(modifier = Modifier.height(8.dp))
                                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                                    Text("🌡️ ${w.temp_c}°C", fontSize = 12.sp, color = Color(0xFF555555))
                                    Text("Feels ${w.feels_like}°C", fontSize = 12.sp, color = Color(0xFF555555))
                                    Text("💧 ${w.humidity}%", fontSize = 12.sp, color = Color(0xFF555555))
                                    Text("💨 ${w.wind_kmh} km/h", fontSize = 12.sp, color = Color(0xFF555555))
                                }
                            }
                        }
                    }

                    // Best seasons
                    recommendation.best_seasons?.takeIf { it.isNotEmpty() }?.let { seasons ->
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("Best Seasons", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color(0xFF1A1A2E))
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("🗓️ ${seasons.joinToString(", ")}", fontSize = 12.sp, color = Color(0xFF555555))
                    }

                    // Activities
                    recommendation.activities?.takeIf { it.isNotEmpty() }?.let { activities ->
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("Activities", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color(0xFF1A1A2E))
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("🎯 ${activities.joinToString(", ")}", fontSize = 12.sp, color = Color(0xFF555555))
                    }

                    // Local cuisine
                    recommendation.local_cuisine?.takeIf { it.isNotEmpty() }?.let { cuisine ->
                        Spacer(modifier = Modifier.height(10.dp))
                        Text("Local Cuisine", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color(0xFF1A1A2E))
                        Spacer(modifier = Modifier.height(4.dp))
                        Text("🍽️ ${cuisine.joinToString(", ")}", fontSize = 12.sp, color = Color(0xFF555555))
                    }

                    // Ideal days
                    recommendation.ideal_days?.let { days ->
                        Spacer(modifier = Modifier.height(10.dp))
                        Text(
                            "📅 Ideal stay: ${days.toInt()} days",
                            fontSize = 12.sp,
                            color = Color(0xFF555555),
                            fontWeight = FontWeight.Medium
                        )
                    }

                    // Tags
                    Spacer(modifier = Modifier.height(10.dp))
                    Text("Travel tags", fontWeight = FontWeight.SemiBold, fontSize = 13.sp, color = Color(0xFF1A1A2E))
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        recommendation.tags.forEach { tag ->
                            Box(
                                modifier = Modifier
                                    .background(Color(0xFFE8F5E9), RoundedCornerShape(20.dp))
                                    .padding(horizontal = 10.dp, vertical = 4.dp)
                            ) {
                                Text(
                                    tag.replaceFirstChar { it.uppercase() },
                                    fontSize = 11.sp,
                                    color = Color(0xFF2E7D6E),
                                    fontWeight = FontWeight.Medium
                                )
                            }
                        }
                    }
                    Spacer(modifier = Modifier.height(10.dp))
                }
            }

            // Feedback buttons
            if (feedbackGiven == null) {
                Spacer(modifier = Modifier.height(8.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(
                        onClick = { feedbackGiven = true; onLike() },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF2E7D6E)),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Icon(Icons.Filled.ThumbUp, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("Love it", fontSize = 13.sp)
                    }
                    OutlinedButton(
                        onClick = { feedbackGiven = false; onDislike() },
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF9E9E9E)),
                        shape = RoundedCornerShape(10.dp)
                    ) {
                        Text("Not for me", fontSize = 13.sp)
                    }
                }
            } else {
                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    if (feedbackGiven == true) "Thanks! Model updated." else "Noted. We'll improve.",
                    fontSize = 13.sp,
                    color = Color(0xFF2E7D6E),
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}

@Composable
fun StatItem(emoji: String, value: String, label: String, valueColor: Color = Color(0xFF1A1A2E)) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(emoji, fontSize = 16.sp)
        Text(value, fontWeight = FontWeight.Bold, fontSize = 13.sp, color = valueColor)
        Text(label, fontSize = 10.sp, color = Color(0xFF9E9E9E))
    }
}
