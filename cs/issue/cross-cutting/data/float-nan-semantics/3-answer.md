# cs/issue/data/float-nan-semantics — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **`NaN == NaN`은 false.**\
   IEEE-754는 NaN과의 모든 순서·동등(`==`) 비교를 거짓으로 정의한다(`!=`만 참).\
   그래서 동치 관계의 **반사성(x == x)** 이 깨진다.\
   대칭성·추이성이 아니라 "자기 자신과 같다"는 가장 기본 조건이 무너지는 것이다.
   > **반사성(reflexivity)** — 모든 x에 대해 x == x가 참이어야 한다는 동치 관계의 조건.

2. **전동치 선언 불가.**\
   "완전한 동치(Eq)"는 반사성까지 보장한다는 약속인데, 부동소수점은 NaN 때문에 그 약속을 지킬 수 없다.\
   동적 값 타입이 f64를 그대로 담고 Eq를 구현하지 않으면 같은 제약을 물려받는다 — 그 필드 하나가 구조체 전체의 `derive(Eq)`를 막는다(라이브러리마다 다름 — NaN을 표현 불가로 막고 Eq를 제공하는 JSON 값 타입도 있다).\
   부분 동치(PartialEq)만 남기면 테스트의 동등 단언은 그대로 쓰지만, **해시 맵 키처럼 Eq를 요구하는 자리**에는 그 타입을 쓸 수 없게 된다(전순서 비교 `total_cmp`나 순서 보장 래퍼 타입으로 Eq를 직접 정의하는 길은 별도로 있다).
   > **PartialEq / Eq** — 부분 동치(반사성 미보장)와 전동치(반사성 보장)를 구분하는 트레이트.

3. **`v == Float.NaN` 분기는 어떤 입력에서도 실행되지 않는다.**\
   v가 NaN이어도 NaN == NaN이 false이기 때문이다.\
   특수값 탐지는 `Float.isNaN(v)`처럼 **전용 판정 함수**로 한다.\
   ±Infinity는 == 비교가 정상 동작하므로 `v == Float.POSITIVE_INFINITY`로 잡을 수 있다.

4. **toString ≠ 리터럴 문법.**\
   NaN의 toString은 `"NaN"`, 무한대는 `"Infinity"`인데 이것은 언어의 적법한 숫자 리터럴이 아니다 — 생성 코드에서는 선언되지 않은 식별자로 읽혀 컴파일이 실패한다.\
   템플릿의 "리터럴 그대로 삽입" 치환은 인자를 검증하지 않고 문자열을 넣으므로 이 불일치를 막지 못한다.\
   특수값은 리터럴이 없으니 **정적 상수 참조**(`Float.NaN`, `Float.POSITIVE_INFINITY`)로 출력한다.

5. **분기 순서.**\
   유한값 출력 폴백은 "아무 float이나 toString + 접미사"로 처리하는 일반 경로라, 먼저 실행되면 특수값도 그 경로로 빠져 다시 비컴파일 코드가 된다.\
   특수값 분기가 폴백보다 앞에 있어야 "특수값 → 상수 참조, 나머지 → 리터럴"이 성립한다.

6. **왕복 계약과의 연결.**\
   코드 생성은 "값 → 문자열(소스) → 컴파일러가 다시 값으로 해석"하는 왕복이다.\
   출력 표현이 소비자(컴파일러)의 문법 안에 있어야 왕복이 성립한다는 점에서, 구분자 이스케이프·직렬화 포맷 문제와 같은 구조다 — 출력 쪽 표현이 입력 쪽 문법의 부분집합이어야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — 부동소수점을 품은 타입에 전동치 선언
① 문제 코드
```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]   // Eq ✗
pub struct Record {
    // ...
    #[serde(default)]
    pub layout: Option<AnyValue>,   // AnyValue는 f64를 담을 수 있다
}
```
② 고친 코드
```rust
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize)]  // Eq 제거
pub struct Record {
    // ...
    #[serde(default)]
    pub layout: Option<AnyValue>,
}
// 대가: Record는 해시 맵 키 등 Eq 요구 자리에 쓸 수 없다
```
무엇이 깨졌나: 새 필드 하나가 품은 f64가 NaN 반사성 문제를 구조체 전체의 동치 선언으로 전파했다.

### 변형 B — 코드 생성에서 특수값을 리터럴로 출력
① 문제 코드
```java
Code generate(Object value) {
    if (value instanceof Float) {
        return Code.literal(value + "F");          // "NaNF", "InfinityF" → 컴파일 불가
    }
    // ...
}
// 고칠 때의 함정: if (f == Float.NaN) { ... }  → NaN == NaN 이 false라 영원히 미도달
```
② 고친 코드
```java
Code generate(Object value) {
    if (value instanceof Float f) {
        if (Float.isNaN(f)) return Code.constantRef(Float.class, "NaN");
        if (f == Float.POSITIVE_INFINITY) return Code.constantRef(Float.class, "POSITIVE_INFINITY");
        if (f == Float.NEGATIVE_INFINITY) return Code.constantRef(Float.class, "NEGATIVE_INFINITY");
        return Code.literal(value + "F");          // 유한값 폴백은 마지막 (-0.0·서브노멀은 toString이 적법 리터럴)
    }
    // ...
}
```
무엇이 깨졌나: "생성 코드는 컴파일 가능해야 한다"는 불변식을 toString이 리터럴이라는 가정에 맡겼고, 특수값에서 그 가정이 깨졌다(탐지를 ==로 쓰면 NaN만 다시 새어 나간다).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
