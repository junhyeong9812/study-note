# language/05-type-systems — 타입 시스템: 정적/동적·강/약·명목/구조·제네릭·변성 — 정리 (힌트)

## 해결하는 문제

값마다 "할 수 있는 연산"이 다르다. 문자열에 나눗셈을 하거나, 주문 ID 자리에 회원 ID를 넣으면 틀린 결과가 나온다.

```text
  타입이 없으면                         타입이 있으면
  "1" + 1  → ?  (문자열? 숫자? 오류?)    규칙이 정한다: 오류 / "11" / 2 중 하나
  order(userId)  → 조용히 남의 주문      컴파일러가 막거나, 실행 중 즉시 예외
```

- *타입(type)*: 값의 집합과, 그 값에 허용된 연산의 약속.
- *타입 시스템*: 프로그램의 각 식에 타입을 붙이고, 약속을 어기는 식을 걸러 내는 규칙의 모음.
  - Pierce 『TAPL』 1장(1.1 "Types in Computer Science", 1.2 "What Type Systems Are Good For" — 목차 PDF로 확인)이 이 정의와 쓰임을 다룬다. 본문 문장은 열지 못했다.

쉬운 예: 콘센트와 플러그다.
- 모양이 안 맞으면 아예 꽂히지 않는다 → 실행 전에 막는다(정적 검사).
- 꽂은 뒤 과전류면 차단기가 내려간다 → 실행 중에 막는다(동적 검사).
- 어댑터가 알아서 모양을 바꿔 준다 → 암묵 변환(약한 타입). 편하지만 엉뚱한 기기도 꽂힌다.

똑같은 구조다.\
언어마다 "언제 막나"와 "얼마나 알아서 바꿔 주나"가 다르다. 이 차이가 운영에서 서로 다른 증상으로 나온다.

실무 예:
- 배포 후 `ClassCastException`이 났는데, 스택 트레이스가 가리키는 줄은 잘못된 값을 **넣은** 곳이 아니라 **꺼낸** 곳이다.
- `Object[]` 변수에 담긴 `String[]`에 정수를 넣었더니 `ArrayStoreException`.
- C에서 `if (n < sizeof(buf))`가 `n = -1`일 때 거짓이 되어 경계 검사가 뒤집힌다.

## 동작·원리

### 1. 두 축 — 언제 검사하나, 얼마나 알아서 바꾸나

```text
                 암묵 변환 적음(강)                 암묵 변환 많음(약)
             ┌──────────────────────────┬──────────────────────────────┐
  실행 전    │ Java, Go, Rust,          │ C (정수 승격·부호 변환)        │
  (정적)     │ TypeScript*              │                              │
             ├──────────────────────────┼──────────────────────────────┤
  실행 중    │ Python                   │ JavaScript                   │
  (동적)     │                          │ ("1" + 1 → "11")             │
             └──────────────────────────┴──────────────────────────────┘
  * TypeScript는 정적으로 검사하지만, 컴파일 결과(JS)에서 타입이 지워진다 → 실행 중에는 JS 규칙
```

- *정적 타입 검사*: 실행 전에(컴파일·타입 검사 단계) 타입 오류를 찾는다.
- *동적 타입 검사*: 값에 붙은 타입 표식을 실행 중에 보고 연산 직전에 막는다.
  - 흔한 오해: "동적 타입 = 타입이 없다". Python은 `"1" + 1`을 실행 중에 `TypeError`로 막는다. 검사 시점이 다를 뿐이다.
- *강한/약한 타입*: 문헌마다 정의가 다르다. 이 노트에서는 **암묵 변환이 얼마나 넓은가**로만 쓴다.
- 정적 검사는 **보수적**이다. 실행하면 문제없었을 프로그램도 거부할 수 있다.
  - 이유: "이 프로그램이 실행 중 어떤 성질을 갖나"를 일반적으로 정확히 판정하는 것은 결정 불가능하다(라이스 정리, [algorithm/41](../../algorithm/41-computability-and-halting/2-summary.md)). 그래서 타입 검사는 안전한 쪽으로 근사한다.

### 실험 A: 같은 식, 세 언어의 다른 답

