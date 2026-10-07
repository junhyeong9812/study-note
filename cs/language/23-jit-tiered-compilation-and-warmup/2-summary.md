# language/23-jit-tiered-compilation-and-warmup — 계층 컴파일과 워밍업: 인터프리터 → C1 → C2, 그리고 역최적화 — 정리 (힌트)

## 해결하는 문제

JVM은 시작하자마자 최고 속도로 돌지 않는다. 같은 메서드가 호출될수록 빨라진다.

```text
  JDK 21 HotSpot, 같은 메서드를 반복 호출했을 때 1회 평균 (실험 1, 예시)

  호출      1~     1  ████████████████████████████  73~125us   인터프리터
  호출     11~   100  ██████████████████████         52~60us   인터프리터(프로파일 수집 중)
  호출    101~  1000  ███                           6.7~8.6us  C1(프로파일 코드) → C2 전환 중
  호출 10001~100000  █                             2.8~3.3us  C2
```

- *JIT(just-in-time) 컴파일*: 실행 중에 바이트코드를 기계어로 바꾸는 것. 자주 도는 코드만 골라서 한다.
- *워밍업*: JIT가 뜨거운 코드를 최적화해 최고 속도에 이를 때까지의 구간.
- 왜 처음부터 다 컴파일하지 않나: 컴파일 자체가 CPU·시간을 쓴다. 그리고 **실행해 봐야 아는 정보**(어느 분기가 자주 가나, 이 호출 지점에 어떤 타입이 오나)를 써야 더 잘 최적화된다.

쉬운 예: 새 직원.
- 첫날은 매뉴얼을 한 줄씩 읽으며 일한다(인터프리터).
- 자주 하는 일은 메모해 두고 빨리 한다(C1).
- 몇 주 뒤엔 "이 손님은 늘 같은 걸 시킨다"는 경험까지 써서 미리 준비한다(C2, 프로파일 기반 최적화).
- 손님 취향이 갑자기 바뀌면 준비해 둔 걸 버리고 다시 매뉴얼을 본다(역최적화).

똑같은 구조다.\
그래서 **배포 직후·스케일 아웃 직후**의 새 인스턴스는 느리다.

실무 예:
- 배포 직후 readiness는 통과했는데 몇 분간 p99가 몇 배로 뛴다.
- 평소와 다른 타입의 요청(새 결제 수단)이 섞이자 CPU가 잠깐 튄다(역최적화 후 재컴파일).
- `CodeCache is full. Compiler has been disabled.`(분할 캐시면 `CodeHeap '…' is full. …`) 경고 뒤 새로 뜨거워지는 코드가 컴파일되지 못해 인터프리터(또는 이미 있던 하위 단계 코드) 속도에 머문다.

컴파일·인터프리트·바이트코드의 기초는 [language/01](../01-compile-interpret-jit/2-summary.md)(원고 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md)의 바이트코드 절), 컴파일러 최적화 일반(인라이닝·데드 코드 제거)은 [language/22](../22-ir-and-optimization/2-summary.md)에 있다. 이 노트는 **HotSpot이 언제·무엇을 컴파일하고, 언제 버리는가**를 본다.

## 동작·원리

### 1. 다섯 단계 (JDK 21 HotSpot)

```text
                     프로파일 수집 ─────────────────────────────┐
  level 0 인터프리터 ──(호출·백엣지 카운터가 문턱 넘음)──▶ level 3 C1 + 전체 프로파일
     │                                                       │ (프로파일 충분)
     │                                                       ▼
     │                                                 level 4 C2 (프로파일 기반 최적화)
     │                                                       │
     └──────────────── 역최적화(deopt): 가정이 깨지면 ◀────────┘
  level 1 C1 최적화, 프로파일 없음 (사소한 메서드 — C2를 해도 같은 코드)
  level 2 C1 + 호출·백엣지 카운터만 (C2 큐가 길 때 잠시 거쳐 감)
```

