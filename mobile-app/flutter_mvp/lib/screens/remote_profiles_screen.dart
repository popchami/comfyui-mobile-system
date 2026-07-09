import 'package:flutter/material.dart';

import '../models/local_profile.dart';
import '../models/remote_profile.dart';
import '../services/comfy_api_client.dart';
import '../services/local_profile_store.dart';
import '../services/profile_zip_service.dart';

class RemoteProfilesScreen extends StatefulWidget {
  const RemoteProfilesScreen({super.key, required this.comfyUrl});

  final String comfyUrl;

  @override
  State<RemoteProfilesScreen> createState() => _RemoteProfilesScreenState();
}

class _RemoteProfilesScreenState extends State<RemoteProfilesScreen> {
  bool _loading = false;
  bool _saving = false;
  String _status = 'Not loaded';
  List<RemoteProfile> _profiles = const [];

  ComfyApiClient get _client => ComfyApiClient(baseUrl: widget.comfyUrl);

  Future<void> _loadProfiles() async {
    setState(() {
      _loading = true;
      _status = 'Loading profiles...';
    });

    try {
      final profiles = await _client.getRemoteProfiles();
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

  Future<void> _downloadAndSave(RemoteProfile profile) async {
    if (profile.id.isEmpty) {
      setState(() => _status = 'Profile id missing');
      return;
    }

    setState(() {
      _saving = true;
      _status = 'Downloading ${profile.id}...';
    });

    try {
      final zipBytes = await _client.downloadProfileZip(profile.id);
      final bundle = ProfileZipService.parseProfileZip(zipBytes);
      final local = LocalProfile.fromBundle(
        appProfileJson: bundle.rawAppProfileJson,
        workflowJson: bundle.rawWorkflowJson,
        comfyUrl: widget.comfyUrl,
      );
      await LocalProfileStore().upsertProfile(local);
      setState(() => _status = 'Saved local profile: ${local.name}');
    } catch (e) {
      setState(() => _status = 'Download/save failed: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  String _profileSubtitle(RemoteProfile profile) {
    final parts = <String>[];
    if (profile.file.isNotEmpty) parts.add(profile.file);
    if (profile.sizeBytes > 0) parts.add('${profile.sizeBytes} bytes');
    if (profile.modifiedAt.isNotEmpty) parts.add(profile.modifiedAt);
    return parts.isEmpty ? profile.id : parts.join(' / ');
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
              onPressed: _loading || _saving ? null : _loadProfiles,
              child: Text(_loading ? 'Loading...' : 'Load remote profiles'),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: ListView.builder(
                itemCount: _profiles.length,
                itemBuilder: (context, index) {
                  final profile = _profiles[index];
                  return ListTile(
                    title: Text(profile.name),
                    subtitle: Text(_profileSubtitle(profile)),
                    trailing: FilledButton(
                      onPressed: _saving ? null : () => _downloadAndSave(profile),
                      child: const Text('Save'),
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
