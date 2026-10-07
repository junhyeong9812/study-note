# language/06-values-references-passing — 값과 참조, 전달 방식, 얕은/깊은 복사, 동일성 vs 동등성 — 정리 (힌트)

## 해결하는 문제

변수에 든 것이 **값 자체**인지, **객체를 가리키는 표(참조)** 인지 모르면 두 종류의 사고가 난다.

```text
  복사한 줄 알았는데 공유였다           공유인 줄 알았는데 복사였다
  b = a.copy()  b[0][0] = 99           swap(x, y)  → 호출자의 x, y는 그대로
  → a도 바뀜                            reassign(p) → 호출자는 옛 객체를 계속 봄
```

- *값(value)*: 변수 칸에 직접 든 데이터. Java의 `int`, C의 구조체.
- *참조(reference)*: 힙에 있는 객체를 가리키는 값. 변수 칸에는 주소 같은 "가리킴"만 든다.

쉬운 예: 공유 문서다.
- 링크를 보내면 받은 사람이 고친 내용이 내 화면에도 보인다 → 참조 공유.
- 파일을 내려받아 보내면 받은 사람이 고쳐도 내 원본은 그대로다 → 값 복사.
- 폴더를 복사했는데 안의 바로가기는 원본을 가리킨다 → 얕은 복사.

똑같은 구조다.\
언어는 "무엇을 복사하나"를 정해 둔다. 대부분의 언어는 **참조를 값으로 복사**한다. 그래서 내부 수정은 보이고, 재할당은 안 보인다.

실무 예:
- Python 함수의 기본 인자 `acc=[]`가 요청마다 공유되어 앞 사용자 데이터가 다음 응답에 섞인다.
- 테넌트별 설정을 템플릿에서 얕게 복사했더니, 한 테넌트의 중첩 설정 변경이 모든 테넌트에 퍼진다.
- 테스트에서는 ID가 작아 `Integer == Integer`가 통과했는데, 운영에서 ID가 128을 넘자 같은 ID가 "다르다"고 나온다.

기초 서술(파이썬 변수 = 이름표, 얕은/깊은 복사, 불변·가변 객체를 함수에 넘기기)은 원고 [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md) §1·§2·§4·§5·§7·§8에 있다. 이 노트는 그 위에 언어 비교, 동일성/동등성, 장애를 더한다.

## 동작·원리

### 1. 값과 참조 — 스택 칸과 힙 객체

```text
  Java 메서드 프레임(스택)                 힙
  ┌──────────────┐
  │ int n = 5    │  ← 값이 칸에 직접
  │ Box x  ──────┼──────────>  Box { v = 1 }
  │ Box y  ──────┼──────┐
  └──────────────┘      └──>  Box { v = 2 }

  Python: 모든 변수가 참조 (int도 객체)        n ──> int 객체 5
```

- Java: 기본형(`int`·`long`·`double` …)은 칸에 값, 그 밖은 참조(JLS 4.1의 두 종류 타입).
- Python: 모든 값이 객체이고, 변수는 객체를 가리키는 이름이다(원고 §1).
- C: 구조체·배열 원소도 칸에 값으로 들어간다. 참조가 필요하면 포인터를 명시한다.
- Go: 구조체는 값이다. 슬라이스·맵은 내부 저장소를 가리키는 헤더라서 복사해도 저장소를 공유한다([languages/go/syntax/05](../../../languages/go/syntax/05-arrays-vs-slices-value-and-header/2-summary.md)).

### 2. 전달 방식 — 무엇이 복사되나

```text
  값에 의한 전달(call by value)          참조에 의한 전달(call by reference)
  caller: x ──> Box{1}                   caller: i [1]
  callee: a ──> Box{1}  (참조값 복사)     callee: a ═══ i  (같은 칸의 별명)
   a.v = 99   → 같은 객체 → 호출자도 봄     a = 2  → 호출자 i도 2
   a = new …  → callee의 칸만 바뀜         
```

- *값에 의한 전달*: 인자의 값을 새 칸에 복사한다. 값이 참조면 **참조가 복사**된다.
  - Java·JS·Python·Go·C는 이것뿐이다. 객체를 넘기는 이 모양을 "공유에 의한 호출(call by sharing)"이라 부르기도 한다 [?].
