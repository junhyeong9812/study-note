# language/17-dispatch-and-polymorphism-mechanics — 디스패치: 정적/동적, vtable, 단형화, 인라인 캐시 — 정리 (힌트)

## 해결하는 문제

`shape.area()` 한 줄이 **어느 구현**을 실행할지 누군가 정해야 한다. 언제(컴파일/실행), 무엇을 보고(선언 타입/실제 타입), 얼마의 비용으로 정하나가 이 주제다.

```text
  Shape s = pick();          컴파일러가 아는 것: s는 Shape
  s.area();                  실행 중에야 아는 것: s는 Circle? Square? …
                             → 실행 중 "실제 타입의 area"를 찾아가는 장치가 필요
```

- *디스패치(dispatch)*: 호출 지점에서 실행할 메서드 구현을 고르는 일.
- *정적 디스패치*: 컴파일 시점에 고른다. 오버로딩, `static`·`private`·`final` 메서드.
- *동적 디스패치*: 실행 시점에 수신 객체의 실제 타입으로 고른다. 오버라이딩.

쉬운 예: 콜센터 연결이다.
- 내선 번호를 알고 직통으로 건다 → 정적 디스패치.
- 안내원이 고객 등급을 보고 담당 부서로 돌린다 → 동적 디스패치(vtable 조회).
- 안내원이 "이 번호는 지난번에도 VIP였다"는 메모를 보고 바로 연결한다. 메모가 틀리면 다시 확인한다 → 인라인 캐시.
- 고객 등급이 수십 종류면 메모가 소용없어 매번 표를 찾는다 → 메가모픽 호출.

똑같은 구조다.\
"무엇을 보고 고르나"를 착각하면 **엉뚱한 메서드**가 불리고, "몇 종류가 오나"에 따라 **같은 코드의 속도**가 몇 배 달라진다.

실무 예:
- `equals(UserId other)`를 만들었는데 `HashSet.contains`가 거짓을 낸다(오버라이딩이 아니라 오버로딩).
- `List<Integer>`에서 `list.remove(1)`이 값 1이 아니라 1번 인덱스를 지운다.
- 인터페이스 구현을 하나 더 추가했을 뿐인데 핫 루프가 느려진다.

상속·다형성의 개념과 "필드·`static`은 다형적이지 않다" 실험은 [software-design/20](../../software-design/20-oop-fundamentals/2-summary.md)에 있다. 이 노트는 그 아래의 **메커니즘과 비용**을 다룬다.

## 동작·원리

### 1. 두 단계 — 컴파일러는 서명을, 런타임은 구현을 고른다

```text
  소스                    컴파일 시점 (javac, JLS 15.12.2)          실행 시점 (JVM, JVMS 5.4.6)
  f(o)  // Object o       인자의 '선언 타입'으로 오버로드 선택        invokestatic f(Object) — 고정
                          → f(Object)
  a.speak() // Animal a   서명 Animal.speak() 선택                  invokevirtual → 수신 객체의 실제
                                                                    클래스에서 구현 선택 → Dog.speak
```

- *오버로딩(overloading)*: 같은 이름, 다른 매개변수 목록. **컴파일 시점에 인자 식의 정적 타입으로** 고른다(JLS 15.12.2 — 변수면 선언 타입이고, 람다 같은 다형 식은 목표 타입도 본다).
- *오버라이딩(overriding)*: 하위 클래스가 같은 서명의 인스턴스 메서드를 다시 구현(JLS 8.4.8.1). **실행 시점에 수신 객체의 실제 타입으로** 고른다(JVMS 5.4.6 Method Selection).
- 동적 디스패치는 **수신 객체 하나**에만 적용된다. 인자의 실제 타입은 보지 않는다(단일 디스패치). 인자 타입까지 실행 중에 보려면 방문자 패턴 같은 이중 디스패치가 필요하다([software-design/27](../../software-design/27-design-patterns-gof/2-summary.md)).

### 실험 A: 무엇을 보고 고르나

(실험, `eclipse-temurin:21-jdk` 21.0.12, `scratchpad/lang/05/e17/Overload.java`·`OverrideCheck.java`·`Remove.java`, 2026-10-07)

