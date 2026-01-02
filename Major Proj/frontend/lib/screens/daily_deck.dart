import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/api_service.dart';
import '../models/recommendation.dart';
import '../widgets/recommendation_card.dart';

class DailyDeckScreen extends StatefulWidget {
  const DailyDeckScreen({super.key});

  @override
  State<DailyDeckScreen> createState() => _DailyDeckScreenState();
}

class _DailyDeckScreenState extends State<DailyDeckScreen> {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  Recommendation? _recommendation;
  String? _error;

  // Hardcoded for V1 MVP
  final String _niche = "tech_creators"; 
  final List<String> _keywords = ["software engineering", "coding", "AI"];

  @override
  void initState() {
    super.initState();
    _fetchRecommendation();
  }

  Future<void> _fetchRecommendation() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      // For MVP, we use 'generate' endpoint to ensure we see fresh data/AI results
      // In production, we would use 'getDailyRecommendation'
      final result = await _apiService.generateRecommendation(_niche, _keywords);
      
      setState(() {
        _recommendation = result;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          "DAILY DECK", 
          style: GoogleFonts.outfit(
            fontWeight: FontWeight.w900,
            letterSpacing: 2.0,
          ),
        ),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            onPressed: () {}, // TODO: History screen
          ),
        ],
      ),
      body: Center(
        child: _buildContent(),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _fetchRecommendation,
        label: Text(_isLoading ? "ANALYZING..." : "NEW INTELLIGENCE"),
        icon: _isLoading 
            ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
            : const Icon(Icons.auto_awesome),
        backgroundColor: Theme.of(context).primaryColor,
      ),
    );
  }

  Widget _buildContent() {
    if (_isLoading) {
      return Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const CircularProgressIndicator(),
          const SizedBox(height: 24),
          Text(
            "Analyzing market signals...",
            style: GoogleFonts.inter(color: Colors.white54),
          ),
          const SizedBox(height: 8),
          Text(
            "Checking competitors...", // Show users we are doing the "Smart" thing
            style: GoogleFonts.inter(color: Colors.white30, fontSize: 12),
          ),
        ],
      );
    }

    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 48),
            const SizedBox(height: 16),
            Text(
              "Intelligence Network Offline",
              style: GoogleFonts.outfit(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            Text(
              _error!,
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(color: Colors.white54),
            ),
            const SizedBox(height: 24),
            OutlinedButton(
              onPressed: _fetchRecommendation,
              child: const Text("RETRY CONNECTION"),
            ),
          ],
        ),
      );
    }

    if (_recommendation == null) {
      return const Text("No Data");
    }

    return SingleChildScrollView(
      child: Column(
        children: [
          RecommendationCard(recommendation: _recommendation!),
          // Space for FAB
          const SizedBox(height: 80),
        ],
      ),
    );
  }
}
