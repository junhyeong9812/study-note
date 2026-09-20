# spi

상위: [마운트](../README.md)

React 소스를 읽을 때 Java 와 가장 다른 점은 **빌드 플래그**다. 같은 파일을 읽어도 어느 빌드냐에 따라 도는 코드가 다르고, 어떤 분기는 **어느 빌드에서도 안 돈다.** 이 문서는 그 계약을 모았다.

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a).

## 플래그는 두 곳에 있다

```text
 (가) 호출하는 쪽
      if (enableTransitionTracing) { ... }          WorkLoop L1042
      눈에 보인다

 (나) 불리는 함수의 첫 줄
      export function startUpdateTimerByLane(...) {
        if (!enableProfilerTimer || !enableComponentPerformanceTrack) return;
        ...
      }
      호출부에는 플래그가 없다

 (나) 유형의 예 (이 흐름에서만)
      onScheduleRoot                 DevToolsHook 안에서 __DEV__
      markRenderScheduled            DevToolsHook 안에서 enableSchedulingProfiler
      startUpdateTimerByLane         ReactProfilerTimer 안에서 두 플래그
      registerDefaultIndicator       AsyncAction 안에서 enableDefaultTransitionIndicator
      warnIfUpdatesNotWrappedWithActDEV  WorkLoop 안에서 __DEV__

 => 호출부만 훑어 플래그를 세면 대부분을 놓친다
    이 흐름의 실제 분기 자리는 여덟이 아니라 서른 자리가 넘는다
```

## 빌드 메타 플래그 셋

`scripts/rollup/build.js` 가 정한다.

| | dev 번들 | production 번들 | profiling 번들 |
|---|---|---|---|
| `__DEV__` | `true` | **`false`** | `false` |
| `__PROFILE__` | **`true`** | `false` | `true` |
| `__EXPERIMENTAL__` | 릴리스 채널에 따름. stable npm 은 `false` | | |

```text
 __PROFILE__ 이 dev 에서도 true 인 것에 주의

 "프로파일링 빌드 전용" 이라고 읽으면 틀린다
 enableUpdaterTracking 과 enableProfilerTimer 가 __PROFILE__ 이므로
 **개발 빌드에서도 켜져 있다**

 그래서 개발 중에 보이는 동작이 운영과 다를 수 있다
```

```text
 __DEV__ 블록은 프로덕션 번들에서 사라진다

 rollup 이 토큰을 리터럴 false 로 치환하고 (build.js)
 Closure 가 if (false) 를 지운다

 즉 __DEV__ 안의 경고는 운영에서 나오지 않는다
 (산출 번들을 직접 열어 확인하지는 않았다. 빌드 설정까지만 본 것이다)
```

## 어느 플래그 파일을 쓰는가

```text
 packages/shared/forks/ 에 ReactFeatureFlags 변형이 여럿 있는데
 react-dom 은 그 어느 것도 쓰지 않는다

 scripts/rollup/forks.js 의 매핑에서 react-dom 엔트리는
 어느 case 에도 안 걸리고 null 을 돌려준다 = 포크 없음
 => packages/shared/ReactFeatureFlags.js 원본을 쓴다

 포크를 쓰는 것은 www(페이스북), React Native(native-fb / native-oss),
 test-renderer, eslint-plugin 이다
```

## 이 흐름의 플래그

기본값은 OSS `react-dom` 기준이다. **동작**은 코드 경로가 달라지는 것, **경고**는 메시지만 사라지는 것이다.