```text
f(o) with Object o = "hello" : f(Object)          ← 실제는 String이지만 선언 타입 Object로 선택
f((String) o)                  : f(String)
greet(a) with Animal a = Dog   : greet(Animal)->멍  ← 오버로드는 정적(Animal), speak는 동적(Dog)
probe.equals(probe-copy) direct : true            ← equals(UserId)를 직접 부르면 참
HashSet.contains(probe)         : false           ← HashSet은 equals(Object)를 부른다
asObj.equals(...)               : false
remove(1)                 -> [10, 1]              ← List.of(10, 20, 1)에서 인덱스 1(값 20) 삭제
remove(Integer.valueOf(1)) -> [10, 20]
javap -c
       7: invokestatic  #33   // Method f:(Ljava/lang/Object;)Ljava/lang/String;
      48: invokestatic  #52   // Method greet:(LOverload$Animal;)Ljava/lang/String;
      27: invokeinterface #24,  2   // InterfaceMethod java/util/List.remove:(I)Ljava/lang/Object;
      78: invokeinterface #49,  2   // InterfaceMethod java/util/List.remove:(Ljava/lang/Object;)Z
OverrideCheck.java:4: error: method does not override or implement a method from a supertype
```

- 바이트코드에 고른 서명이 **박혀 있다**. 실행 중에는 바뀌지 않는다.
- `equals(UserId)`는 `Object.equals(Object)`를 재정의하지 않고 **새 오버로드**를 만들었다. `HashSet.contains`는 `HashMap.getNode`에서 `key.equals(k)`를 `Object` 서명으로 부르므로 `Object.equals`(동일성)가 실행됐다. 단 실험의 `UserId`는 `hashCode`를 값으로 재정의해 같은 버킷을 찾았기 때문에 `equals`까지 갔다(OpenJDK 21 `HashMap.java`). `hashCode`도 재정의하지 않았다면 해시가 달라 `equals` 호출 전에 못 찾는다 — 어느 쪽이든 `equals(UserId)`는 쓰이지 않는다. `@Override`를 붙이면 컴파일 오류로 잡힌다.
- `remove(1)`: JLS 15.12.2의 1단계(strict invocation — 박싱 없이 맞는 메서드)에서 `remove(int)`가 맞는다. 박싱이 필요한 `remove(Object)`는 2단계라 후보가 되기 전에 결정됐다.

### 2. vtable — 동적 디스패치의 기본 장치

```text
  객체 Dog                  클래스 Dog의 vtable (개념도 — 슬롯 번호는 예시)
  ┌────────────┐            슬롯 0: toString → Object.toString
  │ header ────┼──> klass   슬롯 1: equals   → Object.equals
  │ fields…    │            슬롯 2: hashCode → Object.hashCode
  └────────────┘            슬롯 3: speak    → Dog.speak      ← Animal의 같은 슬롯을 덮어씀

  a.speak()  =  ① 객체 헤더에서 클래스 읽기  ② 슬롯 3 읽기  ③ 그 구현으로 간접 호출
```

- 슬롯 번호는 설명용이다. HotSpot의 `Object`에는 `clone`·`finalize`처럼 재정의 가능한 메서드가 더 있어 실제 배치는 다르다(OpenJDK 21 `Object.java`).
- 칸에 든 것도 구현마다 다르다. C++(실험 B)의 vtable 칸은 함수 주소다. HotSpot의 `vtableEntry`는 `Method*`(메서드 메타데이터)를 담고, 실행 진입점은 그 `Method`에서 얻는다(OpenJDK 21 `klassVtable.hpp`의 `Method* _method`).

- *vtable(virtual method table)*: 클래스마다 둔 "가상 메서드 → 구현(C++은 함수 주소, HotSpot은 `Method*`)" 배열. 하위 클래스는 상위의 배열을 복사하고 재정의한 슬롯만 바꾼다. 그래서 슬롯 번호는 컴파일·링크 시점에 정해진다.
- *itable*: 인터페이스 메서드용 표. 한 클래스가 여러 인터페이스를 구현하므로 고정 슬롯이 아니라 인터페이스별 표를 찾는 단계가 더 있다.
  - HotSpot은 이 둘을 `klassVtable`·`klassItable`로 구현한다(OpenJDK 21 `src/hotspot/share/oops/klassVtable.hpp`: "A klassVtable abstracts the variable-length vtable that is embedded in InstanceKlass and ArrayKlass").