- OpenJDK 21 소스 `compilationPolicy.hpp` 주석이 다섯 단계를 정의한다.
  - level 0 인터프리터(프로파일은 MDO에 기록), level 1 C1 프로파일 없음, level 2 C1 + 카운터, level 3 C1 + 전체 프로파일, level 4 C2.
  - *MDO(MethodData object)*: 메서드별 프로파일(분기 횟수, 호출 지점의 타입 등)을 담는 객체.
- 보통 경로는 0 → 3 → 4다. C2 큐가 길면 0 → 2 → (나중에) 3 → 4로 간다. 같은 주석은 level 3 코드가 level 2보다 약 30% 느리다고 적는다.
- 사소한 메서드는 첫 C1 컴파일 뒤 level 1로 끝낸다(C2를 해도 같은 코드라서).
- *C1*: 빨리 컴파일하는 클라이언트 컴파일러. *C2*: 오래 걸리지만 공격적으로 최적화하는 서버 컴파일러.

### 2. 언제 올라가나 — 카운터와 문턱

```text
  i = 호출 횟수, b = 루프 백엣지(뒤로 점프) 횟수, s = 컴파일 큐 길이에 따른 배율

  0 → 3 :  i > Tier3InvocationThreshold·s  또는  (i > Tier3MinInvocationThreshold·s  그리고  i + b > Tier3CompileThreshold·s)
  3 → 4 :  같은 식을 Tier4* 값과 MDO의 카운트로
  OSR   :  b > TierXBackEdgeThreshold·s          (루프 하나가 오래 돌 때 실행 중에 갈아 끼움)
  s     =  queue_size_X / (TierXLoadFeedback · compiler_count_X) + 1
```

- 식은 `compilationPolicy.hpp` 주석 그대로다. 큐가 길수록 `s`가 커져 문턱이 올라간다.
- `-XX:+PrintFlagsFinal`로 본 JDK 21.0.12 기본값(이 컨테이너, `--cpus=2`)

```text
  Tier3InvocationThreshold = 200     Tier3CompileThreshold = 2000    Tier3BackEdgeThreshold = 60000
  Tier4InvocationThreshold = 5000    Tier4CompileThreshold = 15000   Tier4BackEdgeThreshold = 40000
  CICompilerCount = 2 (ergonomic)    ReservedCodeCacheSize = 251658240 (240MB, ergonomic)
  TieredCompilation = true           SegmentedCodeCache = true
```

- *OSR(on-stack replacement)*: 메서드가 아직 실행 중인데, 루프 중간에서 컴파일된 코드로 갈아타는 것. `PrintCompilation`에서 `%`로 표시된다.
- `CICompilerCount = 2`: CPU 2개 컨테이너라 C1·C2 컴파일 스레드가 적다. 컴파일 큐가 밀리면 워밍업이 길어진다(해석).

### 3. 프로파일로 하는 최적화와 그 대가 — 역최적화

```text
  호출 지점 xs[i].area()  — 프로파일: Sq 100%
  C2:  if (x.klass != Sq) → uncommon trap (역최적화)       ← "가드"
       else  { Sq.area() 본문을 그대로 인라인 }             ← 가상 호출이 사라지고 더 최적화된다

  새 타입 Circle 도착 → 가드 실패 → 인터프리터로 돌아감 → 프로파일 갱신 → 재컴파일
                                                           (이번엔 Sq·Circle·Tri: 가상 호출 유지)
```

