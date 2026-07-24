import 'package:flutter/material.dart';

import 'screens/setup_screen.dart';

void main() {
  runApp(const ComfyMobileMvpApp());
}

class ComfyMobileMvpApp extends StatelessWidget {
  const ComfyMobileMvpApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Comfy Mobile MVP',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange),
        useMaterial3: true,
      ),
      home: const SetupScreen(),
    );
  }
}
