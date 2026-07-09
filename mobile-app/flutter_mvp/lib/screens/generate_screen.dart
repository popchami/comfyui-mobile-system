import 'package:flutter/material.dart';

import '../models/local_profile.dart';

class GenerateScreen extends StatelessWidget {
  const GenerateScreen({super.key, required this.profile});

  final LocalProfile profile;

  @override
  Widget build(BuildContext context) {
    final fields = profile.appProfile.simpleFields;

    return Scaffold(
      appBar: AppBar(title: Text(profile.name)),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: fields.length,
        itemBuilder: (context, index) {
          final field = fields[index];
          return Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text('${field.label} / ${field.type}'),
          );
        },
      ),
    );
  }
}