- *인라이닝*: 호출을 함수 본문으로 바꿔 넣는 것. 다른 최적화(상수 전파, 탈출 분석)의 문을 연다.
- *타입 프로파일*: 호출 지점마다 실제로 온 수신 객체 타입과 횟수. 메서드별 MDO에 기록된다. 컴파일된 코드의 인라인 캐시와 비슷한 정보지만 별개 장치다([language/17](../17-dispatch-and-polymorphism-mechanics/2-summary.md)).
- *역최적화(deoptimization)*: 컴파일할 때 둔 가정이 깨지면, 그 실행을 컴파일된 코드에서 인터프리터 상태로 되돌리는 것. 컴파일된 코드 자체는 바로 버려지기도 하고(`made not entrant`) 재컴파일 전까지 유지되기도 한다.
  - *uncommon trap*: "거의 안 일어날 것"으로 보고 컴파일하지 않은 경로. 실제로 가면 역최적화가 일어난다.
- `PrintInlining`으로 본 실험 2의 같은 호출 지점(`Deopt::total @ 27`)
  - 워밍업 뒤: `Deopt$Sq::area (10 bytes) inline (hot)`, `\-> TypeProfile (844846/844846 counts) = Deopt$Sq`
  - 새 타입 등장 뒤 재컴파일: `Deopt$Shape::area (0 bytes) virtual call`
- `made not entrant`는 두 경우에 찍힌다. 둘을 섞어 읽지 않는다.
  - 더 높은 단계 코드로 **정상 교체**될 때(실험 1: level 3 → 4 뒤 level 3 코드).
  - 가정이 깨져 **역최적화**될 때(실험 2: level 4 코드). 이유는 `-Xlog:deoptimization=debug`의 `reason`으로 가른다.

### 4. 코드 캐시 — 컴파일된 코드가 사는 곳

```text
  JDK 21, SegmentedCodeCache=true, 240MB (실험 1 프로세스 종료 시 -XX:+PrintCodeCache)
  ┌ 'non-nmethods'         5692Kb   used 1262Kb   인터프리터·스텁·어댑터
  ├ 'profiled nmethods'  120032Kb   used  203Kb   level 2·3 (C1 + 프로파일)
  └ 'non-profiled nmethods' 120036Kb used   74Kb   level 1·4 (C1 최종·C2)
  CodeCache: size=245760Kb, used=1539Kb ... full_count=0
  Compilation: enabled, stopped_count=0
```

- *nmethod*: 컴파일된 Java 메서드 하나의 기계어 덩어리.
- 크기: `java` 도구 문서(JDK 21)는 기본 최대 240MB, 계층 컴파일을 끄면(`-XX:-TieredCompilation`) 48MB라고 적는다. 위 출력의 245760Kb가 240MB다.
- 코드 캐시가 차면 OpenJDK 21 `codeCache.cpp`의 `report_codemem_full()`이 경고를 낸다.
  - 분할 캐시면 `CodeHeap '<이름>' is full. Compiler has been disabled.` + `Try increasing the code heap size using -XX:<플래그>=`.
  - 분할하지 않은 캐시면 `CodeCache is full. Compiler has been disabled.` + `Try increasing the code cache size using -XX:ReservedCodeCacheSize=`.
- 컴파일러가 꺼지면 새 컴파일이 멈춘다. 이미 컴파일된 코드는 계속 쓰이고, 새로 뜨거워지는 코드는 인터프리터나 하위 단계 코드에 머문다. 공간이 회수되면 컴파일이 다시 켜진다(`codeCache.cpp`, `restarted_count`). `UseCodeCacheFlushing`(기본 true)이 오래된 코드를 비워 공간을 되찾으려 한다.
- 하한: `-XX:ReservedCodeCacheSize=2m`은 `Invalid ReservedCodeCacheSize: 2048K. Must be at least InitialCodeCacheSize=2496K.`로 거부됐다(JDK 21.0.12).

### 실험 1: 워밍업 계단 — 기본 / C1만 / 인터프리터만

```java
static long work(int[] a) {                     // a.length = 1,000
    long s = 0;
    for (int i = 0; i < a.length; i++) s += (a[i] * 31L) ^ (s >>> 3);
    return s;
}
// 호출 1, 2~10, 11~100, 101~1000, 1001~10000, 10001~100000 구간별 1회 평균 시간
```

