import 'package:flutter/material.dart';

import '../services/comfy_api_client.dart';

class RemoteProfilesScreen extends StatefulWidget {
  const RemoteProfilesScreen({super.key, required this.comfyUrl});

  final String comfyUrl;

  @override
  State<RemoteProfilesScreen> createState() => _RemoteProfilesScreenState();
}

class _RemoteProfilesScreenState extends State<RemoteProfilesScreen> {
  bool _loading = false;
  String _status = 'Not loaded';
  List<dynamic> _profiles = const [];

  Future<void> _loadProfiles() async {
    setState(() {
      _loading = true;
      _status = 'Loading profiles...';
    });

    try {
      final client = ComfyApiClient(baseUrl: widget.comfyUrl);
      final profiles = await client.getRemoteProfiles();
      setState(() {
        _profiles = profiles;
        _status = 'Loaded ${profiles.length} profiles';
      });
    } catch (e) {
      setState(() => _status = 'Load failed: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _profileName(dynamic value) {
    if (value is Map<String, dynamic>) {
      return (value['name'] ?? value['id'] ?? value['file'] ?? 'profile').toString();
    }
    return value.toString();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Remote Profiles')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('ComfyUI: ${widget.comfyUrl}'),
            const SizedBox(height: 12),
            Text(_status),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _loading ? null : _loadProfiles,
              child: Text(_loading ? 'Loading...' : 'Load remote profiles'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: _profiles.length,
                itemBuilder: (context, index) {
                  final profile = _profiles[index];
                  return ListTile(
                    title: Text(_profileName(profile)),
                    subtitle: Text(profile.toString()),
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
