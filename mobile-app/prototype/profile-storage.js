// Local profile storage helper for the HTML prototype.
// This is intentionally simple and browser-only.

const PROFILE_STORAGE_KEY = 'comfy_mobile_profiles_v1';

function loadStoredProfiles() {
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
    if (!raw) return [];
    const value = JSON.parse(raw);
    return Array.isArray(value) ? value : [];
  } catch (e) {
    console.warn('Failed to load stored profiles', e);
    return [];
  }
}

function saveStoredProfiles(profiles) {
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profiles));
}

function makeStoredProfile(appProfile, workflow) {
  const profileId = appProfile.profile_id || ('profile_' + Date.now());
  return {
    id: profileId,
    name: appProfile.profile_name || profileId,
    profileVersion: appProfile.profile_version || '0.0.0',
    workflowId: appProfile.workflow_id || '',
    savedAt: new Date().toISOString(),
    appProfile,
    workflow,
  };
}

function upsertStoredProfile(appProfile, workflow) {
  const profiles = loadStoredProfiles();
  const next = makeStoredProfile(appProfile, workflow);
  const index = profiles.findIndex(p => p.id === next.id);
  if (index >= 0) {
    profiles[index] = next;
  } else {
    profiles.unshift(next);
  }
  saveStoredProfiles(profiles);
  return next;
}

function deleteStoredProfile(profileId) {
  const profiles = loadStoredProfiles().filter(p => p.id !== profileId);
  saveStoredProfiles(profiles);
  return profiles;
}

function clearStoredProfiles() {
  localStorage.removeItem(PROFILE_STORAGE_KEY);
}

window.ComfyMobileProfileStorage = {
  loadStoredProfiles,
  saveStoredProfiles,
  makeStoredProfile,
  upsertStoredProfile,
  deleteStoredProfile,
  clearStoredProfiles,
};
