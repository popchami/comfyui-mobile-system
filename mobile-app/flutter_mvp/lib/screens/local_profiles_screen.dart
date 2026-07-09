import 'package:flutter/material.dart';

class LocalProfilesScreen extends StatelessWidget {
  const LocalProfilesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Local Profiles')),
      body: const Padding(
        padding: EdgeInsets.all(16),
        child: Center(
          child: Text('Local profile list placeholder'),
        ),
      ),
    );
  }
}
