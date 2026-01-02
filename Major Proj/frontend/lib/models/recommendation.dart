class Recommendation {
  final String status;
  final String action;
  final String niche;
  final String? topic;
  final int confidenceScore;
  final String confidenceLevel;
  final String explanation;
  final String reasoning;
  final List<String> sources;
  final int sourceCount;
  final List<AlternativeTopic> alternatives;
  final TimingSuggestion? timing;
  final Map<String, dynamic> metadata;
  final String generatedAt;

  final List<String> suggestedAngles;
  final String? topicDirection;
  final String? avoidAdvice;

  Recommendation({
    required this.status,
    required this.action,
    required this.niche,
    this.topic,
    required this.confidenceScore,
    required this.confidenceLevel,
    required this.explanation,
    required this.reasoning,
    required this.sources,
    required this.sourceCount,
    required this.alternatives,
    this.timing,
    required this.metadata,
    required this.generatedAt,
    required this.suggestedAngles,
    this.topicDirection,
    this.avoidAdvice,
  });

  factory Recommendation.fromJson(Map<String, dynamic> json) {
    return Recommendation(
      status: json['status'] ?? 'unknown',
      action: json['action'] ?? 'wait',
      niche: json['niche'] ?? '',
      topic: json['topic'],
      confidenceScore: json['confidence_score'] ?? 0,
      confidenceLevel: json['confidence_level'] ?? 'low',
      explanation: json['explanation'] ?? '',
      reasoning: json['reasoning'] ?? '',
      sources: List<String>.from(json['sources'] ?? []),
      sourceCount: json['source_count'] ?? 0,
      alternatives: (json['alternatives'] as List? ?? [])
          .map((e) => AlternativeTopic.fromJson(e))
          .toList(),
      timing: json['timing'] != null
          ? TimingSuggestion.fromJson(json['timing'])
          : null,
      metadata: json['metadata'] ?? {},
      generatedAt: json['generated_at'] ?? '',
      suggestedAngles: List<String>.from(json['suggested_angles'] ?? []),
      topicDirection: json['topic_direction'],
      avoidAdvice: json['avoid_advice'],
    );
  }
}

class AlternativeTopic {
  final String topic;
  final double confidenceScore;
  final List<String> sources;

  AlternativeTopic({
    required this.topic,
    required this.confidenceScore,
    required this.sources,
  });

  factory AlternativeTopic.fromJson(Map<String, dynamic> json) {
    return AlternativeTopic(
      topic: json['topic'] ?? '',
      confidenceScore: (json['confidence_score'] ?? 0).toDouble(),
      sources: List<String>.from(json['sources'] ?? []),
    );
  }
}

class TimingSuggestion {
  final String urgency;
  final String suggestedWindow;
  final String reason;

  TimingSuggestion({
    required this.urgency,
    required this.suggestedWindow,
    required this.reason,
  });

  factory TimingSuggestion.fromJson(Map<String, dynamic> json) {
    return TimingSuggestion(
      urgency: json['urgency'] ?? 'low',
      suggestedWindow: json['suggested_window'] ?? '',
      reason: json['reason'] ?? '',
    );
  }
}
