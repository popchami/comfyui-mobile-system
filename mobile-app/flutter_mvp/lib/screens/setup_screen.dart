import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/comfy_api_client.dart';
import 'local_profiles_screen.dart';
import 'remote_profiles_screen.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  static const _comfyUrlKey = 'comfyui_url';

  final TextEditingController _urlController = TextEditingController();
  String _status = 'Not connected';
  bool _checking = false;

  @override
  void initState() {
    super.initState();
    _restoreSavedUrl();
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  String get _url => _urlController.text.trim().replaceAll(RegExp(r'/+$'), '');

  String _friendlyError(Object error) {
    final message = error.toString().replaceFirst('ComfyApiException: ', '');
    if (message.contains('SocketException') || message.contains('Failed host lookup') || message.contains('Connection refused')) {
      return 'Connection failed. Check the ComfyUI URL and whether the pod/server is running.';
    }
    if (message.length > 220) {
      return '${message.substring(0, 220)}...';
    }
    return message;
  }

  Future<void> _restoreSavedUrl() async {
    final prefs = await SharedPreferences.getInstance();
    final savedUrl = prefs.getString(_comfyUrlKey);
    if (!mounted || savedUrl == null || savedUrl.isEmpty) return;
    _urlController.text = savedUrl;
    setState(() => _status = 'Saved ComfyUI URL restored');
  }

  Future<void> _saveUrl() async {
    if (_url.isEmpty) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_comfyUrlKey, _url);
  }

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
      setState(() => _status = 'Connected. Checking nodes...');
      final objectInfo = await client.getObjectInfo();
      setState(() => _status = 'Connected. Checking checkpoint models...');
      var checkpointCount = 0;
      try {
        final checkpoints = await client.getModels(folder: 'checkpoints');
        checkpointCount = checkpoints.length;
      } catch (_) {
        // /models can vary by ComfyUI version. Do not fail connection if only model listing fails.
      }
      await _saveUrl();
      _urlController.text = _url;
      setState(() {
        _status = 'Connected; ${objectInfo.length} node types found; $checkpointCount checkpoints; URL saved';
      });
    } catch (e) {
      setState(() => _status = 'Connection failed: ${_friendlyError(e)}');
    } finally {
      if (mounted) setState(() => _checking = false);
    }
  }

  Future<void> _openRemoteProfiles() async {
    if (_url.isEmpty) {
      setState(() => _status = 'ComfyUI URL is required');
      return;
    }
    await _saveUrl();
    if (!mounted) return;
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