- *참조에 의한 전달*: 매개변수가 호출자 변수의 별명이 된다. C++의 `T&`가 그 예다.
  - 흔한 오해: "C 포인터 전달 = 참조에 의한 전달". C에는 참조 전달이 없다. 주소 값을 **값으로** 복사해 넘기고, 받은 쪽이 역참조해 고친다. 포인터 변수 자체를 바꾸면 호출자에게 안 보인다(실험 A의 `swap_ptr`).

### 실험 A: 네 언어에서 swap·수정·재할당

(실험, `eclipse-temurin:21-jdk` 21.0.12 / `node:22-alpine` v22.23.2 / 호스트 g++ 13.3 `-std=c++17 -O0`, `scratchpad/lang/05/e06/Passing.java`·`passing.js`·`passing.cpp`, 2026-10-07)

```text
Java  after swap     : x=Box(1) y=Box(2)      ← 지역 칸끼리만 교환
      after mutate   : x=Box(99)              ← 같은 객체 수정
      after reassign : y=Box(2)               ← 새 객체는 callee 칸에만
JS    after reassign: {"v":1}
      after mutate  : {"v":99}
C++   by_value  : p.x=1
      by_pointer: p.x=99  caller pointer still non-null=1
      by_ref    : p.y=77
      swap_ptr  : i=1 j=2                     ← 포인터 값만 교환 → 효과 없음
      swap_ref  : i=2 j=1                     ← 진짜 참조 전달
      sizeof(int*) = 8 bytes on this x86-64 build
```

- 참고: 원고 §4의 "보낼 때 4바이트 공간 즉 메모리 주소를 보내는 것"은 32비트 기준이다. 이 x86-64 빌드에서 포인터는 8바이트였다(위 출력). 또 원고 §4는 C 포인터 전달을 "참조에 의한 전달"로 불렀는데, 위 `swap_ptr`처럼 포인터도 값으로 복사된다. 참조 전달의 예는 C++ `swap_ref`다.
- 호출이 스택 프레임에 인자를 어떻게 놓는지는 [architecture/10](../../architecture/10-calling-convention-and-stack-frame/2-summary.md)에 있다.

### 3. 얕은 복사와 깊은 복사 — 참조 그래프에서 어디까지 새로 만드나

```text
  원본 orig ──> [ ●, ● ]                 얕은 복사 shallow ──> [ ●, ● ]   (바깥만 새로)
                  │  │                                          │  │
                  ▼  ▼                                          │  │
               Box1 Box2  <─────────────── 같은 원소 공유 ─────┘──┘

  깊은 복사 deep ──> [ ●, ● ]
                      ▼  ▼
                   Box1' Box2'   (원소까지 새로 → 원본과 독립)
```

- *얕은 복사(shallow copy)*: 바깥 컨테이너만 새로 만들고 원소 참조는 그대로 복사.
- *깊은 복사(deep copy)*: 안쪽 객체까지 재귀적으로 따라가며 복사한다. 순환이 있으면 "이미 복사한 객체" 표가 필요하다.
  - 흔한 오해: "도달 가능한 객체는 전부 새것이 된다". Python `copy.deepcopy`는 함수·클래스를 원본 그대로 돌려주고, 클래스가 `__deepcopy__`로 복사 범위를 정할 수도 있다(Python 3.12 `copy` 문서).

### 실험 B: 얕은 복사가 원본을 바꾼다

(실험 A와 같은 환경 + 호스트 CPython 3.12.3, `Passing.java`·`passing.py`·`passing.js`)

```text
Java   orig after shallow edit : [Box(100), Box(2)]  copyOf sees: [Box(100), Box(2)]
       same list? false  same element? true
       orig size after shallow.add : 2          ← 구조 변경은 독립
       orig after deep edit    : [Box(100), Box(2)]
       grid[0][0] after clone edit = 9          ← 2차원 배열 clone()도 얕다
Python orig after edits: {'user': 'user_001', 'roles': ['read', 'write']}   ← copy.copy의 수정만 샘
       cyclic deepcopy ok: True True            ← deepcopy는 memo로 순환 처리
JS     orig.roles: [ 'read', 'write' ]  clone.created is Date: true
       JSON round-trip Date -> string
       structuredClone(function): DataCloneError
```