(실험, 호스트 gcc 13.3 `-Wall -Wextra -O0` / CPython 3.12.3 / node v22.23.2(`node:22-alpine`), `scratchpad/lang/05/e05/weak.{c,py,js}`, 2026-10-07)

```text
C      : weak.c:4:11: warning: comparison of integer expressions of different signedness: 'int' and 'long unsigned int' [-Wsign-compare]
         -1 < sizeof(int): false  (n이 size_t로 변환됨)
         (size_t)-1 = 18446744073709551615
Python : "1" + 1 -> TypeError: can only concatenate str (not "int") to str
         "1" * 3 = '111'
JS     : "1" + 1 = "11"   "3" * "4" = 12   [] + {} = "[object Object]"
```

- C: `int`와 `size_t`(부호 없음)를 비교하면 C 표준의 "usual arithmetic conversions"(N1570 6.3.1.8)로 `-1`이 부호 없는 큰 수가 된다. 단 이것은 `size_t`의 변환 순위가 `int` 이상인 환경(실험한 x86-64처럼 보통의 환경)의 이야기다. `size_t`가 `int`보다 좁아 그 값을 `int`가 모두 담을 수 있는 구현이라면 반대로 `size_t` 쪽이 `int`로 바뀌어 참이 될 수 있다. 어느 쪽이든 UB가 아니라 정의된 동작이다. 결과가 직관과 반대일 뿐이다(규칙은 [languages/c/syntax/03](../../../languages/c/syntax/03-integer-promotion-and-usual-arithmetic-conversions/2-summary.md)).
- Python: 문자열과 정수의 `+`는 거부한다. 하지만 `"1" * 3`은 정의된 연산(반복)이다. 강/약은 연산마다 다르다.
- JS: `+`는 한쪽이 문자열이면 문자열 연결, `*`는 숫자로 바꾼다(규칙은 [languages/js/syntax/02](../../../languages/js/syntax/02-coercion-and-loose-equality/2-summary.md)).

### 2. 명목적 타입 vs 구조적 타입

```text
  interface Reader { String read(); }        class FileThing { String read() {...} }

  명목적(Java):  FileThing ──?──> Reader     "implements Reader"라고 선언했나? → 아니오 → 거부
  구조적(Go·TS): FileThing ──?──> Reader     read(): string 메서드가 있나?      → 예   → 허용
```

- *명목적 타입(nominal)*: 이름과 선언된 상속 관계로 호환을 정한다.
- *구조적 타입(structural)*: 멤버(메서드·필드)의 모양으로 호환을 정한다.
  - TypeScript 핸드북 "Type Compatibility": "Type compatibility in TypeScript is based on structural subtyping."
  - Go 명세 "Implementing an interface": 타입이 인터페이스의 타입 집합에 속하면 구현한다. `implements` 선언이 없다.

### 실험 B: 같은 모양, 다른 판정

(실험, `eclipse-temurin:21-jdk` 21.0.12 / `golang:1.23-alpine` go1.23.12, `scratchpad/lang/05/e05/Nominal.java`·`structural.go`, 2026-10-07)

```text
Java : Nominal.java:5: error: incompatible types: FileThing cannot be converted to Reader
Go   : go structural: data
```

- 같은 메서드를 가졌는데 Java는 거부, Go는 허용했다.
- 구조적 타입의 함정: 우연히 모양이 같은 타입이 통과한다. `{ id: string }` 모양의 회원과 주문이 서로 섞인다. 브랜드 필드나 newtype으로 막는다([software-design/24](../../software-design/24-types-as-invariants/2-summary.md)).
- TypeScript 쪽 예시는 [languages/ts/syntax/05](../../../languages/ts/syntax/05-structural-typing/2-summary.md). 이 호스트에는 `tsc`가 없어 TS 판정은 실행하지 않았다.

### 3. 제네릭과 소거 — Java는 실행 중에 타입 인자를 모른다

```text
  소스                          바이트코드 (javac)                       실행 중 객체
  List<String> names            필드 descriptor: Ljava/util/List;        ArrayList (타입 인자 없음)
                                Signature 속성: List<String> (반사용)
  String s = names.get(0);      invokeinterface List.get → Object
                                checkcast String   ← 꺼내는 곳에 삽입    여기서 CCE가 난다
  names.add(x)  (원시 타입 경유) invokeinterface List.add(Object)        검사 없음 → 오염된 채 저장
```

