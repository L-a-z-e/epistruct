---
name: expo-sdk-upgrade-53-to-56
description: Expo SDK 53 → 56 업그레이드 경로 — peer dep 충돌 및 버전 정렬 방법
metadata:
  type: error
  severity: moderate
  stack: expo, react-native, node
---

## 증상

`pnpm install` 후 peer dependency 경고 다수 발생:
- `react-native-screens` needs RN >=0.82.0 but found 0.76.5
- `expo-router ~4.0.0` (SDK 53) vs 필요 버전 불일치

## 원인

`expo` 버전만 올리고 나머지 패키지를 `npx expo install --fix`로 정렬하지 않으면
각 패키지가 이전 SDK 기준 버전을 유지해 충돌 발생.

## 해결 순서

```bash
# 1. expo 버전만 먼저 변경
pnpm add expo@~56.0.0

# 2. expo가 권장하는 버전으로 나머지 자동 정렬
npx expo install --fix

# 3. 남은 수동 수정 (--fix가 못 잡는 것)
pnpm add expo-linking@$(npx expo install --check 2>&1 | grep expo-linking | ...)

# 4. eslint v9 수동 업그레이드 (expo가 건드리지 않음)
pnpm add -D eslint@^9.0.0 eslint-config-expo@~56.0.4
```

## SDK 56 주요 버전

| 패키지 | 버전 |
|--------|------|
| expo | ~56.0.8 |
| expo-router | ~56.2.8 |
| react | 19.2.7 |
| react-native | 0.85.3 |
| typescript | ~6.0.3 |

## 불가피한 잔여 경고

`react-native-worklets@0.9.1` — transitive dep, 수동 수정 불가. 무시해도 무방.
