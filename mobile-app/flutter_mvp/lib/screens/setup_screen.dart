import 'package:flutter/material.dart';

class SetupScreen extends StatefulWidget {
  const SetupScreen({super.key});

  @override
  State<SetupScreen> createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final TextEditingController _urlController = TextEditingController();
  String _status = 'Not connected';

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  void _markPending() {
    setState(() {
      _status = 'Connection check will be wired to ComfyApiClient.';
    });
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
              onPressed: _markPending,
              child: const Text('Check connection'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _markPending,
              child: const Text('Remote profiles'),
            ),
            OutlinedButton(
              onPressed: _markPending,
              child: const Text('Local profiles'),
            ),
          ],
        ),
      ),
    );
  }
}
