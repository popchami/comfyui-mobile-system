import 'package:flutter/material.dart';

class RemoteProfilesScreen extends StatelessWidget {
  const RemoteProfilesScreen({super.key, required this.comfyUrl});

  final String comfyUrl;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Remote Profiles')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('ComfyUI: $comfyUrl'),
            const SizedBox(height: 12),
            const Text('This screen will fetch /mobile_analyzer/profiles.'),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () {},
              child: const Text('Load remote profiles'),
            ),
            const SizedBox(height: 12),
            const Expanded(
              child: Center(
                child: Text('Remote profile list placeholder'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
