# language/06-values-references-passing — 정답

## 정답

### 1. 참조를 값으로 복사한다

```text
  caller 칸 x ──┐
                ├──> Box { v }        b.v = 99      → 같은 객체를 고침 → 호출자도 봄
  callee 칸 b ──┘                     b = new Box() → callee 칸만 새 객체를 가리킴 → 호출자는 그대로
```

- 세 언어 모두 값에 의한 전달이다. 객체 인자는 **참조 값**이 새 칸에 복사된다.
- 내부 수정은 같은 객체를 고치므로 보인다. 재할당은 callee의 칸만 바꾸므로 안 보인다.
- 실험 A: Java `after mutate : x=Box(99)`, `after reassign : y=Box(2)`, JS `after reassign: {"v":1}`, `after mutate: {"v":99}`.

### 2. 포인터 교환 vs 참조 교환

- `swap_ptr`: 바뀌지 않는다(`swap_ptr : i=1 j=2`). 포인터 값의 복사본만 서로 바꿨다.
- `swap_ref`: 바뀐다(`swap_ref : i=2 j=1`). 매개변수가 호출자 변수의 별명이다.
- 고칠 서술: "C에는 참조에 의한 전달이 없다. 주소를 **값으로** 넘기고, 받은 쪽이 역참조(`*x = value`)해서 호출자 메모리를 고친다." 덧붙여 원고의 "4바이트"는 32비트 기준이고, 이 x86-64 빌드에서 `sizeof(int*) = 8`이었다.

### 3. 세 가지 복사

```text
  new ArrayList<>(orig)  →  새 리스트 ──> Box1, Box2 (공유)
  List.copyOf(orig)      →  새 변경 불가 리스트 ──> Box1, Box2 (공유)   ※ orig가 ArrayList라서 새로 만든다.
                                                                        orig가 이미 변경 불가면 그대로 돌려줄 수 있다(API 문서)
  원소까지 복사          →  새 리스트 ──> Box1', Box2'
```

- `shallow.get(0).v = 100`은 원본에 보인다(`orig after shallow edit : [Box(100), Box(2)]`, `copyOf sees: [Box(100), Box(2)]`).
- `shallow.add(...)`는 안 보인다(`orig size after shallow.add : 2`). 리스트 객체가 서로 다르기 때문이다.

### 4. 박싱 캐시

- 기본: `127 == : true`, `128 == : false`, `128 equals : true`(실험 C).
- `-XX:AutoBoxCacheMax=1000`: `128 == : true`.
- JLS 5.1.7은 상수 식 박싱에서 -128~127만 같은 참조를 요구한다. 실행 중 박싱은 `Integer.valueOf` API 문서가 같은 범위의 캐시를 보장한다. 그 밖은 구현·설정에 달렸다.
- 교훈: 박싱 값을 `==`로 비교하는 코드는 값의 크기와 JVM 옵션에 따라 결과가 바뀐다. `equals`·`Objects.equals`나 기본형 비교를 쓴다.

### 5. 동일성 vs 동등성

| | 동일성(같은 객체) | 동등성(같은 값) |
|---|---|---|
| Java | `==`(참조형) | `equals()` |
| Python | `is` | `==`(`__eq__`) |
| JS | `===`·`Object.is`(객체일 때) | 내장 없음 — 직접 정의 |

- `NaN === NaN`은 거짓(IEEE 754 비교 규칙을 따름), `Object.is(NaN, NaN)`은 참이다(실험 A `passing.js`). `Object.is`는 `+0`과 `-0`도 구별한다(ECMAScript 2024 6.1.6.1.14 Number::sameValue: "If x is +0𝔽 and y is -0𝔽, return false." — node 22에서 `Object.is(+0,-0)`은 `false`, `+0 === -0`은 `true`).

### 6. 응답에 앞 요청 데이터가 섞임

- 의심: 함수 기본 인자로 가변 객체(`acc=[]`, `cache={}`)를 쓴 곳. 모듈 전역 가변 객체도 후보다.
- 확인: 해당 함수의 `__defaults__`를 찍어 누적되는지 본다(실험 §5 `__defaults__ : (['user_001', 'user_002'],)`). 요청마다 `id(acc)`가 같은지도 본다.
- 원인: 기본값은 `def` 실행 때 한 번 평가된다(Python 레퍼런스 8.7).
- 고침: `acc=None` 후 함수 안에서 `acc = []`(실험 `fixed1: ['user_001'] fixed2: ['user_002']`).

### 7. 순환 참조의 깊은 복사

- 필요한 것: "원본 객체 → 이미 만든 사본" 표. 이미 복사한 객체를 다시 만나면 표의 사본을 쓴다.
- 그래프 순회의 **방문 표(visited)** 와 같다. 없으면 순환에서 무한히 내려간다.
- `copy.deepcopy`는 `memo` 딕셔너리로 이를 한다. 실험 B: `cyclic deepcopy ok: True True` — 사본의 `self`가 사본 자신을 가리키고, 원본과는 다른 객체다.

### 8. JSON 왕복 vs structuredClone

- JSON 왕복: `Date`가 문자열이 된다(`JSON round-trip Date -> string`). `undefined`·함수는 객체 안에서 빠지고, `Map`은 `{}`가 된다(MDN `JSON.stringify`: "undefined, Function, and Symbol values are not valid JSON values… omitted", "Map, Set, etc. will become \"{}\"" — node 22 재현: `{"m":{},…}`).
- `structuredClone`: `Date`는 유지된다(`clone.created is Date: true`). 함수는 `DataCloneError`로 실패한다.
- 둘 다 클래스 인스턴스의 프로토타입(메서드)을 옮기지 않는다(MDN 구조화 복제: "The prototype chain is not walked or duplicated." — node 22 재현: 사본 `instanceof A`가 `false`). 도메인 객체는 명시적 복사 함수가 안전하다.

### 9. 4294967295의 정체

- CPython 3.12의 **불멸 객체**(PEP 683, Python-Version 3.12) 표시다. 불멸 객체는 참조 카운트를 고정값(64비트에서 `UINT_MAX` = 4294967295, `Include/object.h`)으로 두고 증감하지 않는다.
- 로컬 실행(CPython 3.12.3): `None: 4294967295`, `small int 5: 4294967295`, 상수 접기된 `"a"*1000`도 4294967295. 3.12.3은 컴파일러가 인턴한 문자열도 불멸로 만들었다.
- 하지만 3.12.14(`python:3.12-slim`)에서는 `None`·5만 4294967295이고 `"a"*1000`은 `4`, `"abcde"`는 `3`이었다. 변경 기록상 3.12.7(gh-113993)에서 인터닝 내부가 바뀌었다(이것이 차이의 원인이라는 것은 해석 — 중간 패치는 돌려 보지 않았다). 같은 체인지로그의 Core 항목과 C API 항목이 서로 어긋나는데, 3.12 C API 문서는 "interned strings are not 'immortal'"이라 적으므로 그쪽을 따른다(09와 같은 판단). 인턴 문자열이 불멸이라는 것은 보장이 아니라 3.12.3에서 관찰된 구현 결과다. 같은 "3.12"라도 패치 버전에 따라 문자열 결과가 다르다.
- 실행 중 `"a" * n`으로 만든 문자열은 인턴되지 않은 일반 객체라 두 버전 모두 실제 카운트(`2`)가 나온다. 둘은 `==`는 참이고 `is`는 거짓이었다.
- 즉 "인터닝"은 같은 객체를 재사용하는 것이고, 4294967295라는 숫자는 불멸 표시다. 두 개념은 한때 겹쳤을 뿐 같은 것이 아니다.