- *간접 호출(indirect call)*: 주소를 메모리에서 읽어 그곳으로 뛰는 호출. CPU는 목적지를 예측해야 한다([architecture/18](../../architecture/18-pipelining-and-branch-prediction/2-summary.md)).

### 실험 B: C++ 가상 호출의 기계어

(실험, 호스트 g++ 13.3 `-std=c++17 -O2 -c`, `objdump -d -C`, `scratchpad/lang/05/e17/vt.cpp`, 2026-10-07)

```text
-O2 -fno-devirtualize-speculatively
call_virtual(Shape const&):
   4:  mov    (%rdi),%rax        ← 객체 첫 8바이트 = vtable 포인터
   7:  jmp    *(%rax)            ← 슬롯 0의 주소로 간접 점프(꼬리 호출)

-O2 (기본)
call_virtual(Shape const&):
   4:  mov    (%rdi),%rax
   7:  lea    0x0(%rip),%rdx     ← Sq::area의 주소(재배치 전)
   e:  mov    (%rax),%rax
  11:  cmp    %rdx,%rax          ← "슬롯이 Sq::area인가?"
  14:  jne    20
  16:  mov    0x8(%rdi),%eax     ← 맞으면 Sq::area 본문을 인라인: s * s
  19:  imul   %eax,%eax
  1c:  ret
  20:  jmp    *%rax              ← 아니면 간접 점프

call_final(Sq const&):           ← final 클래스: 대상이 확정 → 간접 호출 없음
  34:  mov    0x8(%rdi),%eax
  37:  imul   %eax,%eax
```

- 기본 `-O2`에서 gcc는 "아마 `Sq`일 것"이라 추측해 비교 + 인라인을 넣었다. GCC 13.3 문서의 `-fdevirtualize-speculatively`: "Attempt to convert calls to virtual functions to speculative direct calls … change the call into a conditional deciding between direct and indirect calls." 이 옵션은 `-O2`에서 켜진다.
- 이 파일에서 `Shape`의 구현은 `Sq` 하나뿐이라 추측 대상이 하나였다.
- `final`은 "더 하위 클래스가 없다"는 약속이라 컴파일러가 바로 직접 호출(여기서는 인라인)로 바꿨다.

### 3. 단형화 — 타입마다 코드를 따로 만든다

```text
  template <class T> int twice(const T& x) { return 2 * x.area(); }

  twice<Circle>  →  별도 함수: mov (%rdi),%eax; imul; lea; add    (Circle::area 인라인)
  twice<Rect>    →  별도 함수: mov (%rdi),%eax; imul 0x4(%rdi)    (Rect::area 인라인)
  nm: W int twice<Rect>(Rect const&)   W int twice<Circle>(Circle const&)
```

- *단형화(monomorphization)*: 제네릭 코드를 쓰인 타입마다 복제해 컴파일하는 방식. 타입 인자로 정해지는 호출 대상이 컴파일 시점에 확정되어 그 부분의 간접 호출이 없고 인라인이 쉽다(단 `T=Base`처럼 인스턴스화해 본문에서 `Base`의 가상 함수를 부르면 그 호출은 여전히 동적 바인딩이다). 대신 코드 크기가 커진다.
- C++ 템플릿·Rust 제네릭(`impl Trait`·`<T: Trait>`)이 이 방식이다. Rust `dyn Trait`은 vtable 방식이다([languages/rust/syntax/31](../../../languages/rust/syntax/31-generics-trait-bounds-where-and-monomorphization/2-summary.md), [33](../../../languages/rust/syntax/33-dyn-trait-objects-and-object-safety/2-summary.md)).
- Java 제네릭은 소거되어 코드가 하나뿐이다. 그래서 `T`의 메서드 호출은 인터페이스·가상 호출로 남는다([05](../05-type-systems/2-summary.md)). 대신 JIT가 실행 중 관찰한 타입으로 아래의 인라인 캐시를 쓴다.
- 실험 B와 같은 환경의 `objdump`·`nm` 출력이다.

### 4. 인라인 캐시와 타입 프로파일 — JIT가 "지금까지 본 타입"에 거는 내기

