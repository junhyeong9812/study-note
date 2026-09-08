# 개념: probe(사전 시험 호출) — 하나의 검사, 두 개의 출구

> PR #37153 학습 중 놓쳤던 개념. 질문의 형태: "probe라는 용어를 어떻게 이해해야
> 해?" / "canLoad 실패도 IllegalStateException으로 나와야 하는 거 아니야?"

## probe란

값이 필요해서 읽는 게 아니라, **문제가 있는지 미리 찔러보는 시험 호출**이다.
전자공학의 탐침처럼, `AttributeMethods.canLoad()`는 위험 표시가 된 속성 메서드를
한 번 실제로 호출해 보고 **결과값은 버린다** — 관심사는 "이 호출이 예외 없이
성공하는가"뿐이다. 성공하면 통과, 예외가 나면 "이 annotation은 나중에 반드시
터진다"는 신호로 보고 스캔 단계에서 미리 걸러낸다. 한국어로는 "사전 시험 호출"이
가장 가깝다.

핵심 전제: 대상 실패가 **지연 실패**라는 것. JDK annotation 값 해석은 읽는 순간에야
터지므로([이름 저장과 지연 해석](enum-annotation-name-resolution.md)), 미리 한 번
읽어보는 것으로 "언젠가 터질 놈"을 지금 판별할 수 있다.

## 인과 사슬 (방향을 헷갈렸던 부분)

플래그 값에 따라 사슬이 두 갈래로 갈리는데, 검사가 도는 쪽이 true라는 것이 핵심이다.

```
플래그(canThrowTypeNotPresentException) = true
  → probe 수행 → 예외 관측 → canLoad = false → 필터링(warn 로그) → isPresent() = false

플래그 = false  (수정 전 enum 배열이 여기)
  → probe 스킵 → 예외를 관측할 기회 자체가 없음 → canLoad = true(오판) → 오염된 annotation 통과
```

주의: "플래그 true = 검사를 한다"이다. 학습 중 두 번 반대로 말했던 지점 —
플래그가 **false**라서 검사가 **안 돌아** "정상"으로 오판되는 것이 버그였다.

## 하나의 probe, 두 개의 출구

`canLoad()`와 `validate()`는 **같은 probe**(플래그 선 속성 실호출)를 돌리지만
실패를 알리는 방식이 다르다:

| | canLoad | validate |
|---|---|---|
| 실패 보고 | **boolean `false` 반환** — 예외를 밖으로 던지지 않음 | **`IllegalStateException`을 던짐** — 원인 예외를 cause로 감쌈 |
| 소비자 | `AnnotationsScanner` — false면 스캔 결과에서 제외 + warn 로그 | "이 annotation은 반드시 읽혀야 한다, 아니면 크게 실패하라"는 명시 검증 경로 |
| 성격 | 흐름 제어용 조용한 출구 | 계약 위반 보고용 시끄러운 출구 |

원인 예외는 어디까지나 enum/타입 오류(`EnumConstantNotPresentException` 등)이고,
validate는 그것을 `IllegalStateException`으로 **감싸는** 것이다(원인은 cause 체인에
보존). "관측 오류라서 ISE"가 아니라 "타입 오류를 관측했고, 그 사실을 ISE로 보고".

테스트가 두 벌인 이유도 여기 있다: canLoad 실패 테스트는 `isFalse()`를, validate
실패 테스트는 `assertThatIllegalStateException`을 확인한다 — **보고 방식이 다르다는
것 자체가 각각 검증할 계약**이다.

## 비용 감각

probe는 리플렉션 실호출이므로 공짜가 아니다. 그래서 플래그로 **위험 타입만**
선별하고(`Class`, `Class[]`, enum, 이제 enum[]), 스캐너는 element 단위 캐시로 반복
빈도를 제한한다. "정확성을 위한 최소 비용"이 이 설계의 트레이드오프다.
