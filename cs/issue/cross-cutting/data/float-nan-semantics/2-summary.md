# cs/issue/data/float-nan-semantics — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
IEEE-754 특수값
   NaN        NaN == NaN  → false   (반사성 x == x 붕괴)
   ±Infinity  == 비교는 정상 동작

[변형 A] 타입 시스템의 동치 선언
   struct Record { layout: Option<DynamicValue> }   DynamicValue ⊃ f64
   derive(Eq)  ──✗ 컴파일 거부 (f64는 반사성을 보장 못 함)
   교정: PartialEq만 유지 → assert_eq!는 동작 · Eq 요구 자리(해시 키)에는 못 씀

[변형 B] 코드 생성의 리터럴 출력
   값 NaN ──toString()──▶ "NaN" ──소스에 삽입──▶  float x = NaN;   ✗ 컴파일 불가
   탐지를 v == NaN 으로 하면        → 영원히 false → 특수값 분기 미도달
   교정: isNaN(v) / v == +Inf 분기를 "유한값 출력" 폴백보다 먼저
         → 정적 상수 참조 Float.NaN, Float.POSITIVE_INFINITY 로 출력
```

## 핵심 문장

- NaN은 **자기 자신과 같지 않다** → "x == x"를 전제로 한 모든 것(전동치 선언·== 탐지·중복 제거)이 깨진다.
- 부동소수점을 담은 타입은 **부분 동치까지만** 선언 가능. 대가는 해시 키처럼 전동치를 요구하는 자리에서 못 쓰는 것.
- NaN 탐지는 `==`가 아니라 **전용 판정 함수(isNaN)**.
- 값의 `toString()`은 **소스 코드 리터럴 문법이 아니다** — 특수값은 리터럴이 없으니 상수 참조로 출력하고, 그 분기는 일반 경로보다 먼저 둔다.
