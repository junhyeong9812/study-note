# foundations/languages — JVM과 Java: "결정을 실행 시점까지 미룬다"는 선택과 그 청구서 (정리)

> 이 노트는 JVM이 무엇을 풀려고 만들어졌고, 그 해법이 어떤 성질과 비용을 필연적으로 낳는지를 개념부터 정리한다.\
> 원고 출처: `jun-bank/docs/study/tech/languages/java-jvm.md` (따라 친 학습 노트) · 이관일 2026-09-16.\
> 본문 절들은 **원고**를 고쳐 쓴 것이다(문체·순서·인용·수치 유지). 프로젝트 고유명(특정 은행 시스템·내부 결정 문서 번호)은 일반형으로 바꿨다.\
> 「한눈에」·「전체 흐름」 그림은 **Claude가 새로 그린 것**이고, 원고에 없던 지식은 맨 끝 `[Claude 추가]`에만 둔다. 인용한 스펙(JVMS·JLS SE 21 등)은 원고 그대로다.

바이트코드·클래스로더·JIT·GC·메모리 모델은 각각의 기능이 아니라 **"컴파일 시점에 확정하지 않고 실행 시점까지 미룬다"는 하나의 결정에서 갈라져 나온 결과**로 읽는 것이 이해가 빠르다.

---

## 한눈에 — 쉽게 말하면

JVM은 **주문 직전까지 메뉴를 안 정하는 주방**이다. *(Claude 보강 — 원고에 없는 비유)*

```text
미리 다 정하는 도시락 (네이티브 AOT)      주문 보고 만드는 주방 (JVM)
+---------------------------+          +---------------------------+
| 어느 손님이든 같은 도시락    |          | 손님 취향을 보고 그때 조리   |
| 데우면 바로 나온다          |          | 준비(로드·검증)에 시간 든다  |
| 손님별 최적화는 없다        |          | 자주 오는 주문은 미리 데운다 |
+---------------------------+          +---------------------------+
  → 짧게 왔다 가는 손님에 유리          → 오래 앉아 먹는 손님에 유리
```

**JVM도 똑같은 구조다.** 기계도 실행 시점에, 무엇을 읽을지도 실행 시점에, 어떻게 최적화할지도 실행 시점에 정한다. 그 유연함이 값을 내는 조건은 하나로 줄어든다 — **오래 살아서 그 판단 비용을 상각할 수 있는가.** 은행 코어는 그 조건을 만족하고, 배포 스크립트는 만족하지 않는다.

---

## 이 문서가 답하려는 질문

개념 정리다(코드 과제 없음). 논리는 셋으로 흐른다.

```text
무엇이 문제였나        모르는 기계 + 사람이 메모리를 세는 위험 (§1)
어떤 아이디어로 풀었나   기계를 하나 발명한다 (§2) → 클래스로더·JIT·GC (§3~8)
그 아이디어의 청구서는   기동·상주 메모리·워밍업·튜닝 표면 (§11)
```

인용한 스펙은 Java SE 21의 JVMS·JLS, HotSpot 동작은 OpenJDK 문서·JEP·소스 주석 기준이다.

---

## 전체 흐름 — 하나의 결정에서 갈라져 나온 것들

*(Claude 보강 — 원고 §13의 결론을 세로 흐름으로)*

```text
결정: "컴파일 시점에 확정하지 않고 실행 시점까지 미룬다"
        ↓
바이트코드   어느 기계에서 돌지를 실행 시점에 정한다
        ↓
클래스로더   무엇을 읽을지를 실행 시점에 정한다
        ↓
JIT         어떻게 최적화할지를 실행 시점에 정한다 (실행 통계를 보고)
        ↓
GC          언제 해제할지를 실행 시점에 정한다
        ↓
청구서:  판단할 런타임이 상주해야 하고(메모리)
         판단할 정보를 모을 시간이 필요하며(워밍업)
         판단 자체가 매번 처음부터 시작한다(기동)
```

---

## 0. 왜 태어났나 — 무엇을 지향하고, 이웃 언어와 어디서 갈리나

> 출처: 원고 §0