```text
  호출 지점 s.area() 의 상태 (HotSpot compiledIC.hpp 주석의 상태 전이)

        Clean ──(처음 호출)──> Monomorphic (Klass* 하나 기억)
                                  │  수신 클래스가 다르면(캐시 미스)
                                  ▼
                              Megamorphic (vtable/itable 조회 스텁)

  C2 컴파일 시 타입 프로파일에 따라
  본 타입 1개  → if (klass == S0) { S0.area 인라인 } else { 역최적화 }
  본 타입 2개  → if (S0) {…} else if (S1) {…} else {…}          (UseBimorphicInlining)
  3개 이상     → 한 타입이 90% 이상이면 그 타입만 인라인 + 나머지는 가상 호출
                 (TypeProfileMajorReceiverPercent), 고르게 섞이면 가상 호출(인라인 없음)
```

- *인라인 캐시(inline cache)*: 호출 지점마다 "지난번 수신 클래스와 그 구현 주소"를 기억해, 같은 클래스면 표 조회 없이 바로 부르는 장치.
  - OpenJDK 21 `compiledIC.hpp` 주석: "The CompiledIC represents a compiled inline cache." 상태 전이 그림에 Clean → Monomorphic → Megamorphic가 있고 "[4]: Inline cache miss. We go directly to megamorphic call."
- *단형(monomorphic)·이형(bimorphic)·메가모픽(megamorphic)*: C2 타입 프로파일 기준으로 한 호출 지점이 본 수신 타입이 1개·2개·많음.
  - 흔한 오해: 위 그림의 compiled IC 상태와 같은 분류라는 것. compiled IC는 단형에서 캐시 미스가 한 번 나면(두 번째 클래스) 바로 Megamorphic 스텁으로 간다("[4]"). 또 이미 쓰던 IC도 `set_to_clean`으로 Clean으로 되돌릴 수 있다(OpenJDK 21 `compiledIC.cpp`).
- C2 플래그(OpenJDK 21 `c2_globals.hpp`): `UseBimorphicInlining`(기본 `true`, "Profiling based inlining for two receivers"), `TypeProfileMajorReceiverPercent`(기본 90, "% of major receiver type to all profiled receivers"). 호출 지점마다 기록하는 수신 타입 수는 `TypeProfileWidth`(기본 2, `runtime/globals.hpp`)다.
  - `opto/doCall.cpp`의 판단: 주 수신 타입이 90% 이상(`have_major_receiver`)이거나, 본 타입이 1개이거나, 2개이고 `UseBimorphicInlining`이면 타입 검사 + 인라인을 시도한다. 그래서 "3개 이상이면 무조건 가상 호출"은 아니다. 실험 C처럼 고르게 섞이면 가상 호출로 남는다.
- 핵심: 인라인되면 호출 자체가 사라지고 그 뒤 최적화(상수 접기·탈출 분석)가 이어진다. 메가모픽이면 그 사슬이 끊긴다. 계층 컴파일과 역최적화 자체는 [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md).

### 실험 C: 수신 타입 1·2·4·8종류

(실험, `eclipse-temurin:21-jdk` 21.0.12, `-Xmx512m`, `--cpus=2`, `scratchpad/lang/05/e17/Megamorphic.java`, 2²⁰개 배열을 50회 워밍업 후 20회 측정, 종류마다 별도 JVM 3회, JMH 아님, 2026-10-07)

```text
kinds=1  ns/call  min=0.70~0.87  max=0.78~1.06
kinds=2  ns/call  min=1.19~1.46  max=1.63~1.64
kinds=4  ns/call  min=10.01~11.62  max=13.46~13.58
kinds=8  ns/call  min=9.95~11.83  max=12.74~17.72

사실 점검 재실행(같은 조건, 종류마다 JVM 3회)
kinds=1  min=0.67~0.93   kinds=2  min=1.06~1.28
kinds=4  min=9.32~17.00  (3회 중 1회만 17.00 — 나머지 9.32·9.66)
kinds=8  min=9.50~10.55

-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining (area 호출 지점 @ 27)
kinds=1  Megamorphic$S0::area (2 bytes)   inline (hot)
kinds=2  Megamorphic$S0::area (2 bytes)   inline (hot)
         Megamorphic$S1::area (2 bytes)   inline (hot)
kinds=4  Megamorphic$Shape::area (0 bytes)   virtual call
kinds=8  Megamorphic$Shape::area (0 bytes)   virtual call      (재실행에서 확인)
```

