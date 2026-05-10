package com.smarttourism.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun PreferencesScreen(
    viewModel: TourismViewModel,
    onNavigateToRecommendations: () -> Unit
) {
    val budgetMin by viewModel.budgetMin.collectAsState()
    val budgetMax by viewModel.budgetMax.collectAsState()
    val travelType by viewModel.travelType.collectAsState()
    val sustainabilityPref by viewModel.sustainabilityPref.collectAsState()

    val travelTypes = listOf("nature", "heritage", "beach", "culture")
    val travelEmojis = mapOf("nature" to "🌿", "heritage" to "🏛️", "beach" to "🏖️", "culture" to "🎭")

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F0))
            .verticalScroll(rememberScrollState())
            .padding(20.dp)
    ) {
        Spacer(modifier = Modifier.height(40.dp))

        Text("SafarAI", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = Color(0xFF1A1A2E))
        Text("Tell us your travel style", fontSize = 16.sp, color = Color(0xFF6B6B80), modifier = Modifier.padding(top = 4.dp, bottom = 32.dp))

        // Budget Range Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(2.dp)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("Budget Range", fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                Text("Enter your min and max budget for the trip", fontSize = 12.sp, color = Color(0xFF9E9E9E), modifier = Modifier.padding(top = 2.dp, bottom = 16.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Min Budget
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Min (₹)", fontSize = 12.sp, color = Color(0xFF6B6B80), fontWeight = FontWeight.Medium)
                        Spacer(modifier = Modifier.height(6.dp))
                        OutlinedTextField(
                            value = if (budgetMin == 0) "" else budgetMin.toString(),
                            onValueChange = {
                                val num = it.filter { c -> c.isDigit() }
                                viewModel.budgetMin.value = if (num.isEmpty()) 0 else num.toIntOrNull() ?: 0
                            },
                            placeholder = { Text("e.g. 1000") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            singleLine = true,
                            shape = RoundedCornerShape(12.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = Color(0xFF2E7D6E),
                                unfocusedBorderColor = Color(0xFFE0E0E0)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    // Max Budget
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Max (₹)", fontSize = 12.sp, color = Color(0xFF6B6B80), fontWeight = FontWeight.Medium)
                        Spacer(modifier = Modifier.height(6.dp))
                        OutlinedTextField(
                            value = if (budgetMax == 0) "" else budgetMax.toString(),
                            onValueChange = {
                                val num = it.filter { c -> c.isDigit() }
                                viewModel.budgetMax.value = if (num.isEmpty()) 0 else num.toIntOrNull() ?: 0
                            },
                            placeholder = { Text("e.g. 10000") },
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            singleLine = true,
                            shape = RoundedCornerShape(12.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = Color(0xFF2E7D6E),
                                unfocusedBorderColor = Color(0xFFE0E0E0)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                }

                // Show range summary
                if (budgetMin > 0 && budgetMax > 0) {
                    Spacer(modifier = Modifier.height(10.dp))
                    Text(
                        "₹${"%,d".format(budgetMin)} – ₹${"%,d".format(budgetMax)}",
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF2E7D6E)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Travel Type Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(2.dp)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text("Travel style", fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                Spacer(modifier = Modifier.height(12.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    travelTypes.forEach { type ->
                        val isSelected = travelType == type
                        Box(
                            modifier = Modifier
                                .weight(1f)
                                .background(
                                    if (isSelected) Color(0xFF2E7D6E) else Color(0xFFF0F0F0),
                                    RoundedCornerShape(12.dp)
                                )
                                .clickable { viewModel.travelType.value = type }
                                .padding(vertical = 12.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                Text(travelEmojis[type] ?: "", fontSize = 20.sp)
                                Text(
                                    type.replaceFirstChar { it.uppercase() },
                                    fontSize = 11.sp,
                                    color = if (isSelected) Color.White else Color(0xFF555555),
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Sustainability Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(2.dp)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Eco-consciousness", fontWeight = FontWeight.SemiBold, fontSize = 15.sp)
                    Text("$sustainabilityPref / 10", fontWeight = FontWeight.Bold, color = Color(0xFF2E7D6E), fontSize = 15.sp)
                }
                Spacer(modifier = Modifier.height(12.dp))
                Slider(
                    value = sustainabilityPref.toFloat(),
                    onValueChange = { viewModel.sustainabilityPref.value = it.toInt() },
                    valueRange = 1f..10f,
                    steps = 8,
                    colors = SliderDefaults.colors(
                        thumbColor = Color(0xFF2E7D6E),
                        activeTrackColor = Color(0xFF2E7D6E)
                    )
                )
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        Button(
            onClick = {
                viewModel.getRecommendations()
                onNavigateToRecommendations()
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(16.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D6E))
        ) {
            Text("Find Destinations ✈️", fontSize = 17.sp, fontWeight = FontWeight.Bold)
        }
    }
}