환경: i7-13700HX, `eclipse-temurin:21-jdk`(21.0.12), `--cpus=2`, 옵션별 3회(첫 실행 1회 + 묶음 실행 2회).

```text
                     기본(계층)         -XX:TieredStopAtLevel=1   -Xint
  호출      1        74.5~124.9us       64.6~87.1us              70.8~164.7us
  호출   11~100      58.1~60.0us        47.7~57.7us              59.3~65.3us
  호출  101~1000      8.2~8.6us          3.4~3.8us               63.9~68.2us
  호출 1001~10000     4.3~4.4us          3.7~4.1us               61.5~66.3us
  호출 10001~100000   3.0~3.3us          3.3~3.6us               62.8~69.3us

  사실 점검 재실행(옵션별 2회, 같은 조건)
  호출      1        72.7~101.4us       78.5~84.3us              69.8~76.9us
  호출   11~100      52.1~53.5us        53.2~53.5us              65.8~73.4us
  호출  101~1000      6.7~7.5us          3.8~3.9us               58.5~65.4us
  호출 1001~10000     3.9~4.3us          3.8~4.0us               63.0~64.2us
  호출 10001~100000   2.8~3.2us          3.5~3.8us               62.1~62.8us
```

`-XX:+PrintCompilation`(기본, `Warmup::work`만 추림)

```text
  146  126 %     3       Warmup::work @ 4 (33 bytes)                  ← 루프 OSR, level 3
  147  127       3       Warmup::work (33 bytes)                      ← 메서드, level 3
  161  135 %     4       Warmup::work @ 4 (33 bytes)                  ← OSR, level 4 (C2)
  174  126 %     3       Warmup::work @ 4 (33 bytes)   made not entrant   ← 정상 교체
  174  140       4       Warmup::work (33 bytes)                      ← 메서드, level 4
  183  127       3       Warmup::work (33 bytes)   made not entrant
  (TieredStopAtLevel=1에서는 같은 자리에 level 1만 두 줄)
```

- `-Xint`는 끝까지 약 60~70us다. 이 구간에서 JIT의 이득은 약 20배다.
- 101~1000 구간에서 기본(재실행 포함 6.7~8.6us)이 C1만(3.4~3.9us)보다 느리다. 기본 경로의 level 3 코드는 프로파일을 모으느라 느리다(위 30% 서술과 같은 방향 — 해석).
- 끝 구간에서 C2(재실행 포함 2.8~3.3us)와 C1(3.3~3.8us)의 차이가 작다. 이 루프는 `s`가 매 반복 앞 값에 의존해 C2가 더 할 일이 적다(해석 — 생성 코드는 확인하지 않았다).

### 실험 2: 타입 프로파일이 깨질 때 — 역최적화와 재컴파일

```java
interface Shape { double area(); }
record Sq(double s) implements Shape { ... }  record Circle(...) ...  record Tri(...) ...
static double total(Shape[] xs) { double t = 0; for (Shape x : xs) t += x.area(); return t; }
// 1) Sq만 1,000개 배열로 20,000회 × 2   2) Sq·Circle·Tri 섞은 배열로 200회, 이어서 20,000회
```

환경: 위와 같음, 3회(로그 없이) + 로그 실행 2회 + 사실 점검 재실행 3회.

```text
                       1회        2회        3회
  [단형 측정]          2.24us     2.07us     2.21us
  [혼합 첫 구간 200회]  26.16us    26.11us    23.91us     ← 평균 급등 + 역최적화 트랩 관찰 구간
  [혼합 재컴파일 뒤]    6.12us     6.44us     6.92us      ← 가상 호출 유지(메가모픽)
  재실행 3회: 단형 1.86 / 2.30 / 2.12us, 혼합 첫 구간 31.66 / 27.38 / 22.48us, 재컴파일 뒤 5.98 / 8.42 / 8.16us

  -Xlog:deoptimization=debug (새 타입 등장 직후)
  cid=  18     level=4 Deopt.total([LDeopt$Shape;)D trap_bci=27 class_check maybe_recompile
  cid=  17 osr level=4 Deopt.total([LDeopt$Shape;)D trap_bci=27 osr_bci=11 class_check maybe_recompile
```

