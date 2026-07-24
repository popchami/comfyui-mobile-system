// UI wiring for browser-local stored profiles.
// This file keeps index.html smaller while testing the storage flow.

function getStorageApi() {
  return window.ComfyMobileProfileStorage;
}

function createStoredProfilesSection() {
  const main = document.querySelector('main');
  if (!main || document.getElementById('storedProfilesSection')) return;

  const section = document.createElement('section');
  section.id = 'storedProfilesSection';
  section.innerHTML = `
    <h2>保存済みProfile</h2>
    <div class="status" id="storedProfileStatus">保存済みProfileなし</div>
    <label>保存済みProfile</label>
    <select id="storedProfileSelect"></select>
    <button type="button" onclick="saveCurrentProfileToLocal()">現在のProfileを保存</button>
    <button type="button" class="secondary" onclick="loadSelectedStoredProfile()">選択Profileを読み込み</button>
    <button type="button" class="secondary" onclick="deleteSelectedStoredProfile()">選択Profileを削除</button>
    <button type="button" class="secondary" onclick="clearAllStoredProfiles()">保存済みProfileを全削除</button>
  `;

  const profileSection = document.querySelector('main section:nth-of-type(2)');
  if (profileSection && profileSection.nextSibling) {
    main.insertBefore(section, profileSection.nextSibling);
  } else {
    main.appendChild(section);
  }

  refreshStoredProfileList();
}

function refreshStoredProfileList() {
  const api = getStorageApi();
  const select = document.getElementById('storedProfileSelect');
  const status = document.getElementById('storedProfileStatus');
  if (!api || !select || !status) return;

  const profiles = api.loadStoredProfiles();
  select.innerHTML = '';

  profiles.forEach(profile => {
    const opt = document.createElement('option');
    opt.value = profile.id;
    opt.textContent = `${profile.name || profile.id} / ${profile.profileVersion || ''}`;
    select.appendChild(opt);
  });

  status.textContent = profiles.length > 0
    ? `保存済みProfile: ${profiles.length}件`
    : '保存済みProfileなし';
}

function readCurrentProfileFromTextareas() {
  const appProfileText = document.getElementById('appProfileText')?.value || '';
  const workflowText = document.getElementById('workflowText')?.value || '';
  if (!appProfileText || !workflowText) throw new Error('app_profile.json と workflow.json が必要です');
  return {
    appProfile: JSON.parse(appProfileText),
    workflow: JSON.parse(workflowText),
  };
}

function saveCurrentProfileToLocal() {
  try {
    const api = getStorageApi();
    if (!api) throw new Error('storage helper が読み込まれていません');
    const { appProfile, workflow } = readCurrentProfileFromTextareas();
    const saved = api.upsertStoredProfile(appProfile, workflow);
    refreshStoredProfileList();
    if (window.setStatus) window.setStatus('Profile保存OK: ' + saved.name);
  } catch (e) {
    if (window.setStatus) window.setStatus('Profile保存失敗: ' + e.message);
  }
}

function loadSelectedStoredProfile() {
  try {
    const api = getStorageApi();
    if (!api) throw new Error('storage helper が読み込まれていません');
    const profileId = document.getElementById('storedProfileSelect')?.value;
    if (!profileId) throw new Error('保存済みProfileが選択されていません');
    const profile = api.loadStoredProfiles().find(p => p.id === profileId);
    if (!profile) throw new Error('保存済みProfileが見つかりません');

    document.getElementById('appProfileText').value = JSON.stringify(profile.appProfile, null, 2);
    document.getElementById('workflowText').value = JSON.stringify(profile.workflow, null, 2);

    if (window.loadManualProfile) window.loadManualProfile();
    if (window.setStatus) window.setStatus('保存済みProfile読み込みOK: ' + profile.name);
  } catch (e) {
    if (window.setStatus) window.setStatus('保存済みProfile読み込み失敗: ' + e.message);
  }
}

function deleteSelectedStoredProfile() {
  try {
    const api = getStorageApi();
    if (!api) throw new Error('storage helper が読み込まれていません');
    const profileId = document.getElementById('storedProfileSelect')?.value;
    if (!profileId) throw new Error('保存済みProfileが選択されていません');
    api.deleteStoredProfile(profileId);
    refreshStoredProfileList();
    if (window.setStatus) window.setStatus('保存済みProfile削除OK');
  } catch (e) {
    if (window.setStatus) window.setStatus('保存済みProfile削除失敗: ' + e.message);
  }
}

function clearAllStoredProfiles() {
  try {
    const api = getStorageApi();
    if (!api) throw new Error('storage helper が読み込まれていません');
    api.clearStoredProfiles();
    refreshStoredProfileList();
    if (window.setStatus) window.setStatus('保存済みProfile全削除OK');
  } catch (e) {
    if (window.setStatus) window.setStatus('保存済みProfile全削除失敗: ' + e.message);
  }
}

window.createStoredProfilesSection = createStoredProfilesSection;
window.refreshStoredProfileList = refreshStoredProfileList;
window.saveCurrentProfileToLocal = saveCurrentProfileToLocal;
window.loadSelectedStoredProfile = loadSelectedStoredProfile;
window.deleteSelectedStoredProfile = deleteSelectedStoredProfile;
window.clearAllStoredProfiles = clearAllStoredProfiles;

document.addEventListener('DOMContentLoaded', createStoredProfilesSection);
