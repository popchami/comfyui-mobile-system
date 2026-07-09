import 'package:shared_preferences/shared_preferences.dart';

import '../models/local_profile.dart';

class LocalProfileStore {
  static const _key = 'comfy_mobile_local_profiles_v1';

  Future<List<LocalProfile>> loadProfiles() async {
    final prefs = await SharedPreferences.getInstance();
    final values = prefs.getStringList(_key) ?? const <String>[];
    final profiles = <LocalProfile>[];

    for (final value in values) {
      try {
        profiles.add(LocalProfile.decode(value));
      } catch (_) {
        // Skip corrupted stored profile.
      }
    }

    return profiles;
  }

  Future<void> saveProfiles(List<LocalProfile> profiles) async {
    final prefs = await SharedPreferences.getInstance();
    final values = profiles.map((profile) => profile.encode()).toList();
    await prefs.setStringList(_key, values);
  }

  Future<void> upsertProfile(LocalProfile profile) async {
    final profiles = await loadProfiles();
    final index = profiles.indexWhere((item) => item.id == profile.id);

    if (index >= 0) {
      profiles[index] = profile;
    } else {
      profiles.insert(0, profile);
    }

    await saveProfiles(profiles);
  }

  Future<void> deleteProfile(String profileId) async {
    final profiles = await loadProfiles();
    profiles.removeWhere((profile) => profile.id == profileId);
    await saveProfiles(profiles);
  }

  Future<void> clearProfiles() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