- *제네릭(generics)*: 타입을 인자로 받는 클래스·메서드. `List<String>`.
- *타입 소거(type erasure)*: 컴파일 뒤 타입 인자를 지우고 상한(보통 `Object`)으로 바꾸는 방식(JLS 4.6). 꺼내는 곳에 `checkcast`를 넣는다.
- *힙 오염(heap pollution)*: 매개변수화 타입의 변수가 그 타입이 아닌 객체를 가리키는 상태(JLS 4.12.2). 원시 타입(raw type)·unchecked 변환으로 생긴다.
- *Signature 속성*: 제네릭 선언 정보를 클래스 파일에 남긴다(JVMS 4.7.9). 리플렉션은 읽지만, 실행 중 검사에는 쓰이지 않는다.
- 대조(구현 방식만): C++ 템플릿·Rust 제네릭은 타입마다 코드를 따로 만든다(단형화, [17](../17-dispatch-and-polymorphism-mechanics/2-summary.md)). C# 제네릭은 실행 중에도 타입 인자를 유지한다(Microsoft 문서 "Generics in the runtime": 인스턴스화된 제네릭 클래스는 "reflection can query it at run time and both its actual type and its type parameter can be ascertained").

### 실험 C: 오염은 조용히 들어가고, 꺼낼 때 터진다

(실험, `eclipse-temurin:21-jdk` 21.0.12, `scratchpad/lang/05/e05/Erasure.java`·`Checked.java`·`Raw.java`, 2026-10-07)

```text
same class at runtime: true
size after legacyAdd = 1
get as Object ok: 42
CCE: class java.lang.Integer cannot be cast to class java.lang.String (...)
ASE: java.lang.ArrayStoreException: java.lang.Integer

javap -c (main 일부)
      76: invokeinterface #60,  2   // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;   ← Object로 받음: 검사 없음
     101: invokeinterface #60,  2   // InterfaceMethod java/util/List.get:(I)Ljava/lang/Object;
     106: checkcast     #65         // class java/lang/String                                 ← 여기서 실패
javap -v
  static java.util.List<java.lang.String> names;
    descriptor: Ljava/util/List;
    Signature: #83                  // Ljava/util/List<Ljava/lang/String;>;

Collections.checkedList 로 감싸면:
넣는 순간 CCE: Attempt to insert class java.lang.Integer element into collection with element type class java.lang.String
  at Checked.legacyAdd(Checked.java:4)

javac -Xlint:unchecked Raw.java:
Raw.java:3: warning: [unchecked] unchecked call to add(E) as a member of the raw type List
```

- `List<String>`과 `List<Integer>`는 실행 중 같은 클래스다. 소거의 직접 증거다.
- 정수 42가 `List<String>` 안에 들어갔다. `Object`로 꺼내면 아무 일도 없다. `String`으로 꺼낼 때 비로소 `checkcast`가 실패한다.
- **원인 위치(넣은 곳)와 증상 위치(꺼낸 곳)가 다르다.** 운영에서 CCE 스택 트레이스만 보고 꺼낸 쪽을 고치면 헛수고가 된다.
- `Collections.checkedList`는 넣는 순간 검사한다. 원인 위치를 찾을 때 임시로 감싸 볼 수 있다. 단 감싼 뒤의 모든 삽입이 이 뷰를 거칠 때만 보장된다 — 원래 리스트 참조로 넣으면 우회되고, 감싸기 전에 들어 있던 원소는 검사하지 않는다(Java SE 21 API `Collections.checkedList`).

### 4. 변성 — 배열은 공변, 제네릭은 무공변

```text
  String <: Object 일 때
  배열     String[]      <: Object[]        공변   → 쓰기를 실행 중에 검사 (ArrayStoreException)
  제네릭   List<String>  ≮: List<Object>     무공변 → 컴파일 오류
           List<String>  <: List<? extends Object>   주로 읽기용으로 공변 (생산자)
           List<Object>  <: List<? super String>     주로 쓰기용으로 반공변 (소비자)
```

