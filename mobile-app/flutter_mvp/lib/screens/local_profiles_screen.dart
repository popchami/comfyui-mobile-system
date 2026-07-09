import 'package:flutter/material.dart';

import '../models/local_profile.dart';
import '../services/local_profile_store.dart';
import 'generate_screen.dart';

class LocalProfilesScreen extends StatefulWidget {
  const LocalProfilesScreen({super.key});

  @override
  State<LocalProfilesScreen> createState() => _LocalProfilesScreenState();
}

class _LocalProfilesScreenState extends State<LocalProfilesScreen> {
  bool _loading = false;
  String _status = 'Not loaded';
  List<LocalProfile> _profiles = const [];

  Future<void> _loadProfiles() async {
    setState(() {
      _loading = true;
      _status = 'Loading local profiles...';
    });

    try {
      final profiles = await LocalProfileStore().loadProfiles();
      setState(() {
        _profiles = profiles;
        _status = 'Loaded ${profiles.length} local profiles';
      });
    } catch (e) {
      setState(() => _status = 'Load failed: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _deleteProfile(LocalProfile profile) async {
    await LocalProfileStore().deleteProfile(profile.id);
    await _loadProfiles();
  }

  void _openProfile(LocalProfile profile) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => GenerateScreen(profile: profile)),
    );
  }

  @override
  void initState() {
    super.initState();
    _loadProfiles();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Local Profiles')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(_status),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _loading ? null : _loadProfiles,
              child: Text(_loading ? 'Loading...' : 'Reload'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: _profiles.length,
                itemBuilder: (context, index) {
                  final profile = _profiles[index];
                  return ListTile(
                    title: Text(profile.name),
                    subtitle: Text(profile.profileVersion),
                    onTap: () => _openProfile(profile),
                    trailing: IconButton(
                      icon: const Icon(Icons.delete_outline),
                      onPressed: () => _deleteProfile(profile),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
