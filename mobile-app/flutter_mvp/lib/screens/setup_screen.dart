import 'package:flutter/material.dart';

import '../services/comfy_api_client.dart';
import 'local_profiles_screen.dart';
import 'remote_profiles_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final TextEditingController _urlController = TextEditingController();
  String _status = 'Not connected';
  bool _checking = false;

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  String get _url => _urlController.text.trim();

  Future<void> _checkConnection() async {
    if (_url.isEmpty) {
      setState(() => _status = 'ComfyUI URL is required');
      return;
    }

    setState(() {
      _checking = true;
      _status = 'Checking connection...';
    });

    try {
      final client = ComfyApiClient(baseUrl: _url);
      await client.getSystemStats();
      setState(() => _status = 'Connected');
    } catch (e) {
      setState(() => _status = 'Connection failed: $e');
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  void _openRemoteProfiles() {
    if (_url.isEmpty) {
      setState(() => _status = 'ComfyUI URL is required');
      return;
    }
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => RemoteProfilesScreen(comfyUrl: _url)),
    );
  }

  void _openLocalProfiles() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const LocalProfilesScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Comfy Mobile Setup')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'ComfyUI URL',
                hintText: 'https://xxxxx-8188.proxy.runpod.net',
              ),
            ),
            const SizedBox(height: 12),
            Text(_status),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _checking ? null : _checkConnection,
              child: Text(_checking ? 'Checking...' : 'Check connection'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _openRemoteProfiles,
              child: const Text('Remote profiles'),
            ),
            OutlinedButton(
              onPressed: _openLocalProfiles,
              child: const Text('Local profiles'),
            ),
          ],
        ),
      ),
    );
  }
}
