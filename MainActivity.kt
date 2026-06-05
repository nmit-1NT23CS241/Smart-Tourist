package com.smarttourism

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.smarttourism.ui.PreferencesScreen
import com.smarttourism.ui.RecommendationsScreen
import com.smarttourism.ui.TourismViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                val navController = rememberNavController()
                val viewModel: TourismViewModel = viewModel()

                NavHost(navController = navController, startDestination = "preferences") {
                    composable("preferences") {
                        PreferencesScreen(
                            viewModel = viewModel,
                            onNavigateToRecommendations = {
                                navController.navigate("recommendations")
                            }
                        )
                    }
                    composable("recommendations") {
                        RecommendationsScreen(
                            viewModel = viewModel,
                            onBack = { navController.popBackStack() }
                        )
                    }
                }
            }
        }
    }
}
