import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:uuid/uuid.dart';
import '../models/recommendation.dart';

class ApiService {
  // Generate a unique user ID for tracking preferences
  static final String userId = const Uuid().v4();
  
  // Use 10.0.2.2 for Android Emulator, localhost for iOS/Web/Windows
  String get baseUrl {
    if (kIsWeb) return 'http://127.0.0.1:8000/api';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000/api';
    return 'http://127.0.0.1:8000/api';
  }

  Future<Recommendation> generateRecommendation(
      String niche, List<String> keywords) async {
    final url = Uri.parse('$baseUrl/recommendations/generate');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'niche': niche,
          'keywords': keywords,
        }),
      );

      if (response.statusCode == 200) {
        return Recommendation.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Failed to generate recommendation: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Recommendation> getDailyRecommendation(String niche) async {
    final url = Uri.parse('$baseUrl/recommendations/daily/$niche');
    
    try {
      final response = await http.get(url);

      if (response.statusCode == 200) {
        return Recommendation.fromJson(jsonDecode(response.body));
      } else {
        throw Exception('Failed to get daily recommendation: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> analyzeProfile(String username) async {
    final url = Uri.parse('$baseUrl/onboarding/analyze');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': username,
          'user_id': userId,  // Include user ID for personalization
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to analyze profile: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> fetchSimilarCreators(List<String> selectedIds) async {
    final url = Uri.parse('$baseUrl/onboarding/similar');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'selected_ids': selectedIds,
          'user_id': userId,  // Include user ID for personalization
        }),
      );

      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(jsonDecode(response.body));
      } else {
        throw Exception('Failed to fetch similar: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<void> trackFeedback({
    required String creatorId,
    required String action,
    required List<String> creatorTags,
    String? reason,
  }) async {
    final url = Uri.parse('$baseUrl/onboarding/feedback');
    
    try {
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'user_id': userId,
          'creator_id': creatorId,
          'action': action,
          'creator_tags': creatorTags,
          'reason': reason,
        }),
      );

      if (response.statusCode != 200) {
        debugPrint('Failed to track feedback: ${response.body}');
      }
    } catch (e) {
      debugPrint('Error tracking feedback: $e');
    }
  }

  Future<void> saveCompetitors(List<String> competitorIds) async {
    // Track all selected competitors as feedback
    for (final id in competitorIds) {
      // In a real app, you'd fetch the creator data to get tags
      await trackFeedback(
        creatorId: id,
        action: 'selected',
        creatorTags: [],  // Would be populated with actual tags
      );
    }
    
    await Future.delayed(const Duration(seconds: 1));
    debugPrint("Saved ${competitorIds.length} competitors");
  }
}
