import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/api_service.dart';
import 'competitor_select.dart';

class InstaLoginScreen extends StatefulWidget {
  const InstaLoginScreen({super.key});

  @override
  State<InstaLoginScreen> createState() => _InstaLoginScreenState();
}

class _InstaLoginScreenState extends State<InstaLoginScreen> {
  final TextEditingController _controller = TextEditingController();
  final ApiService _apiService = ApiService();
  bool _isLoading = false;

  Future<void> _onContinue() async {
    if (_controller.text.isEmpty) return;

    setState(() => _isLoading = true);

    try {
      final analysis = await _apiService.analyzeProfile(_controller.text);
      
      // Handle Niche parsing (can be null, Map, or String)
      String nicheLabel = 'General';
      if (analysis['niche'] != null) {
        if (analysis['niche'] is Map) {
          nicheLabel = analysis['niche']['label'] ?? 'General';
        } else if (analysis['niche'] is String) {
          nicheLabel = analysis['niche'];
        }
      }

      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => CompetitorSelectScreen(
              username: analysis['user_id'] ?? _controller.text,
              niche: nicheLabel,
              suggestions: List<Map<String, dynamic>>.from(analysis['competitors'] ?? []),
            ),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        padding: const EdgeInsets.symmetric(horizontal: 40),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).scaffoldBackgroundColor,
              const Color(0xFF1A1A2E),
            ],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.camera_alt_outlined, size: 80, color: Colors.white70),
            const SizedBox(height: 40),
            Text(
              "CONNECT PROFILE",
              style: GoogleFonts.outfit(
                fontSize: 28,
                fontWeight: FontWeight.w900,
                letterSpacing: 2.0,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              "Enter your Instagram handle to start personalized analysis",
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(color: Colors.white54, fontSize: 16),
            ),
            const SizedBox(height: 60),
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                prefixText: "@ ",
                hintText: "username",
                filled: true,
                fillColor: Colors.white.withOpacity(0.05),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(16),
                  borderSide: BorderSide.none,
                ),
              ),
              style: GoogleFonts.outfit(fontSize: 18),
            ),
            const SizedBox(height: 40),
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _onContinue,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Theme.of(context).primaryColor,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : Text(
                        "ANALYZE MY PROFILE",
                        style: GoogleFonts.outfit(
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          letterSpacing: 1.2,
                        ),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
