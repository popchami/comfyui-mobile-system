#!/usr/bin/env python3
"""RunPod上で起動中のPodと概算料金(USD/JPY)を表示する。"""

import os
import sys

import requests
from dotenv import load_dotenv

RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"
FX_API_URL = "https://api.frankfurter.app/latest?from=USD&to=JPY"

# RunPod GraphQLスキーマは公開情報を基にしているが、この環境では未検証。
# フィールド名エラーが出た場合はRunPodダッシュボードのAPIスキーマで要確認。
POD_QUERY = """
query Pods {
  myself {
    pods {
      id
      name
      desiredStatus
      costPerHr
      runtime {
        uptimeInSeconds
      }
      machine {
        gpuDisplayName
      }
    }
  }
}
"""


def load_api_key() -> str:
    load_dotenv()
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        raise RuntimeError(
            "RUNPOD_API_KEY が .env から読み込めませんでした。.env の設定を確認してください。"
        )
    return api_key


def fetch_pods(api_key: str) -> list[dict]:
    try:
        response = requests.post(
            f"{RUNPOD_GRAPHQL_URL}?api_key={api_key}",
            json={"query": POD_QUERY},
            timeout=15,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"RunPod APIへの接続に失敗しました: {e}")

    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(f"RunPod APIがエラーを返しました: {payload['errors']}")

    return payload["data"]["myself"]["pods"]


def fetch_usd_jpy_rate() -> float | None:
    try:
        response = requests.get(FX_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()["rates"]["JPY"]
    except (requests.RequestException, KeyError, ValueError):
        return None


def format_elapsed(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{hours}時間{minutes}分"


def calc_usd_cost(cost_per_hr: float, uptime_seconds: int) -> float:
    return cost_per_hr * (uptime_seconds / 3600)


def print_pod(pod: dict, jpy_rate: float | None) -> None:
    name = pod.get("name", "unknown")
    gpu = pod.get("machine", {}).get("gpuDisplayName", "unknown")
    cost_per_hr = pod.get("costPerHr") or 0.0
    uptime_seconds = pod.get("runtime", {}).get("uptimeInSeconds", 0) or 0

    usd_cost = calc_usd_cost(cost_per_hr, uptime_seconds)

    print(f"■ {name}")
    print(f"  GPU: {gpu}")
    print("  状態: RUNNING")
    print(f"  経過時間: {format_elapsed(uptime_seconds)}")
    print(f"  概算料金(USD): ${usd_cost:.2f}")
    if jpy_rate is not None:
        print(f"  概算料金(JPY): ¥{usd_cost * jpy_rate:,.0f}")
    else:
        print("  概算料金(JPY): レート取得失敗、USD建てのみ表示")
    print()


def main() -> int:
    try:
        api_key = load_api_key()
    except RuntimeError as e:
        print(f"[エラー] {e}")
        return 1

    try:
        pods = fetch_pods(api_key)
    except RuntimeError as e:
        print(f"[エラー] {e}")
        return 1

    running_pods = [p for p in pods if p.get("desiredStatus") == "RUNNING"]
    if not running_pods:
        print("現在起動中のPodはありません")
        return 0

    jpy_rate = fetch_usd_jpy_rate()
    if jpy_rate is None:
        print("[警告] 為替レート取得に失敗しました。USD建てのみ表示します。\n")

    for pod in running_pods:
        print_pod(pod, jpy_rate)

    return 0


if __name__ == "__main__":
    sys.exit(main())