- `trap_bci=27`은 바이트코드 27번, 즉 `x.area()` 호출 지점이다. `class_check`가 "타입 가드 실패"다.
- 첫 200회 평균이 단형의 약 11~17배로 뛰었다(같은 실행 안의 비율, 6회). 운영에서는 이것이 "간헐적 CPU·지연 스파이크"로 보인다.
- 재컴파일 뒤에도 단형보다 약 3~4배 느리다. 감속과 가상 호출(`virtual call`)이 함께 관찰됐다. 인라인이 사라진 것이 큰 몫으로 보이지만, 섞인 타입의 `area()` 본문도 달라 그 몫을 분리하지는 않았다(해석).
- 위 로그는 트랩 발생만 보여 준다. 첫 200회 중 몇 번이 인터프리터로 돌았는지, 재컴파일이 언제 끝났는지는 재지 않았다. `maybe_recompile`은 기존 코드를 곧바로 무효화하지 않을 수도 있다(`deoptimization.hpp`: "recompile the nmethod; need not invalidate").

## 쓰이는 자료구조·알고리즘

- **호출·백엣지 카운터** — 메서드와 루프마다 정수 카운터. 문턱과 큐 길이 배율로 컴파일 시점을 정한다(위 식).
- **타입 프로파일(MDO)** — 호출 지점마다 (타입, 횟수) 몇 칸(JDK 21 `TypeProfileWidth` 기본 2). C2는 이것을 보고 1종이면 단형(가드 + 인라인), 2종이면 양형, 그 이상이면 가상 호출로 컴파일한다.
- **인라인 캐시(CompiledIC)** — 컴파일된 코드의 호출 지점에 붙는 별개 장치. JDK 21 HotSpot에서는 단형 상태에서 다른 타입을 만나면 바로 메가모픽(vtable 스텁)으로 바뀐다(`sharedRuntime.cpp`의 `set_to_megamorphic`). 디스패치 기계는 [language/17](../17-dispatch-and-polymorphism-mechanics/2-summary.md), 하드웨어 분기 예측과의 비유는 [architecture/18](../../architecture/18-pipelining-and-branch-prediction/2-summary.md).
- **호출 그래프** — 인라이닝은 호출 그래프를 따라 내려가며 크기·빈도 예산 안에서 본문을 펼친다.
- **우선순위 큐(컴파일 큐)** — 컴파일 요청이 쌓이는 곳. `jcmd <pid> Compiler.queue`로 본다.
- **세그먼트 힙** — 코드 캐시를 수명·종류별 3구역으로 나눠 단편화와 탐색 비용을 줄인다.

## 적용 — 풀어나가는 법

### 1. "배포 직후만 느리다"를 확인하는 순서

1. **새 인스턴스만 느린가?** 인스턴스별 p99를 나눠 본다. 오래된 인스턴스는 멀쩡하고 새 것만 느리면 워밍업 후보다.
2. **첫 요청 비용과 워밍업을 가른다.** 첫 요청의 수십 ms는 클래스 로딩·링크가 크다. 그 뒤 수십~수천 요청 동안 줄어드는 것은 JIT다([reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) 관찰 2·3).
3. **컴파일 활동을 본다.**

```bash
java -XX:+PrintCompilation -jar app.jar > comp.log  # 열: 시각(ms) ID 표시(%=OSR) 단계 메서드 — 시작 직후 단계 3·4가 몰리는지
jcmd <pid> Compiler.queue                    # 큐에 쌓인 컴파일 요청
jcmd <pid> Compiler.codecache                # 세 구역 사용량, full_count, Compilation: enabled
java -Xlog:deoptimization=debug -jar app.jar # 역최적화 이유(class_check, unstable_if 등)
```