- `new ArrayList<>(orig)`도 `List.copyOf(orig)`도 얕다. `List.copyOf`는 **변경 불가 리스트**일 뿐, 원소 객체를 복사하지 않는다. 게다가 입력이 이미 변경 불가 리스트면 보통 새 리스트도 만들지 않고 그대로 돌려준다(Java SE 21 API Implementation Note: "generally not create a copy").
- 원소를 고치면 공유가 드러나고, 원소를 추가·삭제하는 구조 변경은 드러나지 않는다.
- JS: 스프레드(`{...o}`)는 얕다. `structuredClone`은 깊게 복사하고 `Date`를 유지하지만 함수는 복사하지 못한다. `JSON.parse(JSON.stringify())`는 `Date`를 문자열로 바꾼다([languages/js/syntax/48](../../../languages/js/syntax/48-deep-copy-methods-compared/2-summary.md)).

### 4. 동일성 vs 동등성

```text
  동일성(identity): 같은 객체인가?            Java ==   Python is    JS === (객체)
  동등성(equality): 같은 값으로 보는가?       equals()  ==           (직접 정의)

  Integer a = 127, b = 127   ──> [캐시된 Integer 127] <── 같은 객체 → a == b 참
  Integer c = 128, d = 128   ──> [Integer 128] , [Integer 128]  다른 객체 → c == d 거짓
```

- *동일성*: 두 참조가 같은 객체를 가리킨다.
- *동등성*: 타입이 정한 규칙(`equals`·`__eq__`)으로 같은 값이라고 본다.
- Java 박싱 캐시: JLS 5.1.7은 상수 식을 박싱한 결과가 -128~127 범위의 정수 등이면 **같은 참조**가 되라고 요구한다. 그 밖의 범위는 구현 자유다.
  - 실행 중 값의 박싱(`Integer.valueOf`·`Long.valueOf`)은 API 문서가 따로 보장한다: "This method will always cache values in the range -128 to 127, inclusive, and may cache other values outside of this range."
  - HotSpot은 `-XX:AutoBoxCacheMax`로 캐시 상한을 늘릴 수 있다(OpenJDK 21 `c2_globals.hpp`, 기본값 128로 선언).
- 문자열 리터럴과 컴파일 시점 상수 식은 같은 객체로 합쳐진다(인턴). 실행 중 연결(`+`)로 만든 비상수 문자열은 새 객체다(JLS 15.18.1). 단 `intern()`을 부르면 내용이 같은 문자열끼리 같은 객체를 돌려받는다(Java SE 21 API `String.intern`).

### 실험 C: `==`가 통과하다가 128에서 깨진다

(실험 A와 같은 Java 환경, `Passing.java`)

```text
Integer 127 == : true   128 == : false   128 equals : true
literal==const-folded : true  literal==new : false  literal==runtime concat : false  equals : true
--- -XX:AutoBoxCacheMax=1000
Integer 127 == : true   128 == : true   128 equals : true
```

- 같은 코드가 JVM 옵션 하나로 결과가 바뀐다. `==`로 박싱 값을 비교하는 코드는 **구현과 설정에 기대는 코드**다.
- Python의 `is`도 같다. CPython 3.12는 작은 정수(-5~256)를 미리 만든 객체로 쓰는데, 이것은 구현 세부다([languages/python/syntax/02](../../../languages/python/syntax/02-is-vs-eq-interning/2-summary.md)).
- JS: `{} === {}`는 거짓(다른 객체), `NaN === NaN`도 거짓, `Object.is(NaN, NaN)`은 참(실험 A의 `passing.js` 출력).
- 참고: 원고 §6은 `sys.getrefcount("abcde")`가 4294967295인 이유를 인터닝으로 설명했다. 숫자 자체는 CPython 3.12의 **불멸 객체(immortal object, PEP 683)** 표시다. 불멸 객체는 참조 카운트를 고정값으로 둔다(64비트 빌드에서 `UINT_MAX` = 4294967295, CPython 3.12 `Include/object.h`의 `_Py_IMMORTAL_REFCNT`).
  - PEP 683이 불멸로 정한 것은 `None`·`True`·`False` 같은 싱글턴과 작은 정수 등 런타임 전역 객체다. "모든 인턴 문자열을 불멸로"는 PEP에서 "other possibilities"로만 적혀 있고, 인턴 문자열 처리는 **패치 버전마다 다르다**.
  - 로컬 실행(`scratchpad/lang/05/e06/immortal.py`): CPython 3.12.3에서 `None`·작은 정수 5·상수 접기된 `"a"*1000`·리터럴 `"abcde"`가 모두 4294967295, 실행 중 만든 `"a"*n`은 `2`. 같은 코드를 3.12.14(`python:3.12-slim`)에서 돌리면 `None`·5는 4294967295 그대로지만 `"a"*1000`은 `4`, `"abcde"`는 `3`이었다.
  - 근거: 3.12.7 변경 기록 gh-113993 "Strings interned with sys.intern() are again garbage-collected when no longer used … Internals of the string interning mechanism have been changed." 같은 체인지로그의 Core 항목은 "`PyUnicode_InternInPlace()`로 인턴한 문자열은 여전히 불멸"이라 적지만, C API 항목("no longer prevents its argument from being garbage collected")과 3.12 C API 문서("interned strings are not 'immortal'")는 거꾸로 적는다 — 체인지로그 안에서 어긋나므로 C API 문서 쪽을 따른다([09](../09-memory-management-models/2-summary.md)와 같은 판단). 해석: 원고의 4294967295는 3.12 초기 패치에서 인턴 문자열이 불멸이었기 때문에 나온 값이고, 3.12.14와의 차이는 이 3.12.7 변경에서 왔다(3.12.4~3.12.13은 돌려 보지 않았다). 인터닝(같은 객체 재사용)과 불멸(카운트 고정)은 다른 개념이다. 참조 카운트 자체는 [09-memory-management-models](../09-memory-management-models/2-summary.md)에서 다룬다.

