# language/05-type-systems — 정답

## 정답

### 1. 동적 타입 ≠ 타입 없음

- 동적 타입 언어도 값마다 타입 표식이 있다. 연산 직전에 실행 중 검사한다.
- Python(동적·암묵 변환 적음): `"1" + 1` → `TypeError: can only concatenate str (not "int") to str`(실험 A).
- JS(동적·암묵 변환 많음): `+`의 한쪽이 문자열이면 다른 쪽을 문자열로 바꿔 `"11"`.
- 두 언어 모두 검사 시점은 실행 중이다. 차이는 "알아서 바꿔 주는 범위"다.

### 2. `-1 < sizeof(int)`

- 거짓이다. 실험 A 출력: `-1 < sizeof(int): false`, `(size_t)-1 = 18446744073709551615`(x86-64, gcc 13.3).
- `sizeof`의 타입은 부호 없는 `size_t`다. 비교 전에 usual arithmetic conversions(N1570 6.3.1.8)로 `-1`이 부호 없는 값으로 바뀐다. `size_t`의 변환 순위가 `int` 이상인 보통의 환경 이야기다 — `size_t`가 `int`보다 좁은 구현이라면 `size_t` 쪽이 `int`로 바뀌어 참이 될 수 있다.
- C 표준이 정한 변환이므로 UB가 아니라 정의된 동작이다.
- `-Wsign-compare`(gcc는 `-Wextra`에 포함되어 실험에서 경고가 났다)가 잡는다.

### 3. 명목 vs 구조

- 명목적: 선언된 이름·상속 관계로 호환을 정한다. 구조적: 멤버의 모양으로 정한다.
- Java: `incompatible types: FileThing cannot be converted to Reader` 컴파일 오류.
- Go: `implements` 선언 없이 통과, `go structural: data` 출력(실험 B).
- 함정: 우연히 모양이 같은 타입(회원 `{id}`와 주문 `{id}`)이 섞인다.
- 막는 법: 브랜드 필드·newtype 같은 전용 타입([software-design/24](../../software-design/24-types-as-invariants/2-summary.md)).

### 4. 힙 오염의 실패 지점

```text
  legacyAdd(raw List) ── add(Object) ──> [ 42 ]   ← 검사 없음 (소거: add의 매개변수는 Object)
  String s = names.get(0);
     invokeinterface List.get → Object
     checkcast String   ← 여기서 ClassCastException
```

- 넣을 때: 소거 뒤 `add`는 `Object`를 받는다. 원시 타입 경유라 컴파일러는 unchecked 경고만 낸다.
- 꺼낼 때: javac가 `get` 뒤에 `checkcast String`을 넣었다(실험 C의 `106: checkcast`). 이 명령이 실패한다.
- `Object o = names.get(0)`이면 `checkcast`가 없어 실패하지 않는다(실험 C `get as Object ok: 42`).

### 5. 같은 클래스, Signature 속성

- `true`(실험 C `same class at runtime: true`). 타입 인자는 소거되어 객체에 남지 않는다.
- `Signature` 속성(JVMS 4.7.9)은 **선언**의 제네릭 정보다. 리플렉션(`Field.getGenericType()` 등)과 컴파일러가 읽는다.
- 실행 중 객체가 무엇을 담고 있는지는 알려 주지 않는다. 검사에도 쓰이지 않는다.

### 6. 공변 배열 vs 무공변 제네릭

| | 잘못된 쓰기를 막는 시점 | 형태 |
|---|---|---|
| 배열 `Object[] a = new String[1]; a[0] = 1;` | 실행 중 | `ArrayStoreException: java.lang.Integer`(JLS 10.5) |
| 제네릭 `List<Object> l = new ArrayList<String>();` | 컴파일 | `incompatible types` 오류 |

- 배열 객체는 자기 원소 타입을 실행 중에 안다. 그래서 JVM이 저장마다 검사할 수 있다.
- 제네릭 객체는 소거로 원소 타입을 모른다. 실행 중 검사할 근거가 없다. 그래서 컴파일 시점에 무공변으로 막고(실행 중 타입 인자를 유지하는 C#의 `List<T>`도 무공변이다 — 가변 컬렉션의 타입 안전이 근본 이유이고, 소거는 배열식 실행 중 검사를 막는 이유다), 필요한 방향만 와일드카드(`? extends`/`? super`)로 연다.

### 7. 단일화 계산

- `\f. \x. f (f x)`
  - `f : t0`, `x : t1`. 안쪽 `f x`에서 `t0 = t1 -> t2`.
  - 바깥 `f (f x)`에서 `t0 = t2 -> t3`. 단일화하면 `t1 = t2`, `t2 = t3`.
  - 결과: `(a -> a) -> a -> a`(실험 D 출력과 같다).
- `(\id. id id)`: 람다 매개변수 `id`는 한 타입 변수 `t`다. `id id`에서 `t = t -> u`가 나와 occurs check 실패(실험 D `occurs check: t12 = t12 -> t13`).
- `let id = \x.x in id id`: `let`으로 묶은 이름은 일반화(∀a. a -> a)된다. 쓸 때마다 새 변수로 인스턴스화하므로 두 `id`가 다른 타입을 가질 수 있다 → `a -> a`.

### 8. CCE 원인 위치 찾기

1. 스택 트레이스 줄이 컬렉션에서 꺼내는 곳(`get`, 향상된 for, 람다)이면 힙 오염을 의심한다.
2. `javac -Xlint:unchecked`로 원시 타입·unchecked 호출을 모두 본다(`Raw.java:3: warning: [unchecked] unchecked call to add(E) …`).
3. 의심 컬렉션을 `Collections.checkedList(list, String.class)`로 감싼다. 이제 이 뷰를 거쳐 넣는 순간 CCE가 나고 스택이 원인을 가리킨다(실험 C `at Checked.legacyAdd(Checked.java:4)`). 원래 리스트 참조로 넣는 경로는 검사를 우회하고, 감싸기 전에 든 원소도 검사하지 않는다(Java SE 21 API) — 모든 삽입 경로가 뷰를 쓰게 바꿔야 한다.
4. 역직렬화 경계라면 원소 타입을 담은 타입 토큰을 넘기고, `Class.cast`로 경계에서 한 번 검증한다.
5. 재발 방지: unchecked 경고를 CI에서 오류로.

### 9. TS와 Java의 공통점

- 같은 점: 둘 다 정적 타입 정보가 실행 코드에 남지 않는다. TS는 JS로 컴파일되며 타입이 지워진다. Java 제네릭은 타입 인자가 지워진다. 외부에서 들어온 값은 정적 타입과 무관하게 아무 모양이나 될 수 있다.
- 차이: Java는 꺼낼 때 `checkcast`가 있어 늦게라도 예외가 난다. TS(JS)는 꺼낼 때 그런 자동 검사가 없다. 없는 속성을 읽으면 `undefined`가 나와 그대로 흘러가다가, 그 값의 속성을 읽는 것처럼 허용되지 않는 연산에서 비로소 `TypeError`가 난다(ECMAScript `ToObject`: Undefined → TypeError). 그래서 증상 위치가 원인과 더 멀어질 수 있다.
- 대처: 신뢰 경계(HTTP 응답·메시지)에서 런타임 스키마 검증을 한다. `as` 단언은 검사가 아니다([languages/ts/syntax/30](../../../languages/ts/syntax/30-type-assertions-and-non-null/2-summary.md)).