### 2. 워밍업 전략

- **자기 자신에게 대표 요청을 보낸 뒤 Ready.** readiness는 "포트 열림"이 아니라 "뜨거운 경로가 컴파일됨"이어야 한다. Kubernetes 예시·startupProbe는 [reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md).
- **대표성 있는 워밍업.** 운영에 섞일 타입·분기를 고루 지나게 한다. 한 타입만 데우면 실험 2처럼 운영 트래픽에서 역최적화가 난다.
- **AOT 캐시로 시작·워밍업을 줄인다.** JDK 24 JEP 483은 클래스 로드·링크 상태를, JDK 25 JEP 515는 메서드 프로파일까지 캐시에 담는다. JEP 515의 목표: 프로파일을 이전 실행에서 가져와 JIT가 "시작 직후 바로" 네이티브 코드를 만들게 하는 것. 자세한 비교는 [24번](../24-aot-native-image-and-startup/2-summary.md).
- **짧게 사는 프로세스**(CLI·배치 한 번)는 `-XX:TieredStopAtLevel=1`이 나을 수 있다. 실험 1에서 C1만으로 101~1000 구간이 더 빨랐다. 대신 오래 돌면 C2의 최고 성능을 잃는다.

### 3. 코드 캐시를 지킨다

- 클래스·람다·프록시를 대량으로 만드는 앱(동적 언어 엔진, 거대한 모놀리스)은 `jcmd Compiler.codecache`의 `max_used`를 지표로 본다.
- 부족하면 `-XX:ReservedCodeCacheSize`를 늘린다. 분할 캐시면 경고가 알려 주는 구역 플래그(`-XX:NonProfiledCodeHeapSize` 등)를 조정한다.

## 장애 시나리오와 대처

### 1. 배포 직후 p99 급등 — readiness는 통과했는데 JIT가 안 끝났다 (⚠)

- **현상**: 롤링 배포 뒤 몇 분간 p99가 몇 배, 평균은 조금만 오른다. 새 파드에서만 나온다.
- **보이는 형태**: 새 파드 CPU가 높다(앱 스레드 + C1/C2 컴파일 스레드). `PrintCompilation`에 level 3·4 컴파일이 몰린다. 시간이 지나면 저절로 가라앉는다.
- **원인**: 인터프리터·level 3 코드로 트래픽을 받는다. 실험 1에서 C2 전 구간은 C2 코드보다 약 2~20배 느렸다(첫 호출은 그 이상).
- **대처**: 워밍업 요청 후 Ready, 새 파드에 트래픽을 천천히(가중치) 올리기, AOT 캐시(JDK 24+/25+). CPU 한도가 작으면 컴파일 스레드가 앱과 경쟁하니 시작 직후 CPU 여유를 둔다(해석).

### 2. 역최적화 연쇄 → 간헐적 CPU 스파이크 (⚠)

- **현상**: 평소엔 안정적인데 특정 시점(새 기능 플래그 켜짐, 드문 요청 유형)에 CPU와 지연이 잠깐 튄다.
- **보이는 형태**: `-Xlog:deoptimization=debug`에 같은 메서드의 `class_check`·`unstable_if` `maybe_recompile`이 반복. `PrintCompilation`에 같은 메서드의 level 4 `made not entrant` → 재컴파일이 반복.
- **원인**: 단형으로 굳은 호출 지점에 새 타입이 들어오면 가드가 실패해 역최적화된다. 재컴파일 전까지 느린 코드로 돈다(실험 2: 약 11~17배).
- **대처**: 워밍업에 모든 타입·분기를 포함한다. 같은 메서드가 계속 재컴파일되면(jdk21u `globals.hpp`: 같은 종류 트랩이 `PerMethodTrapLimit`=100을 넘으면 그 투기를 줄이고, 재컴파일이 `PerMethodRecompilationCutoff`=400회를 넘으면 그 메서드는 인터프리터에 머문다) 그 지점을 다형성이 덜한 구조로 나누는 것을 검토한다.