- *변성(variance)*: `A <: B`일 때 `F<A>`와 `F<B>` 사이의 관계.
  - *공변(covariant)*: 같은 방향(`F<A> <: F<B>`). *반공변(contravariant)*: 반대 방향. *무공변(invariant)*: 관계 없음.
- 왜 배열 공변이 위험한가: `Object[]`로 보면 정수를 넣을 수 있어 보인다. 실제 배열은 `String[]`이다. 그래서 JVM이 배열 원소 저장마다 실제 원소 타입을 검사한다(JLS 10.5).
- 가변 컬렉션을 공변으로 두면 타입 안전이 깨진다. 배열은 그 구멍을 실행 중 저장 검사로 메운다. Java 제네릭은 소거 때문에 그 검사마저 할 수 없어, 컴파일 시점에 무공변으로 막는다.
  - 소거만이 이유는 아니다: 실행 중 타입 인자를 유지하는 C#에서도 `List<T>`는 무공변이다(Microsoft Learn "Variance in Generic Interfaces": "you cannot implicitly convert `List<String>` to `List<Object>`").

```text
(실험 C와 같은 환경, Variance.java / Variance2.java)
Variance.java:4: error: incompatible types: ArrayList<String> cannot be converted to List<Object>
sum(extends) = 7.0
fill(super) = [1, 2]
```

- `? extends Number`는 원소를 `Number`로 읽을 수 있지만 새 값을 넣을 수 없다. `? super Integer`는 `Integer`를 넣을 수 있지만 꺼낸 값은 `Object`로만 보장된다. 엄밀한 읽기·쓰기 전용은 아니다 — `? extends` 리스트에도 `null`을 넣거나 `clear()`를 부를 수 있다(Oracle Java 튜토리얼 "Wildcard Guidelines")("PECS" — 문법 세부는 [languages/java/syntax/18](../../../languages/java/syntax/18-wildcards-pecs/2-summary.md)).
- TypeScript는 메서드 매개변수를 양방향(bivariant)으로 허용하는 예외가 있다. `strictFunctionTypes`를 켜도 함수 문법에만 적용되고 메서드 문법에는 적용되지 않는다(TS tsconfig 문서 `strictFunctionTypes`, [languages/ts/syntax/17](../../../languages/ts/syntax/17-variance-and-parameter-compatibility/2-summary.md)).

### 5. 타입 추론 = 방정식 풀기(단일화)

```text
  식:  \x. add x 1          add : int -> int -> int

  ① 모르는 타입에 변수를 붙인다      x : t1,  (add x) : t2,  (add x 1) : t3
  ② 쓰임에서 방정식을 만든다        int -> int -> int  =  t1 -> t2
                                    t2                 =  int -> t3
  ③ 단일화로 푼다                   t1 := int,  t2 := int -> int,  t3 := int
  ④ 결과                            \x. add x 1 : int -> int
```

- *타입 추론*: 선언하지 않은 타입을 쓰임에서 계산하는 것.
- *단일화(unification)*: 두 타입 식을 같게 만드는 변수 대입을 찾는 알고리즘. 구조가 다르면(int vs bool) 실패한다.
- *occurs check*: `t = t -> u`처럼 변수가 자기 자신을 포함하는 방정식은 무한 타입이라 거부한다.
- *let 다형성*: `let id = \x.x`처럼 묶은 이름은 쓸 때마다 새 변수로 복사(인스턴스화)해 여러 타입으로 쓴다. 람다 매개변수는 그렇지 않다.
- 이 방식(Hindley–Milner, 알고리즘 W)은 TAPL 22장 "Type Reconstruction"이 다룬다(목차로 확인).

### 실험 D: 50줄짜리 추론기

(실험, CPython 3.12.3 표준 라이브러리, `scratchpad/lang/05/e05/infer.py`, 2026-10-07)

```text
\x. x                        : a -> a
\x. add x 1                  : int -> int
    단일화 과정: t1 := int; t2 := int -> int; t3 := int
\f. \x. f (f x)              : (a -> a) -> a -> a
let id = \x.x in id id       : a -> a
(\id. id id) (\x.x)          : 타입 오류 — occurs check: t12 = t12 -> t13 (무한 타입)
\x. if x then 1 else 2       : bool -> int
add 1 true                   : 타입 오류 — mismatch: int vs bool
```

