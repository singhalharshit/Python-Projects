import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../core/app_theme.dart';

class CreatorCard extends StatefulWidget {
  final Map<String, dynamic> creator;
  final bool isSelected;
  final VoidCallback onTap;
  final VoidCallback onReject;
  final bool showConfidence;

  const CreatorCard({
    super.key,
    required this.creator,
    required this.isSelected,
    required this.onTap,
    required this.onReject,
    this.showConfidence = true,
  });

  @override
  State<CreatorCard> createState() => _CreatorCardState();
}

class _CreatorCardState extends State<CreatorCard> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  bool _isHovered = false;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: AppTheme.animationMedium,
      vsync: this,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final confidenceScore = widget.creator['confidence_score'] as double? ?? 75.0;
    final matchReason = widget.creator['match_reason'] as String? ?? 'Recommended for you';
    final tags = List<String>.from(widget.creator['tags'] ?? []);

    return GestureDetector(
      onTap: () {
        _controller.forward().then((_) => _controller.reverse());
        widget.onTap();
      },
      child: MouseRegion(
        onEnter: (_) => setState(() => _isHovered = true),
        onExit: (_) => setState(() => _isHovered = false),
        child: AnimatedContainer(
          duration: AppTheme.animationFast,
          transform: Matrix4.identity()
            ..scale(_isHovered ? 1.02 : 1.0),
          decoration: BoxDecoration(
            gradient: widget.isSelected
                ? LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      AppTheme.primaryColor.withOpacity(0.2),
                      AppTheme.secondaryColor.withOpacity(0.2),
                    ],
                  )
                : null,
            color: widget.isSelected ? null : AppTheme.cardColor,
            borderRadius: BorderRadius.circular(AppTheme.borderRadiusLarge),
            border: Border.all(
              color: widget.isSelected
                  ? AppTheme.primaryColor
                  : Colors.white.withOpacity(0.1),
              width: widget.isSelected ? 2 : 1,
            ),
            boxShadow: [
              if (_isHovered || widget.isSelected) AppTheme.cardShadow,
            ],
          ),
          child: Stack(
            children: [
              // Main Content
              Padding(
                padding: const EdgeInsets.all(AppTheme.spacingM),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Avatar with loading shimmer
                    _buildAvatar(),
                    const SizedBox(height: AppTheme.spacingM),
                    
                    // Name
                    Text(
                      widget.creator['name'],
                      textAlign: TextAlign.center,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: GoogleFonts.outfit(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: Colors.white,
                      ),
                    ),
                    
                    const SizedBox(height: AppTheme.spacingXS),
                    
                    // Subscriber count
                    Text(
                      widget.creator['subs'],
                      style: GoogleFonts.inter(
                        color: Colors.white38,
                        fontSize: 12,
                      ),
                    ),
                    
                    const SizedBox(height: AppTheme.spacingS),
                    
                    // Tags
                    if (tags.isNotEmpty) _buildTags(tags.take(2).toList()),
                    
                    const SizedBox(height: AppTheme.spacingS),
                    
                    // Confidence indicator
                    if (widget.showConfidence) _buildConfidenceIndicator(confidenceScore),
                  ],
                ),
              ),
              
              // Selection checkmark
              if (widget.isSelected)
                Positioned(
                  top: 12,
                  right: 12,
                  child: Container(
                    padding: const EdgeInsets.all(4),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryColor,
                      shape: BoxShape.circle,
                      boxShadow: [AppTheme.subtleShadow],
                    ),
                    child: const Icon(
                      Icons.check,
                      color: Colors.white,
                      size: 16,
                    ),
                  ),
                ).animate().scale(duration: AppTheme.animationFast),
              
              // Reject button
              Positioned(
                bottom: 8,
                right: 8,
                child: IconButton(
                  icon: Icon(
                    Icons.close,
                    size: 16,
                    color: Colors.white.withOpacity(0.3),
                  ),
                  onPressed: widget.onReject,
                  tooltip: 'Not interested',
                ),
              ),
              
              // Match reason tooltip
              if (matchReason.isNotEmpty)
                Positioned(
                  top: 8,
                  left: 8,
                  child: Tooltip(
                    message: matchReason,
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.secondaryColor.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppTheme.secondaryColor.withOpacity(0.3),
                        ),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(
                            Icons.lightbulb_outline,
                            size: 12,
                            color: AppTheme.secondaryColor,
                          ),
                          const SizedBox(width: 4),
                          Text(
                            'Match',
                            style: GoogleFonts.inter(
                              fontSize: 10,
                              color: AppTheme.secondaryColor,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAvatar() {
    final avatarUrl = widget.creator['avatar'] as String?;
    
    return Container(
      width: 80,
      height: 80,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(
          color: widget.isSelected
              ? AppTheme.primaryColor
              : Colors.white.withOpacity(0.1),
          width: 3,
        ),
        boxShadow: [
          if (widget.isSelected) AppTheme.subtleShadow,
        ],
      ),
      child: ClipOval(
        child: avatarUrl != null && avatarUrl.startsWith('http')
            ? CachedNetworkImage(
                imageUrl: avatarUrl,
                fit: BoxFit.cover,
                placeholder: (context, url) => Container(
                  color: AppTheme.surfaceColor,
                  child: const Center(
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                ),
                errorWidget: (context, url, error) => _buildFallbackAvatar(),
              )
            : _buildFallbackAvatar(),
      ),
    );
  }

  Widget _buildFallbackAvatar() {
    final name = widget.creator['name'] as String;
    final initials = name.split(' ').take(2).map((e) => e[0]).join().toUpperCase();
    
    return Container(
      color: AppTheme.primaryColor.withOpacity(0.3),
      child: Center(
        child: Text(
          initials,
          style: GoogleFonts.outfit(
            fontSize: 28,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }

  Widget _buildTags(List<String> tags) {
    return Wrap(
      spacing: 4,
      runSpacing: 4,
      alignment: WrapAlignment.center,
      children: tags.map((tag) {
        return Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: AppTheme.primaryColor.withOpacity(0.2),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: AppTheme.primaryColor.withOpacity(0.3),
            ),
          ),
          child: Text(
            tag,
            style: GoogleFonts.inter(
              fontSize: 10,
              color: AppTheme.primaryColor.withOpacity(0.9),
              fontWeight: FontWeight.w600,
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildConfidenceIndicator(double score) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.trending_up,
          size: 12,
          color: _getConfidenceColor(score),
        ),
        const SizedBox(width: 4),
        Text(
          '${score.toInt()}% match',
          style: GoogleFonts.inter(
            fontSize: 10,
            color: _getConfidenceColor(score),
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  Color _getConfidenceColor(double score) {
    if (score >= 80) return Colors.green;
    if (score >= 60) return AppTheme.secondaryColor;
    return Colors.orange;
  }
}