### 3. `CodeCache is full. Compiler has been disabled.` (⚠)

- **현상**: 오래 돈 프로세스가 어느 순간부터 새 코드 경로가 느리고, 잘 회복되지 않는다.
- **보이는 형태**: 위 경고(분할 캐시면 `CodeHeap 'non-profiled nmethods' is full...`). `jcmd Compiler.codecache`의 `full_count` > 0, `Compilation: disabled`.
- **원인**: 코드 캐시가 가득 차 새 컴파일이 멈췄다. 동적으로 생성되는 클래스가 계속 늘거나 캐시가 작게 설정돼 있다.
  - JDK 21 `compileBroker.cpp` `handle_full_code_cache()`: `UseCodeCacheFlushing`(기본 true)이면 컴파일을 **멈추고**, 코드 언로딩으로 공간이 생기면 `codeCache.cpp` `maybe_restart_compiler()`가 다시 켠다(`Compiler.codecache`의 `stopped_count`·`restarted_count`). 이 플래그를 끄면 영구히 끈다. 공간이 계속 모자라면 멈춘 시간이 길어진다.
- **대처**: `ReservedCodeCacheSize`·구역 크기를 늘리고, 클래스 생성 누수(프록시·람다·스크립트 엔진 재생성)를 찾는다. 이 노트에서는 작은 캐시(하한 2496K)로 재현을 시도했지만 시도한 규모에서는 경고가 나오지 않았다. 문구는 소스로만 확인했다.

### 4. 마이크로벤치마크가 거짓말을 한다

- **현상**: 로컬 측정에서는 A가 빨랐는데 운영에서는 B가 빠르다.
- **원인**: 측정이 워밍업 구간(인터프리터·level 3)을 섞었거나, 한 타입만으로 데워 단형 인라인 결과를 쟀다(실험 2의 단형 약 2us vs 운영 같은 혼합 6~8us).
- **대처**: 워밍업 구간을 버리고 여러 번 잰다. 운영과 같은 타입 분포로 데운다. 가능하면 JMH를 쓴다(이 노트 실험은 JMH 없이 직접 측정 — 값은 해석의 근거로만).

## 핵심 문장

- HotSpot은 인터프리터로 시작해 호출·루프 카운터가 문턱을 넘은 코드만 C1(프로파일 수집) → C2(프로파일 기반 최적화)로 올린다.
- 워밍업이 필요한 이유는 컴파일 비용과, 실행해 봐야 아는 프로파일 정보 두 가지다.
- C2는 프로파일을 가정으로 삼아 가드 + 인라인을 한다. 가정이 깨지면 역최적화로 되돌아가고 재컴파일한다.
- `made not entrant`는 정상 교체와 역최적화 모두에 찍힌다. 이유는 역최적화 로그로 가른다.
- 코드 캐시가 차면 새 컴파일이 멈추고, 새로 뜨거워지는 코드는 인터프리터나 하위 단계 코드에 머문다.
- 배포 직후 p99 급등은 "Ready = 포트 열림"이 원인일 때가 많다. 대표 요청으로 데운 뒤 Ready로 만든다.

## 관련 주제·근거

- 선행
  - [01-compile-interpret-jit](../01-compile-interpret-jit/2-summary.md) · [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md) · [17-dispatch-and-polymorphism-mechanics](../17-dispatch-and-polymorphism-mechanics/2-summary.md)
  - 원고 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md) — 바이트코드·PVM