- 1·2종류에서는 구현이 인라인됐고(`inline (hot)`), 4종류부터 `virtual call`로 남았다. 같은 지점에서 비용이 약 10배 뛰었다(재실행에서도 같은 경향, 한 번은 약 15배).
- 4와 8의 차이는 작았다(재실행 한 번의 4종류 17.00ns는 같은 조건의 다른 실행과 크게 달라 이상치로 본다). 메가모픽이 되면 종류 수보다 "인라인이 끊겼다"가 비용을 정한다(해석).
- 원인 로그(`PrintInlining`)로 인라인 여부를 확인했다. ns 값의 절대 크기는 이 호스트·이 루프 모양에 한정된다. 측정 방법론은 [reliability/38](../../reliability/38-microbenchmarking/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **vtable = 슬롯 번호로 찾는 배열**(C++은 함수 포인터, HotSpot은 `Method*`): 슬롯 번호로 O(1) 조회. 상속 = 상위 배열 복사 + 재정의 슬롯 교체. C에서 손으로 만드는 같은 구조는 [languages/c/syntax/35](../../../languages/c/syntax/35-function-pointers-and-callback-tables/2-summary.md).
- **itable**: 인터페이스 → 메서드 표의 2단계 조회. 인터페이스 호출이 가상 호출보다 한 단계 더 든다.
- **인라인 캐시 = 크기 1(또는 소수)의 캐시**: 키 = 수신 클래스, 값 = 구현 주소. 미스가 나면 더 일반적인 조회로 내려간다. 캐시 일반은 [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md).
- **타입 프로파일**: 호출 지점별 "수신 클래스 → 횟수" 히스토그램. C2가 이를 보고 인라인 여부를 정한다.
- **클래스 계층 그래프**: 오버라이딩 관계와 `final` 판정은 상속 트리 위의 질의다([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).

## 적용 — 풀어나가는 법

1. **증상**: 같은 객체로 보이는데 `HashSet`·`HashMap`·`contains`가 못 찾는다.
   - 원리: `equals`·`hashCode`를 오버로딩했다(서명이 `Object`가 아님).
   - 확인: 메서드에 `@Override`를 붙여 컴파일해 본다(실험 A 오류). `javap -p`로 `equals(java.lang.Object)`가 있는지 본다.
2. **증상**: 컬렉션에서 엉뚱한 원소가 지워진다·엉뚱한 오버로드가 불린다.
   - 원리: 오버로드는 인자 식의 **정적(컴파일 시점) 타입**과 박싱 단계로 정적으로 고른다(JLS 15.12.2).
   - 확인: `javap -c`로 호출 지점의 서명을 본다(`remove:(I)…` vs `remove:(Ljava/lang/Object;)Z`). 공개 API에서 `int`/`Object`, `Object`/`String`처럼 겹치는 오버로드를 피한다.
3. **증상**: 구현 클래스를 추가한 배포 뒤 특정 핫 루프만 느려졌다.
   - 원리: 호출 지점이 메가모픽이 되어 인라인이 끊겼다.
   - 확인: `java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining …`에서 그 메서드 줄이 `inline (hot)`인지 `virtual call`인지 본다(실험 C). 프로파일러에서 itable/vtable 스텁이 보이는지도 본다.
   - 대처: 타입별로 호출 지점을 나눈다(종류별로 모아 처리), 구현을 `final`·`sealed`로 닫는다, 진짜 핫한 경로는 다형성 없이 데이터 지향으로 바꾼다.

```java
// 메가모픽 지점을 타입별 단형 지점 여러 개로 나누는 예 — 호출 지점(바이트코드 위치)이 타입마다 따로 있어야 한다
// (그룹으로 묶어 같은 sumAreas(group)에 넘기면 그 안의 s.area()는 여전히 한 호출 지점·한 타입 프로파일이다)
long total = 0;
for (Circle c : circles) total += c.area();   // 이 지점은 Circle만 본다
for (Rect r : rects)     total += r.area();   // 이 지점은 Rect만 본다
// 효과는 PrintInlining·측정으로 확인한다.
```

## 장애 시나리오와 대처

### 1. 오버로딩(컴파일 시점) vs 오버라이딩(실행 시점) 혼동 → 엉뚱한 메서드 호출 (⚠ 커리큘럼)

- 현상: 중복 제거용 `Set<UserId>`에 같은 사용자가 여러 번 들어가 알림이 중복 발송된다.
- 보이는 형태: `ids.contains(probe)`가 `false`, 직접 `probe.equals(copy)`는 `true`(실험 A).
- 원인: `public boolean equals(UserId other)`는 `Object.equals(Object)`의 재정의가 아니라 새 오버로드다. 컬렉션은 `Object` 서명을 부르므로 동일성 비교가 실행된다.
- 대처: `@Override` 필수(정적 분석 규칙). `equals(Object)`·`hashCode()`를 함께 재정의하거나 `record`를 쓴다([languages/java/syntax/27](../../../languages/java/syntax/27-equals-hashcode-contract/2-summary.md)).

### 2. 박싱 오버로드 → 값이 아니라 인덱스를 지운다

- 현상: 차단 목록 `List<Integer>`에서 사용자 ID 1을 지웠는데 다른 ID가 사라졌다.
- 보이는 형태: `remove(1)` 뒤 `[10, 1]`(실험 A). `javap`에 `List.remove:(I)`.
- 원인: JLS 15.12.2 1단계(박싱 없이 적용 가능)에서 `remove(int index)`가 먼저 선택됐다.
- 대처: `remove(Integer.valueOf(id))`·`removeIf(x -> x == id)`로 의도를 드러낸다. ID를 전용 타입으로 감싸면 혼동이 원천적으로 사라진다([software-design/24](../../software-design/24-types-as-invariants/2-summary.md)).

### 3. 구현을 추가했더니 핫 루프가 10배 느려졌다 (메가모픽)

- 현상: 새 결제 수단 구현 2개를 추가한 배포 뒤 수수료 계산 배치가 느려졌다. 코드 변경은 새 클래스뿐이다.
- 보이는 형태: 프로파일에서 계산 메서드 비중 증가. `PrintInlining`에서 `inline (hot)`이 `virtual call`로 바뀜(실험 C에서 2종류 1.19~1.64ns → 4종류 10.01~13.58ns, 재실행 min 1.06~1.28 → 9.32~17.00).
- 원인(실험 C와 같은 경우): 한 호출 지점이 보는 수신 타입이 2개를 넘었고, 어느 하나가 90% 이상을 차지하지도 않아 C2가 인라인을 시도하지 않았다(`UseBimorphicInlining`은 2개까지, 주 수신 타입 기준은 `TypeProfileMajorReceiverPercent`=90).
- 대처: 측정으로 원인을 먼저 확정한다. 그다음 종류별 일괄 처리, 핫 경로 데이터화(타입 대신 숫자 표), `final`/`sealed`로 닫기 중 고른다. 효과는 다시 측정한다.

### 4. C++ 가상 호출을 "공짜"로 가정

- 현상: 객체 수백만 개의 가상 `update()`를 도는 루프가 예상보다 느리다.
- 보이는 형태: `objdump`에 `jmp *(%rax)`·`call *…` 간접 호출, `perf`에서 분기 예측 실패 증가 [?].
- 원인: 구현이 여럿이면 추측 탈가상화(`-fdevirtualize-speculatively`)가 맞지 않고, 간접 분기 목적지가 섞이면 예측이 빗나간다([architecture/18](../../architecture/18-pipelining-and-branch-prediction/2-summary.md)).
- 대처: `final`로 닫을 수 있는 클래스는 닫는다(실험 B `call_final`). 타입별로 모아 처리하거나 템플릿(단형화)으로 바꾼다. 코드 크기 증가와 교환이다.

## 핵심 문장

- 오버로딩은 컴파일 시점에 인자 식의 정적 타입으로, 오버라이딩은 실행 시점에 수신 객체의 실제 타입으로 고른다.
- 고른 서명은 바이트코드에 박히므로, `equals(UserId)` 같은 오버로드는 컬렉션이 부르는 `equals(Object)`를 대신하지 못한다.
- 동적 디스패치의 기본 장치는 클래스별 메서드 표(vtable — C++은 함수 포인터, HotSpot은 `Method*`)이고, 인터페이스는 한 단계 더 찾는 itable을 쓴다.
- 단형화는 타입마다 코드를 복제해 호출을 확정하고, Java는 소거로 코드 하나를 두는 대신 JIT의 인라인 캐시에 기댄다.
- HotSpot C2는 호출 지점이 본 타입이 1~2개이거나 지배적인 타입(90% 이상)이 있으면 타입 검사 + 인라인을 시도한다. 시도해도 크기 등으로 거절될 수 있고, 수신 클래스가 여럿이어도 같은 구현으로 귀결되면 클래스 계층 분석(CHA)으로 직접 호출이 될 수 있다(`opto/doCall.cpp`의 `optimize_virtual_call`·CHA 경로). 실험 C처럼 고르게 섞이면 가상 호출로 남아 비용이 크게 뛰었다.

## 관련 주제·근거

- 선행: [05-type-systems](../05-type-systems/2-summary.md)
- 후속: [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md)(역최적화·타입 프로파일) · [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md)(인라이닝)
- 다른 영역
  - [software-design/20-oop-fundamentals](../../software-design/20-oop-fundamentals/2-summary.md) — 다형성 개념, `invokevirtual`·`getfield`·`invokestatic` 실험
  - [software-design/27-design-patterns-gof](../../software-design/27-design-patterns-gof/2-summary.md) — 방문자(이중 디스패치)
  - [architecture/18-pipelining-and-branch-prediction](../../architecture/18-pipelining-and-branch-prediction/2-summary.md) — 간접 분기 예측
  - [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) — 측정 함정
  - 언어별: [java/08 overloading](../../../languages/java/syntax/08-method-declaration-overloading/2-summary.md), [java/09 overriding](../../../languages/java/syntax/09-inheritance-overriding/2-summary.md), [rust/31 monomorphization](../../../languages/rust/syntax/31-generics-trait-bounds-where-and-monomorphization/2-summary.md), [rust/33 dyn](../../../languages/rust/syntax/33-dyn-trait-objects-and-object-safety/2-summary.md), [go/19 method sets](../../../languages/go/syntax/19-method-sets-value-vs-pointer-receiver/2-summary.md)
- 명세·문서·소스
  - JLS SE 21 8.4.8.1 Overriding · 8.4.9 Overloading · 15.12.2 Compile-Time Step 2(1단계 strict / 2단계 loose) — <https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html>
  - JVMS SE 21 5.4.6 Method Selection · 6.5 `invokevirtual`·`invokeinterface` — <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html>
  - OpenJDK 21 `src/hotspot/share/code/compiledIC.hpp`(인라인 캐시 상태 전이) · `src/hotspot/share/oops/klassVtable.hpp` · `src/hotspot/share/opto/c2_globals.hpp`(`UseBimorphicInlining`, `TypeProfileMajorReceiverPercent`) · `src/hotspot/share/opto/doCall.cpp`(인라인 판단) · `src/hotspot/share/runtime/globals.hpp`(`TypeProfileWidth`) — <https://github.com/openjdk/jdk21u>
  - GCC 13.3 "Options That Control Optimization" `-fdevirtualize-speculatively` — <https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html>
  - Dragon Book의 해당 장 [?]
- 실험 목록(모두 `scratchpad/lang/05/e17/`, 2026-10-07, 컨테이너는 `--rm --network none --cpus=2`)
  - A `Overload.java`·`OverrideCheck.java`·`Remove.java`: 오버로드 vs 오버라이드, `equals` 오버로드 버그, `remove(int)`, `javap -c` — `eclipse-temurin:21-jdk` 21.0.12
  - B `vt.cpp`: 가상 호출·`final`·추측 탈가상화·템플릿 단형화 기계어 — 호스트 g++ 13.3 `-O2`(± `-fno-devirtualize-speculatively`), `objdump`, `nm`
  - C `Megamorphic.java`: 수신 타입 1·2·4·8종류 지연(종류당 JVM 3회) + `PrintInlining` — `eclipse-temurin:21-jdk`(사실 점검 때 같은 조건으로 한 번 더)
