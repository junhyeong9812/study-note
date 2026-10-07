# language/17-dispatch-and-polymorphism-mechanics — 정답

## 정답

### 1. 정적 선택과 동적 선택

- `f(o)` → `f(Object)`(실험 A). 오버로드는 **컴파일 시점에 인자 식의 정적 타입**(여기서는 변수 `o`의 선언 타입 `Object`)으로 고른다(JLS 15.12.2). 바이트코드에 `invokestatic f:(Ljava/lang/Object;)…`로 박힌다.
- `a.speak()` → `Dog.speak`. 컴파일러는 서명 `Animal.speak()`만 고르고, **실행 시점에 수신 객체의 실제 클래스**에서 구현을 찾는다(`invokevirtual`, JVMS 5.4.6).

### 2. `equals` 오버로드 버그

- `HashSet.contains(probe)` → `false`. 직접 `probe.equals(copy)` → `true`(실험 A).
- 이유: `equals(UserId)`는 `Object.equals(Object)`를 재정의하지 않은 새 오버로드다. `HashSet.contains` → `HashMap.getNode`는 해시가 같은 노드에서 `key.equals(k)`를 `Object` 서명으로 부르므로 `Object.equals`(동일성)가 실행됐다. 실험의 `UserId`가 `hashCode`를 값으로 재정의해 같은 버킷을 찾았기 때문이다(재정의하지 않았다면 해시가 달라 `equals`까지 가지도 않는다).
- 잡는 법: `@Override`를 붙이면 `error: method does not override or implement a method from a supertype`(실험 A `OverrideCheck.java`).

### 3. `remove(1)`

- `[10, 1]` — 인덱스 1(값 20)이 지워졌다(실험 A).
- JLS 15.12.2의 1단계(strict invocation, 박싱·언박싱 없이 적용 가능한 메서드)에서 `remove(int)`가 맞아 선택됐다. `remove(Object)`는 박싱이 필요해 2단계 후보다.
- `javap -c`: `InterfaceMethod java/util/List.remove:(I)Ljava/lang/Object;`. 값으로 지우려면 `remove(Integer.valueOf(1))` → `remove:(Ljava/lang/Object;)Z`, 결과 `[10, 20]`.

### 4. vtable

```text
  (개념도 — 슬롯 번호는 예시. HotSpot의 Object에는 clone·finalize 등도 있어 실제 배치는 다르다)
  Animal vtable: [0 toString][1 equals][2 hashCode][3 speak → Animal.speak]
  Dog    vtable: [0 toString][1 equals][2 hashCode][3 speak → Dog.speak]   ← 같은 슬롯 번호
```

- ① 객체 헤더에서 클래스(vtable) 포인터를 읽는다. ② 슬롯 3에서 구현을 읽는다(C++은 함수 주소, HotSpot은 `Method*` — 진입점은 그 `Method`에서 얻는다, `klassVtable.hpp`). ③ 그 구현으로 간접 호출한다.
- 인터페이스 호출: 한 클래스가 여러 인터페이스를 구현해 슬롯 번호가 고정되지 않는다. 그래서 그 인터페이스의 표(itable)를 먼저 찾는 단계가 더 있다.

### 5. gcc의 가상 호출 기계어

- `-O2` 기본: vtable 슬롯을 읽어 `Sq::area` 주소와 `cmp`하고, 같으면 `Sq::area` 본문(`imul`)을 인라인, 다르면 `jmp *%rax`(실험 B). 추측 탈가상화(`-fdevirtualize-speculatively`, `-O2`에서 켜짐)다.
- `-fno-devirtualize-speculatively`: `mov (%rdi),%rax; jmp *(%rax)` — 순수 간접 점프.
- `call_final(const Sq&)`: 간접 호출 없이 `mov 0x8(%rdi),%eax; imul %eax,%eax` — 대상이 확정되어 인라인됐다.

### 6. 단형화 vs 소거

| | 코드 | 호출 | 비용 |
|---|---|---|---|
| 단형화 | 타입마다 복제(`twice<Circle>`, `twice<Rect>` 별도 심볼, 실험 B `nm`) | 타입 인자로 정해지는 호출은 컴파일 시점 확정, 인라인 쉬움(본문이 가상 함수를 부르면 그 호출은 동적으로 남는다) | 코드 크기·컴파일 시간 증가 |
| Java 소거 | 하나 | 인터페이스·가상 호출로 남음 | 실행 중 디스패치 비용 — JIT의 인라인 캐시·타입 프로파일로 줄임 |

### 7. 수신 타입 수와 인라인

| 종류 | `PrintInlining` | ns/call(min 범위, 3회) | 사실 점검 재실행(min, 3회) |
|---|---|---|---|
| 1 | `S0::area inline (hot)` | 0.70~0.87 | 0.67~0.93 |
| 2 | `S0::area`, `S1::area` 모두 `inline (hot)` | 1.19~1.46 | 1.06~1.28 |
| 4 | `Shape::area virtual call` | 10.01~11.62 | 9.32~17.00(17.00은 1회 이상치) |
| 8 | `Shape::area virtual call`(재실행에서 확인) | 9.95~11.83 | 9.50~10.55 |

- 1~2종류는 타입 검사 + 인라인을 시도한다(이형 인라인은 `UseBimorphicInlining`, 기본 `true` — 시도해도 크기 등으로 거절될 수 있다). 이 실험처럼 고르게 섞인 3종류 이상은 가상 호출로 남아 약 10배 비쌌다. 한 타입이 90% 이상이면(`TypeProfileMajorReceiverPercent`) 그 타입은 인라인될 수 있다(`opto/doCall.cpp`). 직접 측정이며 이 호스트·루프에 한정된다.

### 8. 배포 뒤 배치 감속

- 의심: 계산 루프의 인터페이스 호출 지점이 2종류 → 4종류가 되어 메가모픽이 됐다.
- 확인: `java -XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining …`에서 해당 호출이 `inline (hot)`에서 `virtual call`로 바뀌었나 본다. 프로파일러로 그 루프의 비중 증가를 확인한다.
- 대처 후보: 종류별로 묶어 처리, 핫 경로를 데이터(요율 표)로 바꿔 다형성 제거, 구현을 `final`/`sealed`로 닫기. 무엇이든 적용 후 다시 측정한다.

### 9. 인라인 캐시 상태 전이

- Clean: 아직 대상이 정해지지 않은 상태(처음 상태이며, 이미 쓰던 IC도 `set_to_clean`으로 이 상태로 되돌아갈 수 있다 — `compiledIC.cpp`). Monomorphic: 지난 수신 클래스(`Klass*`) 하나를 기억하고 맞으면 바로 그 구현으로 간다. Megamorphic: 다른 클래스가 와서 캐시가 맞지 않으면 일반 조회(vtable/itable) 스텁으로 간다("[4]: Inline cache miss. We go directly to megamorphic call."). 그래서 IC의 Megamorphic은 두 번째 클래스만 와도 될 수 있고, 7번 표의 1·2·다수(C2 타입 프로파일 분류)와 같은 기준이 아니다.
- 닮은 점: CPU 간접 분기 예측도 "이 분기는 지난번 그 주소로 갔다"는 기록에 건다. 목적지가 하나면 잘 맞고, 여러 목적지가 섞이면 빗나간다([architecture/18](../../architecture/18-pipelining-and-branch-prediction/2-summary.md)). 둘 다 "과거에 본 대상이 반복된다"는 가정에 기대는 캐시다.
