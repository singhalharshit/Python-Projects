import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../core/api_service.dart';
import '../../widgets/creator_card.dart';
import '../daily_deck.dart';

class CompetitorSelectScreen extends StatefulWidget {
  final String username;
  final String niche;
  final List<Map<String, dynamic>> suggestions;

  const CompetitorSelectScreen({
    super.key,
    required this.username,
    required this.niche,
    required this.suggestions,
  });

  @override
  State<CompetitorSelectScreen> createState() => _CompetitorSelectScreenState();
}

class _CompetitorSelectScreenState extends State<CompetitorSelectScreen> {
  final List<Map<String, dynamic>> _allSuggestions = [];
  final Set<String> _selectedIds = {};
  final Set<String> _rejectedIds = {};
  final ApiService _apiService = ApiService();
  bool _isSaving = false;
  bool _isFetchingMore = false;

  @override
  void initState() {
    super.initState();
    _allSuggestions.addAll(widget.suggestions);
  }

  Future<void> _handleSelection(String id, bool selected) async {
    setState(() {
      if (selected) {
        _selectedIds.add(id);
      } else {
        _selectedIds.remove(id);
      }
    });

    if (selected) {
      // Track selection feedback
      final creator = _allSuggestions.firstWhere((c) => c['id'] == id);
      final tags = List<String>.from(creator['tags'] ?? []);
      
      try {
        await _apiService.trackFeedback(
          creatorId: id,
          action: 'selected',
          creatorTags: tags,
        );
      } catch (e) {
        debugPrint("Error tracking selection: $e");
      }
      
      // Trigger "More Like This"
      _fetchMore(id);
    }
  }

  Future<void> _fetchMore(String sourceId) async {
    if (_isFetchingMore) return;
    
    setState(() => _isFetchingMore = true);
    try {
      final more = await _apiService.fetchSimilarCreators([sourceId]);
      setState(() {
        for (var item in more) {
          // Only add if not already in list and not rejected
          if (!_allSuggestions.any((existing) => existing['id'] == item['id']) &&
              !_rejectedIds.contains(item['id'])) {
            _allSuggestions.add(item);
          }
        }
      });
    } catch (e) {
      debugPrint("Error fetching more: $e");
    } finally {
      setState(() => _isFetchingMore = false);
    }
  }

  void _rejectCreator(String id) async {
    // Track rejection feedback
    final creator = _allSuggestions.firstWhere((c) => c['id'] == id);
    final tags = List<String>.from(creator['tags'] ?? []);
    
    try {
      await _apiService.trackFeedback(
        creatorId: id,
        action: 'rejected',
        creatorTags: tags,
      );
    } catch (e) {
      debugPrint("Error tracking rejection: $e");
    }
    
    setState(() {
      _selectedIds.remove(id);
      _rejectedIds.add(id);
      _allSuggestions.removeWhere((c) => c['id'] == id);
    });
  }

  Future<void> _onStartAnalysis() async {
    if (_selectedIds.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select at least one creator to track.')),
      );
      return;
    }

    setState(() => _isSaving = true);
    try {
      await _apiService.saveCompetitors(_selectedIds.toList());
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const DailyDeckScreen()),
          (route) => false,
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) setState(() => _isSaving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: const Color(0xFF0F0F1A),
      appBar: AppBar(
        title: Text("DISCOVER RIVALS", style: GoogleFonts.outfit(fontWeight: FontWeight.w900, letterSpacing: 1.2)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            child: Text(
              "Select creators that inspire or compete with you. We'll suggest more as you pick.",
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(color: Colors.white54, fontSize: 14),
            ),
          ),
          if (_isFetchingMore)
            const LinearProgressIndicator(minHeight: 2, backgroundColor: Colors.transparent),
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(16),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 0.75,
                crossAxisSpacing: 12,
                mainAxisSpacing: 12,
              ),
              itemCount: _allSuggestions.length,
              itemBuilder: (context, index) {
                final creator = _allSuggestions[index];
                return _buildCreatorTile(creator);
              },
            ),
          ),
          _buildActiveFooter(),
        ],
      ),
    );
  }

  Widget _buildCreatorTile(Map<String, dynamic> creator) {
    final isSelected = _selectedIds.contains(creator['id']);
    
    return GestureDetector(
      onTap: () => _handleSelection(creator['id'], !isSelected),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        decoration: BoxDecoration(
          color: isSelected ? Colors.white.withOpacity(0.1) : Colors.white.withOpacity(0.03),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected ? Theme.of(context).colorScheme.primary : Colors.white10,
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Stack(
          children: [
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  _buildAvatar(creator['avatar'], creator['name']),
                  const SizedBox(height: 8),
                  Text(
                    creator['name'],
                    textAlign: TextAlign.center,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 13),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    creator['subs'],
                    style: GoogleFonts.inter(color: Colors.white38, fontSize: 11),
                  ),
                ],
              ),
            ),
            if (isSelected)
              Positioned(
                top: 8,
                right: 8,
                child: Icon(Icons.check_circle, color: Theme.of(context).colorScheme.primary, size: 20),
              ),
            Positioned(
              bottom: 4,
              right: 4,
              child: IconButton(
                icon: const Icon(Icons.close, size: 14, color: Colors.white24),
                onPressed: () => _rejectCreator(creator['id']),
                padding: EdgeInsets.zero,
                constraints: const BoxConstraints(),
              ),
            ),
          ],
        ),
      ),
    ).animate().fadeIn(delay: 50.ms * _allSuggestions.indexOf(creator)).scale(begin: const Offset(0.9, 0.9));
  }

  Widget _buildAvatar(String? url, String name) {
    return Container(
      width: 50,
      height: 50,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white10, width: 2),
        image: (url != null && url.startsWith('http'))
            ? DecorationImage(image: NetworkImage(url), fit: BoxFit.cover)
            : null,
      ),
      child: (url == null || !url.startsWith('http'))
          ? Center(child: Text(name[0], style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)))
          : null,
    );
  }

  Widget _buildActiveFooter() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF161625),
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 20)],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "${_selectedIds.length} SELECTED",
                style: GoogleFonts.outfit(fontWeight: FontWeight.w900, color: Colors.white54),
              ),
              if (_selectedIds.isNotEmpty)
                TextButton(
                  onPressed: () => setState(() => _selectedIds.clear()),
                  child: const Text("CLEAR ALL"),
                ),
            ],
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            height: 60,
            child: ElevatedButton(
              onPressed: _isSaving ? null : _onStartAnalysis,
              style: ElevatedButton.styleFrom(
                backgroundColor: Theme.of(context).primaryColor,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                elevation: 0,
              ),
              child: _isSaving
                  ? const CircularProgressIndicator(color: Colors.white)
                  : Text(
                      "LOCK IN MY NETWORK",
                      style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 16, letterSpacing: 1.2),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}