| 플래그 | 기본값 | 무엇이 달라지나 | |
|---|---|---|---|
| `__DEV__` | dev `true` / prod `false` | 경고 대부분. 다만 넷은 동작이다 — `onScheduleRoot` 호출, `didScheduleUpdateDuringPassiveEffects` 세움, `isBatchingLegacy` 분기, 루트 fiber 에 `ProfileMode` 추가 | 혼합 |
| `disableLegacyMode` | **`true`** | 가장 크다. 아래 따로 본다 | 동작 |
| `disableCommentsAsDOMContainers` | `true` | 주석 노드를 컨테이너로 못 쓴다. 꺼지면 허용하고 리스너를 `parentNode` 에 건다 | 동작 |
| `enableSuspenseCallback` | `false` | `root.hydrationCallbacks` 필드 자체가 생기지 않는다 | 동작 |
| `enableTransitionTracing` | `false` | `root.transitionCallbacks` 필드 + 갱신마다 transition 기록 | 동작 |
| `enableDefaultTransitionIndicator` | `__EXPERIMENTAL__` (stable `false`) | `onDefaultTransitionIndicator` 옵션 수용 + 관련 필드 | 동작 |
| `enableUpdaterTracking` | `__PROFILE__` (dev `true`) | `root.memoizedUpdaters` + DevTools 에 fiber 기록 | 계측 |
| `enableProfilerTimer` | `__PROFILE__` (dev `true`) | 루트 fiber 에 `ProfileMode`, 업데이트 타이머 | 계측·동작 |
| `enableSchedulingProfiler` | **언제나 `false`** | 정의가 `!enableComponentPerformanceTrack && __PROFILE__` 인데 앞이 `true` 로 고정이라 결과가 늘 `false` | 죽은 코드 |
| `enableInfiniteRenderLoopDetection` | `false` | 켜지면 `markRootUpdated` 가 무한 루프를 감지해 던질 수 있다 | 동작 |

## 이 빌드에서 아예 안 도는 코드

```text
 disableLegacyMode 가 true 라서 죽는 것

 WorkLoop L1080-1097   legacy sync flush 블록 통째
                       조건에 !disableLegacyMode 가 있다 (L1083)
 Reconciler L378-380   updateContainerSync 의 flushPendingEffects
 WorkLoop L813         requestUpdateLane 의 첫 갈래 (SyncLane 고정)

 그리고 한 겹 더 막혀 있다

 FiberRootNode L63   this.tag = disableLegacyMode ? ConcurrentRoot : tag;
                     넘어온 tag 를 **덮어쓴다**
 createHostRootFiber L541  if (disableLegacyMode || tag === ConcurrentRoot)
                     앞 항만으로 mode = ConcurrentMode 가 확정된다

 => createRoot 이 ConcurrentRoot 를 넘기는 것은 결과적으로 무의미하다
    플래그가 이미 같은 일을 한다
    (주석은 없다. 세 자리를 이어 보고 내가 판단한 것이다)

 이 갈래들이 사는 곳은 React Native fb 빌드뿐이다
 (native-fb 와 native-oss 만 disableLegacyMode 가 false 다)
```

```text
 enableSchedulingProfiler 는 어느 빌드에서도 안 돈다

 ReactFeatureFlags L235  enableComponentPerformanceTrack = true
 ReactFeatureFlags L244-245
   enableSchedulingProfiler = !enableComponentPerformanceTrack && __PROFILE__

 앞 항이 상수 true 라 부정하면 false 고, && 이므로 결과가 늘 false 다
 그래서 Reconciler L405 의 markRenderScheduled 는 호출조차 안 된다
 (www 포크는 값이 다르다)
```

## 읽을 때의 규칙

```text
 1. 분기를 만나면 플래그인지 먼저 본다
    플래그면 기본값을 ReactFeatureFlags.js 에서 확인한다

 2. 호출만 보고 넘어가지 않는다
    그 함수 첫 줄에 플래그 가드가 있을 수 있다

 3. 플래그 정의가 다른 플래그로 되어 있으면 끝까지 푼다
    enableSchedulingProfiler 처럼 늘 false 인 것이 있다

 4. __PROFILE__ 은 dev 에서도 true 다

 5. 포크를 쓰는 빌드인지 확인한다
    react-dom 은 원본을 쓴다
```

## 결과가 쓰이는 곳

```text
 플래그 값
      --> 어느 코드가 도는지를 정한다
      --> 문서가 "이 분기는 이렇게 동작한다" 고 쓸 때
          그 빌드에서 실제로 도는지 먼저 확인해야 한다

 죽은 갈래
      --> 소스에는 있지만 읽는 사람이 재현할 수 없다
      --> 이 지도는 그런 자리를 따로 표시한다
```

## 다루지 않는 것

`ReactFeatureFlags.js` 의 나머지 플래그 전부, 포크 파일 여덟 개의 값 차이(일부만 확인했다), `__VARIANT__` 가 정해지는 방식, Closure 컴파일러의 DCE 동작, 릴리스 채널(`stable` / `canary` / `experimental`)의 구분과 배포 경로는 이 문서의 범위 밖이다.