Java는 언어 연구가 아니라 제품 문제에서 나왔다. 1995년 백서가 출발을 직접 적는다 — 배포 대상이 CPU·OS가 제각각인 **이기종 네트워크 기기**였고, 그 위에서 C++의 복잡성과 메모리 위험이 감당이 안 됐다는 것. "When the project started, C++ was the language of choice. But over time the difficulties encountered with C++ grew to the point where the problems could best be addressed by creating an entirely new language environment"([The Java Language Environment, 1995](https://www.stroustrup.com/1995_Java_whitepaper.pdf) §1.1).

지향점은 백서가 이름표를 붙여 두었다.

- **플랫폼 독립.** "the same Java language byte codes will run on any platform"(§1.2.3). 뒤에 "Write Once, Run Anywhere(WORA)"로 굳는다. 기본 자료형의 크기와 산술까지 스펙이 못박는다 — "Your programs are the same on every platform."
- **메모리 안전.** "no pointers or pointer arithmetic—eliminates entire classes of programming errors"(§1.2.2). §12가 은행 맥락에서 되짚는 "틀린 값으로 조용히 계속 도는" 계급이 정확히 이것이다.
- **친숙함 위에서 위험만 제거.** "keeping Java looking like C++ … while removing the unnecessary complexities of C++"(§1.2.1).
- **거대 표준 라이브러리·후방 호환·"지루하지만 안정적".** 이후 30년의 운영에서 굳은 지향이다. **옛 바이트코드가 새 JVM에서 그대로 도는 후방 호환**이 이 생태계의 제1 계율이 됐다. [실무 의견]

**짧은 역사(이정표만).** 1991 Green 프로젝트(언어명 Oak) → 1995 Java 개명·애플릿 공개 → 1996 JDK 1.0 → 2004 J2SE 5.0(제네릭을 **소거(type erasure)**로 구현해 후방 호환 유지) → 2014 Java 8(람다·스트림) → 2017 6개월 릴리스 케이던스([Java version history](https://en.wikipedia.org/wiki/Java_version_history)). 관통하는 규칙은 "안전을 늘리되 기존 것을 안 깬다"이다.

**이웃 언어 좌표.** 같은 "메모리 안전"을 GC로 이룬 언어가 Java만은 아니다.

- **Go(같은 GC 진영).** 공통점은 메모리 오류 계급 제거. 차이는 무게와 겨냥 — Go는 런타임을 가볍게 유지해 고루틴 하나가 약 2.6KB, 단일 바이너리로 뜨고 기동이 짧다([`go.md`](go.md)). JVM은 그 대가로 무겁지만 25년치 관측 도구와 JIT 정점 성능을 얹어 준다.
- **C#(거의 동형).** CLR 위 관리 런타임으로 JIT·GC·바이트코드(IL) 구조가 JVM과 거의 겹친다 — 갈릴 자리가 별로 없어 **생태계와 팀**에서 갈린다([`c-cpp-csharp.md`](c-cpp-csharp.md)).
- **C·C++(반대 진영 — 안전 대 제어).** 백서가 없앤 결함 계급을 C/C++는 "프로그래머를 신뢰하라"는 원칙 아래 **의도적으로 떠안는다** — 검사 대신 제어와 속도([`c-cpp-csharp.md`](c-cpp-csharp.md)).
- **Rust(GC 없는 제3의 답).** 같은 안전을 **런타임 없이 컴파일 타임 소유권**으로 이룬다([`rust.md`](rust.md)). Java는 고전 해법(GC)의 대표 격이고, 이 둘의 대비가 "안전의 값을 런타임에 낼 것인가 컴파일러에 낼 것인가"를 가장 선명하게 보여 준다.

---

## 1~2. 문제와 아이디어 — 기계를 하나 발명한다

> 출처: 원고 §1·§2

두 문제가 동시에 있었다. 첫째, 배포 대상 기계의 CPU·OS를 컴파일 시점에 알 수 없다. 둘째, 사람이 해제 시점을 관리하는 메모리 모델은 UAF·이중 해제를 만드는데, 이 결함은 프로세스가 **죽지 않고 오염된 상태로 계속 도는 것**이 특징이다. 둘의 요구는 같다 — **프로그램과 실제 기계 사이에 판단할 수 있는 층을 하나 끼워 넣는 것.**

JVM 스펙이 자신을 규정한다 — "The Java Virtual Machine is an abstract computing machine." 그리고 결정적 문장 — "The Java Virtual Machine knows nothing of the Java programming language, only of a particular binary format, **the class file format**"([JVMS SE 21 §1.2](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-1.html)). 계약의 단위가 언어가 아니라 `class` 파일 형식이라, Kotlin·Scala·Groovy가 같은 런타임 위에 설 수 있고 **언어를 바꿔도 생태계를 하나도 잃지 않는다.**

메모리 쪽도 같은 자리에 위임된다 — "objects are never explicitly deallocated. The Java Virtual Machine assumes no particular type of automatic storage management system"([JVMS §2.5.3](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-2.html)). 마지막 문장이 중요하다 — 스펙은 **GC를 요구하되 어떤 GC인지는 정하지 않았다.** 그 빈칸이 뒤의 G1과 ZGC를 가능하게 한 자리다.

---

## 3. 클래스로더 — "언제 로드되는가"가 별도 개념이 된다

> 출처: 원고 §3

실행 시점까지 미루기로 한 순간, "무엇을 언제 읽어 들이는가"가 개념으로 승격된다. 스펙은 셋을 나눈다 — **Loading**(바이너리를 찾아 타입을 만드는 것), **Linking**(런타임 상태에 결합하는 것), **Initialization**(`<clinit>` 실행)([JVMS §5](https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html)). 링크는 다시 검증·준비·해소로 나뉘고, "A class is completely verified and prepared before it is initialized." 검증이 여기 있다는 점이 §1의 둘째 문제와 이어진다 — 임의의 바이트 열이 아니라 **타입 안전성이 검사된 것만** 실행된다.

로드는 위임 구조다 — "a `ClassLoader` instance will usually delegate the search … to its parent class loader before attempting to find the class … itself"([ClassLoader javadoc](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/ClassLoader.html)). 부모에게 먼저 묻는 규칙 하나가 "애플리케이션 코드가 `java.lang.String`을 가짜로 바꿔치기할 수 없다"를 보장한다. 반대로 청구서도 여기서 나온다 — 같은 이름 클래스가 다른 로더에서 로드되면 **서로 다른 타입**이고, `ClassCastException`이 "A cannot be cast to A"처럼 읽히는 상황이 그것이다. [실무 의견]

---

## 4~5. JIT — 미룬 덕에 더 많이 아는 컴파일러, 틀려도 되게 만들고 추측한다

> 출처: 원고 §4·§5

바이트코드를 매번 해석하면 느리다. HotSpot은 실행 중에 기계어로 컴파일한다. 컴파일러는 둘이다 — C1(빠르고 가볍게 최적화)과 C2(공격적 인라이닝·전역 최적화). 둘을 함께 쓰는 것이 **티어드 컴파일**이고 서버 VM 기본값이다([HotSpot Glossary](https://openjdk.org/groups/hotspot/docs/HotSpotGlossary.html)).

단계는 다섯이고 소스 주석이 그대로 나열한다.

```text
level 0 - interpreter (프로파일을 MethodData(MDO)로 추적)
level 1 - C1 with full optimization (no profiling)
level 2 - C1 with invocation and backedge counters
level 3 - C1 with full profiling
level 4 - C2 with full profile guided optimization
```

([compilationPolicy.hpp](https://github.com/openjdk/jdk/blob/master/src/hotspot/share/compiler/compilationPolicy.hpp)) 같은 주석이 설계 의도를 드러낸다 — "level 2 is generally faster than level 3 by about 30%", 즉 **프로파일링은 공짜가 아니고** 정책의 상당 부분이 "C2에 넘길 만큼만 모으고 빨리 빠져나오기"에 쓰인다.

JIT의 이점은 "나중에 컴파일해서"가 아니라 **컴파일할 때 실제 실행 통계를 알고 있어서**다. 어느 분기가 실제로 잡히는지, 어느 호출 지점이 단형(monomorphic)인지는 정적 컴파일러가 알 수 없다.

프로파일 추측은 언젠가 깨진다. 그래서 되돌리는 장치가 짝으로 필요하다 — **deoptimization**(컴파일 프레임을 인터프리터 프레임으로 되돌림), **uncommon trap**(C2 코드가 인터프리터로 복귀), **OSR**(루프 도는 인터프리터 프레임을 컴파일 프레임으로 교체). 이것이 JVM 성능의 핵심 비대칭이다 — **되돌릴 수 있으니 틀릴 수 있는 최적화를 해도 된다.** OpenJDK 표현으로 "It can speculatively optimize … and revert to interpreting bytecode when it observes that the assumption no longer holds … the JVM can achieve higher peak performance than … traditional static approaches"([JEP 483](https://openjdk.org/jeps/483)).

---

## 6. 그래서 얼마나 빠른가 — "네이티브 몇 배"의 정직한 형태

> 출처: 원고 §6

이 질문은 조건 없이는 답이 없다. 정직한 형태는 셋으로 쪼개는 것이다.

**① 정점 성능(peak).** 충분히 오래 돈 뒤의 뜨거운 경로는 정적 컴파일과 같은 급이다. 조건이 명시된 공개 실측은 Benchmarks Game이다 — 손 벡터화를 뺀 최속끼리 비교하면 spectral-norm 1.03배, fannkuch-redux 1.31배, n-body 1.34배, mandelbrot 1.73배([Java vs C++ g++](https://benchmarksgame-team.pages.debian.net/benchmarksgame/fastest/javavm-gpp.html)). "1~2배 안"은 **이 조건에서는** 유지된다. 단 ⑴ 워밍업이 끝난 계산 커널만 잰다(JIT에 가장 유리) ⑵ 수작업 벡터화 C++까지 넣으면 격차가 벌어진다(mandelbrot 약 4.7배) ⑶ 사이트 자신이 "언어 순위표가 아니라 특정 구현의 측정치"라 못박는다.

**② 워밍업(warmup).** 정점 도달까지의 구간. "the time required for the HotSpot JVM to optimize an application's code for peak performance"([JEP 483](https://openjdk.org/jeps/483)). 이 구간이 존재한다는 사실 자체가 비용이다.

**③ AOT와의 대조.** 같은 코드를 JIT로 돌린 것과 GraalVM Native Image로 AOT 한 것을 나란히 잰 자료 — CPU 초는 AOT가 조금 앞서고 **상주 메모리는 AOT가 약 1/3**(n-body 20MB 대 61MB), 빌드 시간은 AOT가 두 자릿수 배로 길다([Java vs Java naot](https://benchmarksgame-team.pages.debian.net/benchmarksgame/fastest/java.html)). 그러나 이 프로그램들은 동적 디스패치가 거의 없는 계산 커널이라 **JIT의 무기(실행 프로파일 기반 추측)가 쓰일 자리가 없다.** 그 무기가 필요한 쪽에서는 반대 증거가 나온다 — GraalVM 자신이 "PGO를 써라, **JIT로 돌 때와 유사하게** 프로파일을 활용한다"고 안내한다([GraalVM Native Image: Optimizations](https://www.graalvm.org/latest/reference-manual/native-image/optimizations-and-performance/)).

정리하면 축은 성능이 아니라 **프로세스 수명**이다. 짧게 뜨고 죽는 것에는 AOT가, 오래 도는 큰 동적 코드베이스에는 JIT가 유리하다.

---

## 7~8. GC — 세대 가설의 G1, 일시정지를 힙 크기에서 떼어낸 ZGC

> 출처: 원고 §7·§8

GC 전략의 출발점은 관찰 하나다 — "**weak generational hypothesis**: young objects tend to die young, while old objects tend to stick around"([JEP 439](https://openjdk.org/jeps/439)). 이 가설이 참이면 힙 전체를 매번 훑을 이유가 없다.

**기본 컬렉터 G1**은 힙을 동일 크기 **영역(region)**으로 나누고, 회수는 복사(evacuation)로, 그 복사는 **stop-the-world**에서 한다([GC Tuning Guide: G1](https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-g1-garbage-collector1.html)). G1은 일시정지를 없애는 게 아니라 **예측 가능한 상한 안에 넣는** 컬렉터다 — 목표는 소프트 목표이고 기본값 200ms다. 승인 응답 p99 목표가 3초인 시스템에서 200ms는 예산의 한 자리를 차지하지만 치명적이지 않고, 목표가 수십 ms인 시스템이라면 G1은 처음부터 틀린 선택이다.

**ZGC**는 복사 자체를 애플리케이션과 동시에 하는 쪽으로 문제를 옮겼다. 핵심 장치가 **컬러 포인터와 로드 배리어**다 — "the act of loading a reference field … is subject to a load barrier … the object might have been relocated, in which case the load barrier will … take appropriate action"([JEP 333](https://openjdk.org/jeps/333)). 그 결과가 일시정지와 힙 크기의 분리다 — "Stop-the-world phases are limited to root scanning, so GC pause times do not increase with the size of the heap." 대신 청구서는 처리량으로 간다 — 목표가 "No more than 15% application throughput reduction compared to G1"이었다. **일시정지를 산 값은 상시 오버헤드**다. (세대화는 JDK 21 [JEP 439](https://openjdk.org/jeps/439)로 얹혀 지금 `-XX:+UseZGC`는 세대별 ZGC다.)

실측 대조는 JEP 333이 SPECjbb 2015, 128G 힙에서 보고한 값이 가장 구체적이다.

| | 평균 | 99.9 백분위 | 최대 |
|---|---|---|---|
| ZGC | 1.091ms | 1.663ms | 1.681ms |
| G1 | 156.806ms | 543.846ms | 543.846ms |

이 수치는 **128G 힙이라는 조건에서의 값**이고, 힙이 작으면 격차는 줄어든다(G1 일시정지가 힙에 비례하는 반면 ZGC는 그렇지 않다는 것이 요지다).

---

## 9. 메모리 모델 — happens-before, "동시성이 맞다"를 말할 수 있게 하는 규칙

> 출처: 원고 §9

JIT와 CPU가 재배치를 하면, 다른 스레드가 내 쓰기를 언제 보는지를 어떻게 아는가. 이 물음에 답이 없으면 동시성 코드의 "정확하다"는 말이 정의되지 않는다.

자바의 답이 **happens-before**다 — "If one action *happens-before* another, then the first is visible to and ordered before the second"([JLS SE 21 §17.4.5](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)). 관계를 만드는 규칙은 synchronizes-with에서 온다.

| 만드는 것 | 스펙 문장 |
|---|---|
| 락 | "An unlock action on monitor *m* synchronizes-with all subsequent lock actions on *m*" |
| volatile | "A write to a volatile variable *v* synchronizes-with all subsequent reads of *v* by any thread" |
| 스레드 시작 | "An action that starts a thread synchronizes-with the first action in the thread it starts." |
| 스레드 종료 | "The final action in a thread `T1` synchronizes-with any action in another thread `T2` that detects that `T1` has terminated." |

이 보증의 값어치를 스펙 자신이 설명한다 — "If a program is correctly synchronized, then all executions … will appear to be sequentially consistent." **경합만 없애면 재배치를 머릿속에서 지워도 된다**는 것이 JMM이 개발자에게 판 물건이다. 함정 하나 — 동기화는 "어딘가 락을 걸었다"가 아니라 **같은 모니터로 짝을 맞췄다**일 때만 성립한다([JSR-133 FAQ](https://www.cs.umd.edu/~pugh/java/memoryModel/jsr-133-faq.html)).

```kotlin
class BalanceCache {
    @Volatile private var snapshot: Balance? = null   // volatile 쓰기 = 모니터 해제와 같은 메모리 효과

    fun publish(b: Balance) { snapshot = b }          // 이 쓰기 이전의 모든 쓰기가
    fun read(): Balance? = snapshot                   // 이 읽기 이후에 보인다
}
```

비용도 실재한다. LMAX가 2.4GHz 코어에서 64비트 카운터를 5억 번 증가시킨 실험(단위 ms) — 단일 스레드 300, 락 건 단일 스레드 10,000, 락 경합 두 스레드 224,000, CAS 단일 스레드 5,700, volatile 쓰기 4,700([LMAX Disruptor Table 1](https://lmax-exchange.github.io/disruptor/disruptor.html)). 순서 보장은 공짜가 아니고 **경합이 붙는 순간 두 자릿수 배로 뛴다**.

---

## 10. 관측 — 새벽 3시에 열어볼 수 있는가

> 출처: 원고 §10

JVM의 실무 강점 중 절반은 성능이 아니라 이것이다 — 프로세스가 살아 있는 채로 내부를 꺼낼 수 있고, 그 도구가 JDK에 기본 포함된다.

```bash
jcmd <pid> Thread.print -l          # 스레드 스택 + 락 (Impact: Medium)
jcmd <pid> GC.heap_dump dump.hprof  # 힙 덤프 (Impact: High — full GC 요청)
jcmd <pid> JFR.start                # Flight Recorder (Impact: Low)
```

셋의 성격이 다르다 — **스레드 덤프**는 "지금 누가 어디서 멈춰 있나"의 스냅샷(락 대기·데드락), **힙 덤프**는 "무엇이 메모리를 붙잡나"의 스냅샷(Impact High라 아무 때나 뜨는 도구가 아님; `-XX:+HeapDumpOnOutOfMemoryError`로 사고 순간 자동 포착), **JFR**은 스냅샷이 아니라 **사고 직전까지의 이벤트 기록**이다([JEP 328](https://openjdk.org/jeps/328)). JFR을 상시 켤 수 있는가가 갈림길인데, 성공 기준이 "At most 1% overhead … No measurable overhead when not enabled"였다(단 기본으로는 꺼져 있어 `-XX:StartFlightRecording`로 켜야 한다). 관측 스택을 나중으로 미룬 시스템에서 JVM 기본 도구의 값은 여기 있다 — 외부 도구 없이도 사후 분석의 최소선이 런타임에 들어 있다. [실무 의견]

---

## 11. 비용의 정직한 목록 — 기동·상주 메모리·워밍업·튜닝 표면

> 출처: 원고 §11

JEP 483이 이 청구서를 스스로 요약한다 — "All this dynamism comes at a price, however, which must be paid every time an application starts."

- **기동.** JVM은 시작 시 "수백 개의 JAR을 스캔하고 수천 개 클래스를 읽어 파싱"하고, 로드·링크·검증·해소를 한다. 프레임워크가 있으면 더 늘어난다 — Spring PetClinic 3.2.0은 약 21,000개 클래스를 로드하며 JDK 23에서 4.486초가 걸렸다(AOT 캐시 시 2.604초).
- **워밍업.** 정점 성능 전 구간. [JEP 515](https://openjdk.org/jeps/515)·[Project CRaC](https://openjdk.org/projects/crac/)의 동기다. JEP 515 예시는 90ms → 73ms(19%)였다 — 짧은 프로그램에서는 개선폭도 짧다.
- **상주 메모리.** 힙만이 아니다.

| 항목 | 기본값 | 성격 |
|---|---|---|
| 힙 최대 (`-XX:MaxRAMPercentage`) | 가용의 25% | 컨테이너 한도와 따로 논다 — 명시 설정 사실상 필수 |
| 코드 캐시 (`-XX:ReservedCodeCacheSize`) | 240MB | JIT 산출물 — 힙 밖 |
| 메타스페이스 (`-XX:MaxMetaspaceSize`) | 제한 없음 | 클래스 메타데이터 — 네이티브 메모리 |
| 스레드 스택 (`-Xss`) | Linux/x64 1024KB | 스레드 수 × 이 값이 상주 비용 |

"JVM 메모리 = 힙"이라 생각하면 컨테이너에서 OOM Killer에게 죽는다. n-body에서 C++ 약 2.5MB일 때 JVM은 약 61MB를 썼다 — **하는 일이 작아도 런타임은 작아지지 않는다**는 것이 이 비용의 성질이다. [실무 의견]
- **튜닝 표면.** 위 표 자체가 비용이다 — "기본값으로 잘 도는데 한계에 부딪히면 알아야 할 것이 갑자기 많아진다."

이 넷을 합치면 JVM이 **틀리는 자리**가 보인다 — 호출마다 새로 뜨는 짧은 프로세스, 메모리가 귀한 다수의 작은 데몬, 배포처에 런타임을 깔기 어려운 환경. 인프라 도구를 Go로 가는 근거가 그것이다.

---

## 12. [실무 의견] 은행이 JVM에 수렴한 자리, 그리고 어긋나는 자리

> 출처: 원고 §12 — 공개 1차 출처로 전부 뒷받침되지 않는 해석이다. 위 절들과 구분해서 읽는다.

**수렴의 이유는 "빨라서"가 아니다.** 은행 코어의 지배 항은 CPU가 아니라 DB 왕복과 락 대기다. 그러면 언어 선택의 축은 성능이 아니라 **실패 모드**로 옮겨간다 — 은행에서 최악은 크래시가 아니라 **틀린 값으로 조용히 계속 도는 것**인데, 메모리 비안전 언어의 결함이 만드는 것이 정확히 그 계급이다. GC 언어에는 이 계급 자체가 없다.

**둘째 이유는 §10 그대로다** — 터졌을 때 열어볼 수 있는가. 25년치의 JDBC·트랜잭션·커넥션 풀·TLS 스택이 이 도메인에서 두들겨 맞으며 실패 모드가 문서화되어 있다는 것이, 새 런타임의 이론적 우월함보다 실무에서 자주 이긴다. "안정적"의 정직한 번역은 **"터지는 방식이 예측 가능하고 열어볼 도구가 있다"**이다.

**셋째, GC 반론이 실제로 소멸했다.** "JVM은 GC 때문에 금융에 못 쓴다"는 반론의 전제(수백 ms 일시정지)를 §8의 수치가 무너뜨린다. 다만 소멸한 것은 **반론**이지 **비용**이 아니다 — 저지연을 진지하게 추구하는 코드는 여전히 GC를 회피하는 설계를 한다(LMAX Disruptor가 링 버퍼를 기동 시 전부 선할당하는 이유). 금융 거래소를 JVM 위에 짓되 **할당을 안 하는 방식으로** 짓는다는 것이 실무의 실제 형태다.

**어긋나는 자리는 §11이 열거했다.** 그리고 그 경계는 은행 시스템 안에도 있다 — 코어는 한 번 떠서 몇 주를 도니 기동·워밍업이 상각되지만, 배포·감시 도구는 호출마다 뜨므로 같은 성질이 그대로 손해가 된다. 하나의 시스템 안에서도 층마다 답이 다르다.

---

## 핵심 문장

- **바이트코드·클래스로더·JIT·GC는 별개 기능이 아니라 "실행 시점까지 미룬다"는 한 결정의 결과다.**
- **JIT의 이점은 "나중에 컴파일해서"가 아니라 컴파일할 때 실행 통계를 알고 있어서다.**
- **되돌릴 수 있으니(deopt) 틀릴 수 있는 최적화를 공격적으로 해도 된다** — JVM 성능의 핵심 비대칭.
- **경합만 없애면 재배치를 머릿속에서 지워도 된다** — happens-before가 개발자에게 판 물건.
- **JVM이 값을 내는 조건은 하나로 줄어든다 — 오래 살아서 그 판단 비용을 상각할 수 있는가.**
- **은행이 JVM에 수렴한 이유는 "빨라서"가 아니라 실패 모드(조용한 오답이 없다)와 관측(열어볼 수 있다)이다.**

---

## 관련 자료

- 같은 컬렉션: [`c-cpp-csharp.md`](c-cpp-csharp.md)(C#은 IL·JIT·GC가 JVM과 동형) · [`go.md`](go.md)(같은 GC 진영의 가벼운 쪽) · [`rust.md`](rust.md)(GC 없이 컴파일 타임으로 안전을 사는 대비).
- 스펙 원문: [JVMS SE 21](https://docs.oracle.com/javase/specs/jvms/se21/html/) · [JLS SE 21 §17](https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html)(메모리 모델) · [HotSpot Glossary](https://openjdk.org/groups/hotspot/docs/HotSpotGlossary.html).
- GC 서사: [JEP 439](https://openjdk.org/jeps/439)(Generational ZGC) · [JEP 333](https://openjdk.org/jeps/333)(ZGC 원안) · [G1 Tuning Guide](https://docs.oracle.com/en/java/javase/21/gctuning/garbage-first-g1-garbage-collector1.html).
- 동시성 비용 실측: [LMAX Disruptor](https://lmax-exchange.github.io/disruptor/disruptor.html).

---

## 용어 풀이

- **바이트코드(Bytecode)** — 소스가 먼저 번역되는 중간 명령. JVM은 이 `class` 파일 형식만 상대하므로 Kotlin·Scala도 같은 런타임에 선다.
- **클래스로더(ClassLoader)** — 실행 중 클래스를 찾아 로드하는 장치. 부모에게 먼저 위임해 핵심 클래스 바꿔치기를 막는다.
- **JIT(Just-In-Time)** — 실행 중 바이트코드를 기계어로 컴파일하는 것. 실행 통계를 알기 때문에 정적 컴파일보다 나은 인라이닝이 가능하다.
- **티어드 컴파일(Tiered Compilation)** — C1(빠름)과 C2(공격적)를 5단계로 섞어 쓰는 것. 프로파일링 비용을 최소화하며 정점으로 끌어올린다.
- **탈최적화(Deoptimization)** — 추측이 깨졌을 때 컴파일 프레임을 인터프리터 프레임으로 되돌리는 것. 공격적 추측을 가능케 하는 안전망.
- **세대 가설(Weak Generational Hypothesis)** — "젊은 객체는 젊어서 죽고 늙은 객체는 오래 산다." 세대별 GC의 전제.
- **G1 / ZGC** — G1은 일시정지를 소프트 상한(기본 200ms)에 넣는 기본 컬렉터; ZGC는 로드 배리어로 복사를 동시화해 일시정지를 힙 크기에서 뗀 저지연 컬렉터.
- **happens-before** — 한 동작이 다른 동작에 보이고 앞선다는 순서 관계. 경합만 없으면 순차적 일관성을 보장받는다.
- **워밍업(Warmup)** — JIT가 정점 성능에 도달하기까지의 구간. 오래 도는 프로세스에서만 상각된다.
- **WORA(Write Once, Run Anywhere)** — 같은 바이트코드가 모든 플랫폼에서 돈다는 Java의 구호. 기동 비용의 근원이기도 하다.

---

## [Claude 추가] 더 알면 좋은 것

> 아래는 원고에 없던 배경 지식이다. 복습 시 본문(원고)과 섞어 인출하지 않는다.

- **타입 소거(Type Erasure).** Java 제네릭은 컴파일 후 타입 인자를 지워 `List<String>`이 런타임에 그냥 `List`가 된다. 후방 호환을 위해 택한 설계이고, C#의 실체화(reified) 제네릭과 갈리는 지점이다 — 같은 관리 런타임이라도 이 결정은 다르다.
- **JMM이 왜 "판 물건"인가.** 메모리 모델은 하드웨어마다 다른 재배치 규칙을 개발자에게서 감추고 "경합만 없애라"는 단일 계약으로 바꿔 준다. 이것이 없으면 volatile·synchronized의 의미가 CPU마다 달라진다 — 추상 기계를 발명한다는 §2 결정의 동시성 판(版)이다.
- **Escape Analysis와 스칼라 치환.** JIT는 "이 객체가 메서드 밖으로 새지 않는다"를 판정하면 힙 할당을 없애고 필드를 레지스터/스택으로 흩는다(scalar replacement). 그래서 "할당을 안 하는 방식으로 짓는다"(§12)를 컴파일러가 일부 자동으로 해 주기도 한다.
- **Project Loom(가상 스레드).** JDK 21의 가상 스레드는 블로킹 I/O를 런타임이 흡수해 thread-per-request 스타일로 스케일하게 한다 — JVM이 "무거운 스레드"라는 오래된 약점을 런타임 쪽에서 지운 최신 흐름이고, [`kotlin.md`](kotlin.md)의 코루틴과 "같은 문제, 반대 해법"으로 대비된다.