### 5. 기본 인자는 한 번만 평가된다 (Python)

```text
  def append_to(item, acc=[]):     ← def 문이 실행될 때 리스트 객체 하나 생성
         │                            append_to.__defaults__ = ( [] , )
  call1 ─┤ acc ──> 같은 리스트 ──> ['user_001']
  call2 ─┘ acc ──> 같은 리스트 ──> ['user_001', 'user_002']
```

- Python 언어 레퍼런스 8.7 "Function definitions": "Default parameter values are evaluated from left to right when the function definition is executed. This means that the expression is evaluated once …"
- 실험(호스트 CPython 3.12.3, `passing.py`):

```text
call1: ['user_001']
call2: ['user_001', 'user_002']
__defaults__ : (['user_001', 'user_002'],)
fixed1: ['user_001']  fixed2: ['user_002']
```

- 대처는 `acc=None` 뒤 함수 안에서 새로 만든다([languages/python/syntax/20](../../../languages/python/syntax/20-mutable-default-args/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **참조 그래프**: 객체 = 정점, 참조 = 간선인 방향 그래프([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)). 얕은 복사는 정점 1개만 새로, 깊은 복사는 도달 가능한 정점을 따라가며 새로 만든다(Python `deepcopy`처럼 함수·클래스 등은 공유로 남기는 구현이 있다).
- **깊은 복사 = 그래프 순회 + 방문 표**: DFS로 내려가며 `원본 → 사본` 해시 맵에 기록한다. Python `copy.deepcopy`의 `memo`가 이 표이고, 그래서 순환에서도 끝난다(실험 B)([algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md), [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)).
- **구조 공유**: 바뀌지 않는 부분은 참조를 공유하고 바뀐 경로만 새로 만든다. 영속 자료구조([data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md), [18](../18-functional-concepts/2-summary.md)).

## 적용 — 풀어나가는 법

1. **증상**: "어디서도 안 고쳤는데 값이 바뀌었다".
   - 원리: 두 변수가 같은 객체를 가리킨다(얕은 복사·공유 캐시·기본 인자).
   - 확인: 객체 동일성을 본다. Java는 두 참조를 `==`로 비교한다(`System.identityHashCode(o)`는 서로 다른 객체끼리 겹칠 수 있다 — 값이 다르면 확실히 다른 객체지만, 같다고 같은 객체로 확정할 수는 없다. `Object.hashCode` 계약). Python `is`(또는 동시에 살아 있는 두 객체의 `id(o)`), JS `Object.is`·디버거의 객체 ID. 같으면 공유다.
2. **증상**: 같은 값인데 비교가 거짓/참이 섞인다.
   - 원리: 동일성(`==`)과 동등성(`equals`)을 섞었다. 박싱 캐시 범위 안에서만 우연히 맞는다.
   - 확인: 정적 분석 규칙(박싱 타입 `==` 비교 경고)과 128 이상 값으로 된 테스트를 둔다.
3. **증상**: 함수가 인자를 바꿨는데 호출자에 반영이 안 된다.
   - 원리: 값에 의한 전달 — 매개변수 재할당은 호출자에게 안 보인다.
   - 대처: 새 값을 반환하고 호출자가 대입한다.
4. **설계**: 생성자·레코드에서 받은 가변 컬렉션은 방어적으로 복사한다.

```java
record Order(String id, List<String> items) {
    Order {
        items = List.copyOf(items);   // 바깥 리스트 공유를 끊고 변경 불가로. 원소가 가변 객체면 원소도 따로 복사해야 한다
    }
}
```

- `List.copyOf`는 얕다(실험 B). 원소가 불변(`String`)일 때만 이것으로 충분하다. 불변 설계는 [software-design/19](../../software-design/19-immutability-and-value-objects/2-summary.md).

## 장애 시나리오와 대처

### 1. Python 가변 기본 인자 공유 → 다른 요청의 데이터가 섞인다 (⚠ 커리큘럼)

- 현상: 응답에 이전 요청의 사용자 ID(`user_001`)가 섞여 나온다. 프로세스 재시작 직후에는 멀쩡하다.
- 보이는 형태: 리스트 길이가 요청 수만큼 커진다. `func.__defaults__`를 찍으면 누적된 리스트가 보인다.
- 원인: `def handler(…, acc=[])`의 리스트는 `def` 실행 때 한 번 만들어져 모든 호출이 공유한다(Python 레퍼런스 8.7, 실험 §5).
- 대처: `acc=None` + 함수 안에서 생성. 린터 규칙(가변 기본 인자 경고)을 CI에 둔다.

### 2. 얕은 복사본 수정 → 원본 변경 (⚠ 커리큘럼)

- 현상: 테넌트 A의 알림 설정을 바꿨더니 모든 테넌트 설정이 같이 바뀌었다.
- 보이는 형태: 바깥 객체 ID는 서로 다르지만 중첩 객체 ID가 같다(`same list? false same element? true`, 실험 B).
- 원인: 템플릿을 `new HashMap<>(template)`·`copy.copy`·`{...template}`로 복사 — 중첩 구조는 공유된다.
- 대처: 중첩까지 복사하는 생성 함수를 따로 둔다(`copy.deepcopy`, `structuredClone`, 명시적 복사 생성자). 더 나은 대처는 설정 값을 불변으로 만들어 공유해도 안전하게 하는 것이다.

### 3. `==` vs `equals` → 테스트는 통과, 운영에서 같은 ID가 다르다 (⚠ 커리큘럼)

- 현상: 권한 검사 `if (order.getUserId() == user.getId())`가 신규 사용자에게만 실패한다.
- 보이는 형태: 작은 ID(테스트 데이터 1~100)에서는 통과, 128 이상에서 거짓(실험 C).
- 원인: 두 `Long`/`Integer`를 `==`로 비교 → 동일성 비교. -128~127은 `Integer.valueOf`·`Long.valueOf`가 항상 캐시하는 범위(API 문서)라 같은 객체였고, 우연히 맞았다.
- 대처: `Objects.equals(a, b)` 또는 기본형으로 언박싱 후 비교. 테스트 데이터에 캐시 범위 밖 값을 넣는다. `-XX:AutoBoxCacheMax`로 "고치는" 것은 문제를 숨긴다(게다가 이 옵션의 설명은 `java.lang.Integer` 캐시만 말한다 — `Long`은 해당하지 않는다).

### 4. JSON 왕복으로 깊은 복사 → 타입이 바뀐다

- 현상: 복사한 주문의 `createdAt.getTime()`에서 `TypeError: … is not a function`.
- 원인: `JSON.parse(JSON.stringify(o))`가 `Date`를 문자열로 바꿨다(실험 B `JSON round-trip Date -> string`).
- 대처: `structuredClone` 사용(함수·DOM 노드 등은 `DataCloneError` — 실험 B). 또는 도메인 객체에 명시적 복사 함수를 둔다.

### 5. 매개변수 재할당으로 호출자 변경을 기대

- 현상: `normalize(list)` 안에서 `list = list.stream()…toList()`를 했는데 호출자는 정규화 전 리스트를 쓴다.
- 원인: 값에 의한 전달. 재할당은 callee의 칸만 바꾼다(실험 A `after reassign`).
- 대처: 결과를 반환하게 바꾼다. 매개변수를 `final`로 선언하면 재할당 자체가 컴파일 오류가 된다.

## 핵심 문장

- Java·JS·Python·Go·C는 값에 의한 전달만 한다. 객체는 참조가 복사되어 넘어간다.
- 그래서 받은 객체의 내부 수정은 호출자에게 보이고, 매개변수 재할당은 보이지 않는다.
- C 포인터 전달은 주소를 값으로 넘기는 것이다. 참조에 의한 전달은 C++ `&` 같은 별명이다.
- 얕은 복사는 바깥만 새로 만들고 원소는 공유한다. `List.copyOf`·스프레드·`copy.copy`가 모두 얕다.
- 동일성(`==`·`is`)과 동등성(`equals`·`==`)을 섞으면, 박싱 캐시 같은 구현 세부에 따라 결과가 바뀐다.
- Python 기본 인자는 `def` 실행 때 한 번 평가되어 모든 호출이 공유한다.

## 관련 주제·근거

- 원고: [foundations/variables-and-memory](../../foundations/variables-and-memory/README.md) §1(변수와 값 객체)·§2(얕은/깊은 복사)·§4·§5(전달 방식)·§7·§8(불변·가변 객체 실험). §3(스코프)은 [language 04](../04-semantic-analysis-and-scopes/2-summary.md), §6(참조 카운트)은 [language 09](../09-memory-management-models/2-summary.md), §9(람다)는 [07](../07-scope-closures-first-class-functions/2-summary.md)이 잇는다.
- 선행: [05-type-systems](../05-type-systems/2-summary.md)
- 후속: [07-scope-closures-first-class-functions](../07-scope-closures-first-class-functions/2-summary.md) · [18-functional-concepts](../18-functional-concepts/2-summary.md) · [09-memory-management-models](../09-memory-management-models/2-summary.md)
- 다른 영역
  - [software-design/19-immutability-and-value-objects](../../software-design/19-immutability-and-value-objects/2-summary.md) — 공유를 안전하게 만드는 설계
  - [web-platform/18-ui-rerender-and-memoization](../../web-platform/18-ui-rerender-and-memoization/2-summary.md) — 참조 동일성이 재렌더를 가른다
  - [architecture/10-calling-convention-and-stack-frame](../../architecture/10-calling-convention-and-stack-frame/2-summary.md) — 인자가 레지스터·스택에 놓이는 방식
  - 언어별: [python/03 copying](../../../languages/python/syntax/03-mutability-and-copying/2-summary.md), [java/27 equals-hashcode](../../../languages/java/syntax/27-equals-hashcode-contract/2-summary.md), [js/33 equality](../../../languages/js/syntax/33-equality-three-kinds/2-summary.md), [go/16 pointers](../../../languages/go/syntax/16-pointers-value-copy-semantics-new-and-make/2-summary.md)
- 명세·문서
  - JLS SE 21 4.1 (두 종류의 타입) · 5.1.7 Boxing Conversion · 15.21.3 Reference Equality Operators — <https://docs.oracle.com/javase/specs/jls/se21/html/jls-5.html>
  - OpenJDK 21 `src/hotspot/share/opto/c2_globals.hpp`의 `AutoBoxCacheMax` — <https://raw.githubusercontent.com/openjdk/jdk21u/master/src/hotspot/share/opto/c2_globals.hpp>
  - Python 3.12 Language Reference 8.7 Function definitions — <https://docs.python.org/3.12/reference/compound_stmts.html> · `copy` 모듈 문서 — <https://docs.python.org/3/library/copy.html>
  - PEP 683 Immortal Objects (Python-Version 3.12) — <https://peps.python.org/pep-0683/> · CPython 3.12 `Include/object.h` — <https://raw.githubusercontent.com/python/cpython/3.12/Include/object.h> · Python 3.12 변경 기록(3.12.7 gh-113993) — <https://docs.python.org/3.12/whatsnew/changelog.html>
  - Java SE 21 API `Integer.valueOf(int)`·`Long.valueOf(long)` — <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html>
  - CS2023 FPL(커리큘럼 지식 영역) [?]
- 실험 목록(모두 `scratchpad/lang/05/e06/`, 2026-10-07, 컨테이너는 `--rm --network none --cpus=2`)
  - A `Passing.java`·`passing.js`·`passing.cpp`: 전달 방식 — `eclipse-temurin:21-jdk` 21.0.12, `node:22-alpine` v22.23.2, 호스트 g++ 13.3
  - B 같은 파일 + `passing.py`: 얕은/깊은 복사 — 위 + 호스트 CPython 3.12.3
  - C `Passing.java`(기본, `-XX:AutoBoxCacheMax=1000`): 박싱 캐시·문자열 인턴
  - `immortal.py`: CPython 3.12.3(호스트) 불멸 객체 참조 카운트 — 사실 점검 때 `python:3.12-slim`(3.12.14)로도 돌려 비교
