import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../models/recommendation.dart';

class RecommendationCard extends StatelessWidget {
  final Recommendation recommendation;

  const RecommendationCard({super.key, required this.recommendation});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isPost = recommendation.action.toLowerCase() == 'post';
    final actionColor = isPost ? theme.colorScheme.secondary : theme.colorScheme.error;

    return Card(
      margin: const EdgeInsets.all(20),
      child: Container(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            // 🚥 Header: Action & Confidence
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _buildBadge(recommendation.action.toUpperCase(), actionColor),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      "${recommendation.confidenceScore}%",
                      style: GoogleFonts.outfit(
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                        color: actionColor,
                      ),
                    ),
                    Text("CONFIDENCE", style: theme.textTheme.bodySmall),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 32),
            
            // 📌 Topic Direction (BIG & BOLD)
            Text(
              "📌 TOPIC DIRECTION",
              style: theme.textTheme.bodySmall?.copyWith(color: Colors.white38, letterSpacing: 1.5),
            ),
            const SizedBox(height: 8),
            Text(
              recommendation.topicDirection ?? recommendation.topic ?? "Analyzing...",
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.w900,
                color: Colors.white,
                height: 1.2,
              ),
            ).animate().fadeIn().slideX(begin: -0.1, end: 0),
            
            const SizedBox(height: 24),
            
            // 🧠 Why this works today (NARRATIVE)
            Text(
              "🧠 WHY THIS WORKS TODAY",
              style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.primary, letterSpacing: 1.5, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(
              recommendation.explanation,
              style: theme.textTheme.bodyLarge?.copyWith(height: 1.6, color: Colors.white.withOpacity(0.9)),
            ),
            
            const SizedBox(height: 24),
            const Divider(color: Colors.white10),
            const SizedBox(height: 24),

            // ⚠️ How to avoid being generic
            if (recommendation.avoidAdvice != null) ...[
              Text(
                "⚠️ HOW TO AVOID BEING GENERIC",
                style: theme.textTheme.bodySmall?.copyWith(color: Colors.orangeAccent, letterSpacing: 1.2, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                recommendation.avoidAdvice!,
                style: theme.textTheme.bodyMedium?.copyWith(fontStyle: FontStyle.italic),
              ),
              const SizedBox(height: 24),
            ],

            // 🔍 Suggested Angles
            if (recommendation.suggestedAngles.isNotEmpty) ...[
              Text(
                "🔍 SUGGESTED ANGLES",
                style: theme.textTheme.bodySmall?.copyWith(color: theme.colorScheme.secondary, letterSpacing: 1.2, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              ...recommendation.suggestedAngles.map((angle) => Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("• ", style: TextStyle(color: theme.colorScheme.secondary, fontSize: 20)),
                    Expanded(
                      child: Text(
                        angle,
                        style: GoogleFonts.inter(fontWeight: FontWeight.w500, height: 1.4),
                      ),
                    ),
                  ],
                ),
              )).toList(),
            ],
          ],
        ),
      ),
    ).animate().fadeIn(duration: 600.ms).scale(begin: const Offset(0.95, 0.95));
  }

  Widget _buildBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.5)),
      ),
      child: Text(
        text,
        style: GoogleFonts.outfit(
          color: color,
          fontWeight: FontWeight.bold,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}