- 후속·연결
  - [24-aot-native-image-and-startup](../24-aot-native-image-and-startup/2-summary.md) — 닫힌 세계 AOT, AOT 캐시
  - [25-lto-pgo-and-binary-size](../25-lto-pgo-and-binary-size/2-summary.md) — 빌드 시점의 프로파일 기반 최적화
  - [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) — 콜드 스타트, 워밍업 후 Ready, AppCDS·AOT 캐시 측정
  - [architecture/18-pipelining-and-branch-prediction](../../architecture/18-pipelining-and-branch-prediction/2-summary.md) · [architecture/09-isa-and-machine-code](../../architecture/09-isa-and-machine-code/2-summary.md)
- 근거
  - OpenJDK jdk21u 소스 `src/hotspot/share/compiler/compilationPolicy.hpp` — level 0~4 정의, 0→3·3→4·OSR 문턱 식, 큐 길이 배율 `s`, level 3이 level 2보다 약 30% 느림 <https://github.com/openjdk/jdk21u/blob/master/src/hotspot/share/compiler/compilationPolicy.hpp>
  - OpenJDK jdk21u 소스 `src/hotspot/share/runtime/globals.hpp` — `PerMethodTrapLimit`(100, "Limit on traps (of one kind) in a method")·`PerMethodRecompilationCutoff`(400, "After recompiling N times, stay in the interpreter") <https://github.com/openjdk/jdk21u/blob/master/src/hotspot/share/runtime/globals.hpp>
  - OpenJDK jdk21u 소스 `src/hotspot/share/compiler/compileBroker.cpp` `handle_full_code_cache()`(멈춤 vs 영구 비활성) <https://github.com/openjdk/jdk21u/blob/master/src/hotspot/share/compiler/compileBroker.cpp>
  - OpenJDK jdk21u 소스 `src/hotspot/share/code/codeCache.cpp` `report_codemem_full()` — 경고 문구 두 종류, `maybe_restart_compiler()` <https://github.com/openjdk/jdk21u/blob/master/src/hotspot/share/code/codeCache.cpp>
  - OpenJDK jdk21u 소스 `runtime/deoptimization.hpp`(Action_maybe_recompile "need not invalidate") · `runtime/sharedRuntime.cpp`(인라인 캐시 단형 → `set_to_megamorphic`) · `runtime/globals.hpp`(`TypeProfileWidth` 기본 2) <https://raw.githubusercontent.com/openjdk/jdk21u/master/src/hotspot/share/runtime/deoptimization.hpp>
  - JEP 483 "Ahead-of-Time Class Loading & Linking"(JDK 24) <https://openjdk.org/jeps/483> · JEP 515 "Ahead-of-Time Method Profiling"(JDK 25) <https://openjdk.org/jeps/515>
  - `java` 도구 문서(JDK 21) — `-Xint`(인터프리터만), `-XX:ReservedCodeCacheSize`(기본 최대 240MB, 계층 컴파일을 끄면 48MB, 초기 크기보다 작으면 안 됨) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
- 실험 목록(i7-13700HX, `eclipse-temurin:21-jdk` 21.0.12, `--cpus=2 --network none`)
  - 실험 1: `Warmup.java` 구간별 1회 평균 — 기본 / `-XX:TieredStopAtLevel=1` / `-Xint` 각 3회(+ 점검 재실행 각 2회), `-XX:+PrintCompilation` 2회, `-XX:+PrintFlagsFinal`, `-XX:+PrintCodeCache`
  - 실험 2: `Deopt.java` 단형 → 혼합 — 3회(+ 점검 재실행 3회) + `-XX:+PrintCompilation`·`-Xlog:deoptimization=debug`·`-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining`
  - 보조: `jcmd <pid> help`(Compiler.* 명령 목록)·`Compiler.codecache` 출력, `ReservedCodeCacheSize=2m` 거부 메시지. 코드 캐시 가득 참 재현 시도(작은 메서드 8,000개·`ReservedCodeCacheSize=2496k`)는 경고가 나오지 않아 싣지 않았다