- `id id`는 `let`으로 묶으면 통과하고, 람다 매개변수로 받으면 occurs check에 걸린다. let 다형성의 차이다.
- Java의 `var`는 이 수준의 추론이 아니다. 초기화 식을 단독 식으로 보고 그 타입을 구한 뒤, 캡처 변수 같은 합성 타입 변수가 들어 있으면 상향 투영(upward projection)한 타입을 지역 변수 타입으로 쓴다(JLS 14.4.1, [languages/java/syntax/04](../../../languages/java/syntax/04-var-type-inference/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **단일화(unification)**: 타입 식(트리) 두 개를 동시에 내려가며 변수 대입을 만든다.
  - 대입 맵 = 해시 맵([data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)). 실험 D의 `prune`은 대입 사슬을 끝까지 따라간다.
  - 큰 구현에서는 같은 타입이 된 변수들을 **union-find**로 묶는다([data-structure/14-union-find](../../data-structure/14-union-find/2-summary.md)). `prune`이 union-find의 `find`, 대입이 `union`에 해당한다.
- **occurs check**: 타입 트리를 깊이 우선으로 훑어 변수가 들어 있나 본다([algorithm/12-dfs](../../algorithm/12-dfs/2-summary.md)).
- **부분 타입 관계**: Java의 클래스·인터페이스처럼 선언으로 정하는 명목적 부분 타입은 상속 그래프의 도달 가능성으로 볼 수 있다. 구조적 호환(TS)·배열 부분 타입(JLS 4.10.3)은 상속 경로 없이 언어별 규칙으로 정한다([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).
- **스코프별 환경**: 이름 → 타입 맵의 스택(심벌 테이블, [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md)).

## 적용 — 풀어나가는 법

1. **증상**: `ClassCastException`이 났다.
   - 원리: 소거된 제네릭은 꺼낼 때 `checkcast`한다. 원인은 넣은 곳일 수 있다.
   - 확인: 스택 트레이스의 줄이 `get`·반복문·람다 안이면 힙 오염을 의심한다. `javac -Xlint:unchecked`로 원시 타입·unchecked 경고 위치를 모두 본다. 의심 컬렉션을 `Collections.checkedList(…, String.class)`로 감싸 넣는 순간 잡는다.
2. **증상**: `ArrayStoreException`.
   - 원리: 배열은 공변이고 쓰기를 실행 중에 검사한다.
   - 확인: 배열을 `Object[]`·상위 타입 배열로 넘기는 곳을 찾는다. 대처는 `List<T>`(무공변) 사용.
3. **증상**: 역직렬화한 컬렉션에서 `LinkedHashMap cannot be cast to …` 같은 CCE(흔한 형태, 예시).
   - 원리: 소거 때문에 `List.class`만 넘기면 라이브러리는 원소 타입을 모른다. 그래서 기본 표현(맵)으로 채운다.
   - 대처: 원소 타입을 담은 타입 토큰을 넘긴다(라이브러리별 방법은 그 문서 확인). 받은 직후 경계에서 한 번 검증한다.
4. **증상**: TypeScript는 통과했는데 실행 중 `undefined` 접근.
   - 원리: TS 타입은 컴파일 뒤 지워진다([languages/ts/syntax/01](../../../languages/ts/syntax/01-what-ts-adds-and-erases/2-summary.md)). 외부 JSON에는 검사가 없다.
   - 대처: 신뢰 경계에서 런타임 검증(스키마 파서). `as` 단언은 검사가 아니다.
5. **증상**: C 경계 검사가 음수 입력에서 뒤집히거나 뚫린다(시나리오 4).
   - 확인: `gcc -Wall -Wextra`(`-Wsign-compare`)·`clang -Wsign-compare` 경고를 오류로 다룬다.

```java
// 소거된 제네릭을 쓸 때의 방어 — 경계에서 한 번, 실행 중 타입을 남긴다
static <T> List<T> castAll(List<?> raw, Class<T> type) {
    List<T> out = new ArrayList<>(raw.size());
    for (Object o : raw) out.add(type.cast(o));   // 여기서 바로 실패 → 원인 위치가 곧 증상 위치
    return List.copyOf(out);
}
```

## 장애 시나리오와 대처

### 1. 제네릭 소거 + 원시 타입 → 엉뚱한 곳의 `ClassCastException` (⚠ 커리큘럼)

- 현상: 정산 배치가 특정 고객 데이터에서만 죽는다.
- 보이는 형태: `java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String`. 스택은 집계 루프(`for (String s : names)`)를 가리킨다.
- 원인: 오래된 모듈이 원시 타입 `List`로 정수를 넣었다. 컴파일러는 unchecked 경고만 냈고, 실행 중 검사는 꺼낼 때까지 없다(실험 C).
- 대처: `-Xlint:unchecked` 경고를 0으로 만든다(CI에서 `-Werror`). 넣는 쪽을 찾을 때까지 `Collections.checkedList`로 감싼다.

### 2. 제네릭 소거로 실행 중 타입 정보가 없다 (⚠ 커리큘럼)

- 현상: `if (obj instanceof List<String>)`가 컴파일되지 않거나, `new T[]`·`T.class`를 쓸 수 없다. 역직렬화가 원소 타입을 잃는다.
- 보이는 형태: 컴파일 오류, 또는 실행 중 맵이 담긴 리스트(시나리오 위 적용 3).
- 원인: JLS 4.6·4.7 — 소거된 매개변수화 타입은 실행 중 구별할 수 없다(reifiable하지 않다).
- 대처: `Class<T>`·타입 토큰을 명시적으로 넘긴다. 필요한 정보는 `Signature` 속성에서 리플렉션으로 읽을 수 있지만, 그것은 선언 정보이지 객체의 실제 내용이 아니다.

### 3. 공변 배열 → `ArrayStoreException` (⚠ 커리큘럼)

- 현상: 공용 유틸이 `Object[]`를 받아 기본값으로 채우다가 죽는다.
- 보이는 형태: `java.lang.ArrayStoreException: java.lang.Integer`(실험 C).
- 원인: 호출자가 `String[]`을 넘겼다. 배열은 공변이라 컴파일은 통과하고, JVM이 저장 순간 검사한다(JLS 10.5).
- 대처: 공용 API는 배열 대신 `List<? super T>`를 받는다. 컴파일 시점에 막힌다.

### 4. 암묵 변환 → 조용히 틀린 비교

- 현상: 길이 검사가 음수 길이 입력에서 엉뚱하게 동작한다. `if (n < sizeof(buf))`는 `n = -1`에서 거짓이 되어 의도와 반대로 갈린다(실험 A). 반대로 `int` 상수와 비교하는 검사(`if (n < BUF_LEN)`)는 `-1`을 통과시킨다. 그 뒤 `memcpy(dst, src, n)`처럼 `size_t` 매개변수로 넘기면 `n`이 큰 수로 바뀌어 버퍼 밖 접근(UB)으로 이어질 수 있다.
- 보이는 형태: 경고 `-Wsign-compare`(무시된 상태), 크래시 또는 잘못된 데이터.
- 원인: 부호 있는 값과 `size_t`가 만나는 곳(비교·인자 전달)에서 `-1`이 `18446744073709551615`로 변환(실험 A, x86-64).
- 대처: 경고를 오류로. 길이는 처음부터 부호 없는 타입으로 받고, 외부 입력은 범위를 먼저 검사한다. 메모리 안전 쪽 결과는 [20-undefined-behavior-and-memory-safety](../20-undefined-behavior-and-memory-safety/2-summary.md).

### 5. 동적 타입 언어의 드문 경로

- 현상: Python 서비스가 몇 주 만에 한 번 오는 요청에서 `TypeError`·`AttributeError`.
- 원인: 동적 검사는 그 줄이 **실행될 때만** 한다. 테스트가 그 분기를 지나지 않았다.
- 대처: 타입 힌트 + 정적 검사기(예: mypy — 이 호스트에는 설치하지 않아 실행하지 않았다)를 CI에 넣고, 경계에서 런타임 검증을 한다.

## 핵심 문장

- 타입 시스템은 "언제 검사하나(정적/동적)"와 "얼마나 알아서 바꾸나(강/약)"의 두 축으로 나눠 본다.
- 명목적 타입은 선언된 이름으로, 구조적 타입은 멤버의 모양으로 호환을 정한다.
- Java 제네릭은 소거된다. 실행 중 `List<String>`과 `List<Integer>`는 같은 클래스이고, 검사는 꺼낼 때 넣은 `checkcast`가 한다.
- 그래서 힙 오염의 증상(CCE)은 원인(넣은 곳)과 다른 줄에서 나온다.
- 배열은 공변이라 저장마다 실행 중 검사하고, 제네릭은 무공변이라 컴파일 시점에 막는다.
- Hindley–Milner식 타입 추론은 쓰임에서 방정식을 세우고 단일화로 푸는 일이다(Java `var`는 JLS 14.4.1의 별도 규칙).

## 관련 주제·근거

- 선행
  - [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md) — 타입 검사가 들어가는 의미 분석 단계
- 후속
  - [06-values-references-passing](../06-values-references-passing/2-summary.md) · [08-error-handling-models](../08-error-handling-models/2-summary.md)(합 타입) · [17-dispatch-and-polymorphism-mechanics](../17-dispatch-and-polymorphism-mechanics/2-summary.md)(단형화 vs 소거)
- 다른 영역
  - [software-design/24-types-as-invariants](../../software-design/24-types-as-invariants/2-summary.md) — 타입으로 불법 상태 막기(설계 쪽)
  - [algorithm/41-computability-and-halting](../../algorithm/41-computability-and-halting/2-summary.md) — 정적 검사가 근사인 이유
  - 언어별 문법: [java/19 type-erasure](../../../languages/java/syntax/19-type-erasure/2-summary.md), [java/18 wildcards](../../../languages/java/syntax/18-wildcards-pecs/2-summary.md), [ts/05 structural](../../../languages/ts/syntax/05-structural-typing/2-summary.md), [ts/17 variance](../../../languages/ts/syntax/17-variance-and-parameter-compatibility/2-summary.md), [go/20 interface](../../../languages/go/syntax/20-interface-declaration-and-implicit-implementation/2-summary.md)
- 명세·문서
  - JLS SE 21 4.6 Type Erasure · 4.7 Reifiable Types · 4.10 Subtyping · 4.12.2 (heap pollution) · 10.5 Array Store Exception — <https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html>, <https://docs.oracle.com/javase/specs/jls/se21/html/jls-10.html>
  - JVMS SE 21 4.7.9 The Signature Attribute — <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html>
  - TypeScript Handbook "Type Compatibility" — <https://www.typescriptlang.org/docs/handbook/type-compatibility.html> · tsconfig `strictFunctionTypes` — <https://www.typescriptlang.org/tsconfig/strictFunctionTypes.html>
  - Microsoft Learn "Generics in the runtime (C# programming guide)" — <https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/generics/generics-in-the-run-time> · "Variance in Generic Interfaces (C#)" — <https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/covariance-contravariance/variance-in-generic-interfaces>
  - The Go Programming Language Specification, "Interface types" — <https://go.dev/ref/spec>
  - Pierce, 『Types and Programming Languages』, 1장·15장(Subtyping)·22장(Type Reconstruction) — 목차 PDF <https://www.cis.upenn.edu/~bcpierce/tapl/contents.pdf>(본문 미열람)
- 실험 목록(모두 `scratchpad/lang/05/e05/`, 2026-10-07, 컨테이너는 `--rm --network none --cpus=2`)
  - A `weak.c`·`weak.py`·`weak.js`: 암묵 변환 비교 — 호스트 gcc 13.3, CPython 3.12.3, `node:22-alpine`(v22.23.2)
  - B `Nominal.java`·`structural.go`: 명목 vs 구조 — `eclipse-temurin:21-jdk`(21.0.12), `golang:1.23-alpine`(go1.23.12)
  - C `Erasure.java`·`Checked.java`·`Raw.java`·`Variance*.java`: 소거·힙 오염·`javap`·공변 배열·와일드카드 — `eclipse-temurin:21-jdk`
  - D `infer.py`: 알고리즘 W 축소판 — 호스트 CPython 3.12.3
