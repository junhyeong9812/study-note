# reliability/38-microbenchmarking — JMH·워밍업·포크·데드 코드 제거·결과 비교의 통계 — 정리 (힌트)

## 해결하는 문제

"`StringBuilder`와 `+` 중 뭐가 빠르지?" 같은 질문을 `System.nanoTime()` 두 번으로 재면, 숫자는 나오지만 그 숫자가 무엇을 잰 것인지 알기 어렵다.\
JVM은 실행 중에 코드를 계속 바꾼다(인터프리터 → JIT 컴파일 → 재컴파일). 그리고 결과를 안 쓰는 계산은 지워 버리기도 한다.

```text
 같은 compute(x) — 무엇을 쟀나 (아래 실험, JMH 1.37, JDK 21)
 결과를 버린 벤치마크      1.1 ns/op   ← 빈 메서드(baseline 1.1ns)와 같다 = 계산이 사라졌다
 결과를 반환한 벤치마크    37 ns/op    ← 실제 계산
 입력이 final 상수         1.2 ns/op   ← 계산이 미리 접혔다
```

- *마이크로벤치마크(microbenchmark)*: 메서드 하나, 자료구조 연산 하나처럼 작은 코드 조각의 성능을 재는 것.
- *JMH(Java Microbenchmark Harness)*: OpenJDK가 만든 자바 마이크로벤치마크 도구. 워밍업·반복·별도 JVM 실행(포크)·결과 소비를 대신 처리한다.

쉬운 예: 달리기 기록을 재는데 (1) 몸도 안 푼 첫 바퀴를 재거나, (2) 선수가 지름길로 빠졌는데 모르고 재거나, (3) 한 번 재고 끝내는 것과 같다.

똑같은 구조다.\
실무 예: 직렬화 라이브러리 선택, 해시 함수·정렬 비교, 핫 경로의 객체 생성 줄이기, "이 리팩터링이 느려지나" 회귀 확인.\
단, 마이크로벤치마크 결과가 서비스 지연을 바꾸는지는 별개다 — 그 구간이 전체에서 차지하는 비율로 판단한다(→ [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md)).

## 동작·원리

### 1. JVM이 측정을 왜곡하는 세 가지

```text
 ① 워밍업    호출 횟수 ──>  인터프리터 ── C1 컴파일 ── C2 컴파일(최적화)
            ns/op       300           ~100              ~25      (아래 실험 2의 곡선 — 단계 대응은 해석)
 ② 제거·접기  결과를 안 쓰면 계산 삭제(DCE), 입력이 상수면 결과를 미리 계산(constant folding)
 ③ 프로파일   JIT는 "지금까지 본 타입·분기"로 최적화 → 앞서 돈 벤치마크가 뒤 벤치마크의 코드를 바꾼다
```

- *JIT(Just-In-Time) 컴파일*: 자주 실행되는 메서드를 실행 중에 기계어로 컴파일하는 것. HotSpot은 빠른 C1과 최적화를 많이 하는 C2를 단계적으로 쓴다(세부는 [language/22-ir-and-optimization](../../language/22-ir-and-optimization/2-summary.md)).
- *OSR(On-Stack Replacement)*: 오래 도는 루프를 실행 도중 컴파일된 버전으로 바꾸는 것. 손으로 짠 `for` 루프 측정은 OSR 버전을 재게 되는데, 이것은 일반 호출 경로와 다르게 최적화될 수 있다.
- *DCE(Dead-Code Elimination)*: 결과가 어디에도 쓰이지 않는 계산을 지우는 최적화.
- *constant folding(상수 접기)*: 입력이 컴파일 시점에 알려진 상수면 결과를 미리 계산해 넣는 최적화.

### 2. JMH가 하는 일

```text
 java -jar benchmarks.jar  (기본값 — JMH 1.37 runner/Defaults.java)
 ├─ fork 1 (새 JVM)  ── 워밍업 5회 × 10초 ── 측정 5회 × 10초
 ├─ fork 2 (새 JVM)  ── ...
 └─ fork 5           ── ...                   → 25개 측정값으로 평균·오차(신뢰구간)
```

- 기본값(JMH 1.37 `Defaults.java`): 포크 5, 워밍업 5회·10초, 측정 5회·10초, 스레드 1, 모드 Throughput(초당 연산 수).
- **포크**: 벤치마크마다 새 JVM을 띄운다. 앞선 벤치마크의 JIT 프로파일이 섞이지 않고, JVM 실행 사이의 변동(run-to-run variance)도 표본에 들어간다(jmh-samples `JMHSample_12_Forking`, `_13_RunToRun`).
- **반환값·`Blackhole`**: 벤치마크 메서드가 값을 반환하면 JMH가 그 값을 `Blackhole`로 "소비"해 DCE를 막는다. 결과가 둘 이상이면 합쳐서 반환하거나 `Blackhole.consume()`에 넣는다(`JMHSample_08_DeadCode`, `_09_Blackholes`).
  - *Blackhole*: 값을 받아서 JIT가 "이 값은 쓰인다"고 믿게 만드는 JMH 객체. 실제로는 아무 일도 안 하는 것처럼 보이도록 비용이 작게 설계됐다.
- **`@State` 필드에서 입력 읽기**: 입력을 `final`이 아닌 인스턴스 필드에서 읽어야 상수 접기를 피한다. 샘플 주석: "IDE가 이 필드를 final로 하라고 해도 믿지 마라"(`JMHSample_10_ConstantFold`).
- **루프 금지**: 벤치마크 안에서 `for`로 반복하지 않는다. JIT가 루프 반복을 합쳐(언롤·파이프라이닝) 한 번의 비용이 실제보다 작게 나온다(`JMHSample_11_Loops`). 반복은 JMH가 한다.

### 실험 1: DCE·상수 접기·Blackhole (JMH)

```java
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3, time = 1) @Measurement(iterations = 5, time = 1) @Fork(1)
public class Pitfalls {
    int x = 42;                 // final이 아닌 필드: JIT가 값을 미리 알 수 없다
    final int fx = 42;          // final 상수: 계산을 통째로 접을 수 있다

    int compute(int d) {        // JMHSample_08/10과 같은 모양(샘플은 double·Math.PI, 여기서는 int·42)
        for (int c = 0; c < 10; c++) d = d * d / 42;
        return d;
    }

    @Benchmark public void baseline() { }
    @Benchmark public void deadCode() { compute(x); }               // 결과를 버림
    @Benchmark public int returned() { return compute(x); }          // 반환 = Blackhole로 소비
    @Benchmark public int constantFold() { return compute(fx); }     // 입력이 상수
    @Benchmark public void twoWrong() { compute(x); compute(x + 1); } // 둘 다 버림
    @Benchmark public void twoBlackhole(Blackhole bh) { bh.consume(compute(x)); bh.consume(compute(x + 1)); }
}
```

(실험, JMH 1.37, Docker eclipse-temurin:21-jdk(Temurin 21.0.12) `--cpus=2`, 짧게 줄인 설정: 포크 1·워밍업 3×1초·측정 5×1초, 호스트 부하 높음, 2026-10-01)

```text
Benchmark              Mode  Cnt   Score    Error  Units
Pitfalls.baseline      avgt    5   1.108 ±  0.208  ns/op
Pitfalls.constantFold  avgt    5   1.219 ±  0.180  ns/op
Pitfalls.deadCode      avgt    5   1.113 ±  0.068  ns/op
Pitfalls.returned      avgt    5  37.475 ± 16.724  ns/op
Pitfalls.twoBlackhole  avgt    5  65.376 ± 22.112  ns/op
Pitfalls.twoWrong      avgt    5   1.141 ±  0.270  ns/op
```

- 사실 점검 재실행(같은 설정, `-prof gc` 추가): baseline 1.088, constantFold 1.066, deadCode 1.078, returned 35.245 ± 13.112, twoBlackhole 63.537, twoWrong 1.110 ns/op — 같은 모양이다.
- 관찰 1 — `deadCode`·`twoWrong`이 빈 메서드(`baseline`)와 같은 약 1.1ns다. 커리큘럼 ⚠의 "결과가 0.3ns/op → DCE"와 같은 증상이다(절대값은 기계마다 다르다). **빈 메서드와 같은 숫자 = 계산이 사라졌다는 신호**다.
- 관찰 2 — `constantFold`도 약 1.2ns다. 입력이 `final` 상수라 결과를 미리 계산했다.
- 관찰 3 — `returned` 37ns, `twoBlackhole` 65ns(약 2배)로 계산이 실제로 측정됐다.
- 관찰 4 — Error 칸은 JMH가 낸 99.9% 신뢰구간의 반폭이다(로그: `CI (99.9%): [20.751, 54.199] (assumes normal distribution)`). 반복 5회·공유 호스트라 ±45%로 넓다. 이 상태로는 37ns와 50ns도 구분할 수 없다.
- JMH 1.37은 이 JVM에서 "Compiler Blackholes"를 실험적으로 쓴다고 경고를 냈다. Blackhole 방식이 다르면 결과도 달라질 수 있으니, 비교는 같은 JVM·같은 Blackhole 모드끼리 한다(JMH 출력 문구).

### 실험 2: JMH 없이 `nanoTime` 루프로 재면

```java
for (int batch = 1; batch <= 300; batch++) {          // 같은 일을 1만 번씩 묶어 잰다
    long t0 = System.nanoTime();
    int s = 0;
    for (int i = 0; i < 10_000; i++) s += compute(x + i);
    sink += s;
    print(batch, (System.nanoTime() - t0) / 10_000.0);
}
```

(실험, 같은 환경, `java Naive.java` 2회 실행)

```text
묶음(1만 회)   ns/op
    1          319.17
    2          188.21
    3          169.44
   10          111.08
   30          128.01
  100           29.44
  300           70.17
반복 0: 결과 버림 35.042 ns/op, 결과 사용 38.995 ns/op
반복 1: 결과 버림 39.250 ns/op, 결과 사용 37.697 ns/op
반복 2: 결과 버림 35.566 ns/op, 결과 사용 36.313 ns/op
```

두 번째 실행의 묶음 값: 296.51 / 167.62 / 168.62 / 107.45 / 148.80 / 24.89 / 32.74.

- 관찰 1 — 같은 코드인데 첫 묶음(319ns)과 100번째 묶음(29ns)이 10배 차이다(사실 점검 재실행 2회: 314 → 29ns, 301 → 40ns — 약 8~11배. 30번째 묶음은 40ns·121ns로 실행마다 크게 달랐다). 워밍업 구간을 섞어 평균 내면 숫자가 의미를 잃는다.
- 관찰 2 — 300번째 묶음이 한 번은 70ns, 한 번은 33ns였다. 워밍업이 끝난 뒤에도 공유 호스트 잡음·GC·재컴파일이 끼어든다. 한 번 잰 값으로 결론 내리면 안 된다.
- 관찰 3 — 이 루프에서는 "결과 버림"이 지워지지 **않았다**(35ns ≈ 결과 사용 37ns). JMH 실험 1에서는 지워졌다. 제거 여부는 JIT가 주변 코드(OSR 루프·인라이닝 상태)를 보고 정하므로 **소스만 보고 예측할 수 없다.** 그래서 "결과를 반드시 소비"를 도구 규칙으로 강제한다.

### 실험 3: 포크 없이 여러 벤치마크를 이어 돌리면 (프로파일 오염)

- `JMHSample_12_Forking` 그대로: 의미가 같은 `Counter1`·`Counter2`를 인터페이스로 호출한다. 앞 셋은 `@Fork(0)`(같은 JVM에서 이어 실행), 뒤 둘은 `@Fork(1)`.

(실험, 같은 환경)

```text
Benchmark                    Mode  Cnt  Score   Error  Units
Forking.measure_1_c1         avgt    5  5.070 ± 0.494  ns/op
Forking.measure_2_c2         avgt    5  7.577 ± 2.130  ns/op
Forking.measure_3_c1_again   avgt    5  9.487 ± 2.033  ns/op
Forking.measure_4_forked_c1  avgt    5  4.502 ± 2.115  ns/op
Forking.measure_5_forked_c2  avgt    5  4.096 ± 0.382  ns/op
```

- 관찰: 같은 `c1`인데 처음(5.1ns)과 `c2`를 돈 뒤 다시(9.5ns)가 거의 2배 다르다. (사실 점검 재실행: 4.65 → 6.78 → 9.21 ± 5.68ns, 포크한 둘 4.54·4.30ns — 같은 경향.) 호출 지점이 두 구현을 다 본 뒤라 JIT가 덜 최적화된 코드를 만든 것이다(샘플 주석의 "profile-guided optimizations ... mix their profiles together"). 포크한 둘(4.5·4.1ns)은 비슷하다.
- JMH도 `@Fork(0)` 실행에 "Non-forked runs ... Use non-forked runs only for debugging purposes" 경고를 출력했다.
- 커리큘럼 ⚠ "포크 1회로 여러 벤치마크를 돌림 → 프로파일이 섞여 실행 순서마다 결과가 다름"이 이 현상이다(정확히는 포크 0 = 같은 JVM 안에서 여러 벤치마크).

### 3. 결과 비교의 통계

```text
 A: 37 ± 17 ns   B: 33 ± 5 ns     차이 4ns의 구간(≈ 4 ± 18)이 0을 포함 → "B가 빠르다"고 말할 근거 부족
 A: 37 ±  2 ns   B: 25 ± 2 ns     구간이 안 겹친다 → 차이가 있다고 볼 수 있다(같은 조건이라면)
```

- Georges, Buytaert, Eeckhout(OOPSLA 2007): JIT·GC·스레드 스케줄 때문에 자바 실행 시간은 실행마다 다르다. 평균만, 최고값만 보고하는 흔한 방법이 잘못된 결론으로 이어질 수 있다. 시작 성능은 여러 번의 JVM 실행 각각의 1회 실행 시간으로, 정상 상태 성능은 여러 JVM 실행에서 정상 상태 반복들의 값으로 신뢰구간을 계산하라고 권한다.
- JMH의 Error는 정규분포를 가정한 99.9% 신뢰구간이다. 포크가 여러 개면 포크 간 변동이 반영된다.
- *신뢰구간(confidence interval)*: 같은 방식으로 표본을 뽑아 구간을 만드는 일을 반복하면 그 구간들 중 신뢰수준(예: 99.9%)만큼이 참값을 포함하는 구간 추정. 신뢰수준은 절차의 장기 포함률이지, 계산된 구간 하나가 참값을 담을 확률이 아니다. 계산과 해석은 [data-analysis/08-confidence-intervals](../../data-analysis/08-confidence-intervals/2-summary.md).
- 차이가 작으면 반복·포크를 늘려 구간을 좁힌 뒤 판단한다. 판단은 두 구간의 겹침이 아니라 차이 자체의 구간(또는 검정)으로 한다. 구간이 조금 겹쳐도 차이는 유의할 수 있다([data-analysis/08](../../data-analysis/08-confidence-intervals/2-summary.md) 실험 E). 차이의 구간이 0을 포함하면 "차이를 확인하지 못했다"가 결론이다.

## 쓰이는 자료구조·알고리즘

- **반복 측정 분포**: 측정값 n개(포크 × 반복)의 평균·표준편차·신뢰구간. JMH 로그는 `(min, avg, max)`와 `stdev`도 출력한다(실험 1 로그). SampleTime 모드는 호출별 시간을 표본으로 잰다.
- **신뢰구간**: t분포 기반 구간(표본이 작을 때). 두 구간의 겹침이 아니라 차이의 구간이 0을 포함하는지로 비교한다(겹침 판정은 보수적이다. 두 구간이 전혀 안 겹치면 차이도 유의하다).
- **JIT 단계 모델**: 호출·루프 카운터가 문턱을 넘으면 다음 단계로 컴파일한다. 워밍업 횟수가 "충분한가"는 반복별 값이 평평해졌는지로 확인한다(위 실험 2의 곡선).
- **Blackhole**: 값을 쓰는 척하는 싱크. 비용이 작고 JIT가 값의 사용을 증명할 수 없게 설계된다.
- **포크(프로세스 격리)**: 상태(JIT 프로파일·힙·클래스 로딩)를 실험마다 초기화한다.

## 적용 — 풀어나가는 법

### 1. 프로젝트 만들기와 실행

```bash
# JMH 아키타입 (JMH README)
mvn archetype:generate -DinteractiveMode=false -DarchetypeGroupId=org.openjdk.jmh \
  -DarchetypeArtifactId=jmh-java-benchmark-archetype -DgroupId=org.sample -DartifactId=bench -Dversion=1.0
cd bench && mvn clean verify
java -jar target/benchmarks.jar MyBench -f 3 -wi 5 -i 5 -prof gc   # 포크 3, 할당량(gc) 프로파일러
```

- 이 노트 실험은 아키타입 대신 `javac -cp 'jmh-core:jmh-generator-annprocess'`로 컴파일하고 `java -cp ... org.openjdk.jmh.Main`으로 실행했다(어노테이션 프로세서가 `META-INF/BenchmarkList`를 만든다).
- `-prof gc`는 연산당 할당 바이트(`gc.alloc.rate.norm`, 단위 B/op)를 보여 준다. 실험 1의 `returned`는 `≈ 10⁻⁴ B/op`(할당 없음)였다. 시간이 같아도 할당이 다르면 운영 GC 부담이 다르다.

### 2. 벤치마크 작성 체크리스트

```java
@State(Scope.Benchmark)
public class JsonBench {
    @Param({"10", "1000"}) int size;          // 입력 크기를 여러 개로
    Order order;                              // final 아님
    @Setup(Level.Trial) public void setup() { order = Orders.random(size, 42); }  // 준비는 측정 밖

    @Benchmark public byte[] jackson() throws Exception { return mapper.writeValueAsBytes(order); } // 반환
    @Benchmark public void two(Blackhole bh) { bh.consume(a(order)); bh.consume(b(order)); }        // 결과 둘
}
```

- 결과를 반환하거나 `Blackhole`에. 입력은 `@State`의 비-final 필드에서. 벤치마크 안에 반복 루프 금지.
- 준비 작업은 `@Setup`으로 측정 밖에. `Level.Invocation`(호출마다 실행)은 JMH 1.37 `Level.java` 주석이 "HERE BE DRAGONS"라고 경고한다: 호출 하나가 1ms를 넘는 벤치마크에만 쓸 만하고, 매 호출 타임스탬프 비용과 (coordinated) omission 위험이 있다(→ 19).
- 빈 `baseline` 벤치마크를 함께 두고, 결과가 baseline과 비슷하면 DCE를 의심한다.

### 3. 결과 읽기

- Score ± Error를 함께 읽는다. 비교는 차이의 구간으로 하고, 그 구간이 0을 포함하면 결론을 내리지 않는다.
- 반복별 값(로그)이 워밍업 뒤 평평한지 본다. 계속 내려가면 워밍업이 부족하다.
- 결과를 보고할 때 JMH·JDK 버전, CPU·코어 수, 포크·반복 수, 다른 부하 여부를 함께 적는다.
- 측정한 연산이 서비스 지연에서 차지하는 비율을 확인한다. 5% 구간의 2배 개선은 전체 2.5%다(→ 20).

## 장애 시나리오와 대처

### 1. 결과가 0.3 ns/op — 계산이 사라졌다

- 현상: "새 알고리즘이 100배 빠르다"는 PR. 벤치마크 결과가 1ns 미만이다.
- 보이는 형태: 결과가 빈 메서드 baseline과 같다(실험 1: deadCode 1.1ns = baseline 1.1ns).
- 원인: 결과를 버려서 DCE, 또는 입력이 상수라 상수 접기.
- 대처: 결과를 반환하거나 `Blackhole`에 넣고, 입력을 `@State` 비-final 필드에서 읽는다. baseline과 비교한다. 의심되면 `-prof perfasm`으로 생성 코드를 본다(JMH 1.37 내장 프로파일러 "Linux perf + PrintAssembly Profiler" — `ProfilerFactory.java`. Linux `perf`와 hsdis 플러그인이 있어야 한다).

### 2. `System.nanoTime` 루프로 직접 잼 → 워밍업·OSR 왜곡

- 현상: 같은 측정을 두 번 했는데 결과가 3배 다르다. 루프 반복 수를 바꾸니 ns/op도 바뀐다.
- 보이는 형태: 실험 2처럼 앞쪽 묶음 300ns, 뒤쪽 25~70ns.
- 원인: 인터프리터·C1·C2 구간이 섞였다. 루프는 OSR 컴파일 버전으로 재진다. 루프 안 계산이 합쳐지거나 지워질 수 있다.
- 대처: JMH를 쓴다. 손으로 재야 한다면 워밍업을 분리하고, 결과를 소비하고, 여러 번 재 분포를 본다.

### 3. 포크 없이 여러 벤치마크 → 실행 순서마다 결과가 다름

- 현상: 벤치마크 A를 먼저 돌리면 B가 빠르고, B를 먼저 돌리면 A가 빠르다.
- 보이는 형태: 실험 3처럼 같은 벤치마크가 다른 벤치마크 뒤에서 2배 느리다. `@Fork(0)` 또는 `-f 0`, IDE 실행.
- 원인: 같은 JVM에서 JIT 프로파일이 섞였다(타입 프로파일이 다형성으로 바뀜).
- 대처: 포크를 켠다(기본 5). 벤치마크 간 비교는 각자 새 JVM에서.

### 4. 한 번 재고 차이를 주장

- 현상: 37ns vs 33ns로 "10% 개선"이라고 머지했는데 다음 측정에서는 반대로 나왔다.
- 보이는 형태: Error가 ±17ns처럼 차이보다 크다. 포크 1, 반복 몇 회.
- 원인: 실행 간 변동이 차이보다 크다(Georges 외 2007이 경고한 상황).
- 대처: 포크·반복을 늘려 구간을 좁힌다. 차이의 구간이 0을 포함하면 "차이를 확인하지 못함"으로 기록한다(차이가 없다는 뜻은 아니다). 두 구간의 겹침만으로 판정하지 않는다. 조용한 전용 머신에서 잰다.

## 핵심 문장

- JVM은 실행 중에 코드를 바꾸고(워밍업·JIT), 쓰이지 않는 계산을 지우고(DCE), 상수를 미리 계산한다. 손으로 잰 숫자는 이 중 무엇을 쟀는지 모른다.
- JMH는 워밍업·반복·포크·결과 소비를 대신해 준다. 결과는 반환하거나 Blackhole에, 입력은 비-final 필드에서, 반복 루프는 쓰지 않는다.
- 빈 메서드와 같은 결과는 계산이 사라졌다는 신호다(실험: 1.1ns = baseline). 결과를 반환하자 37ns가 됐다.
- 포크 없이 여러 벤치마크를 이어 돌리면 JIT 프로파일이 섞여 같은 코드가 2배 느려질 수 있다(실험: 5.1 → 9.5ns).
- 차이는 차이 자체의 신뢰구간(또는 검정)으로 판단한다. 두 구간이 겹쳐도 차이가 유의할 수 있다.

## 관련 주제·근거

- 선행
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) — 측정 일반, 분위수
  - [language/22-ir-and-optimization](../../language/22-ir-and-optimization/2-summary.md) — IR·인라이닝·DCE
  - [data-analysis/08-confidence-intervals](../../data-analysis/08-confidence-intervals/2-summary.md)
- 후속·연결
  - [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md) — 마이크로 개선이 전체에 주는 몫
  - [36-profiling](../36-profiling/2-summary.md) — 서비스 안에서 핫 코드 찾기
  - [42-cold-start-and-scale-from-zero](../42-cold-start-and-scale-from-zero/2-summary.md) — JIT 워밍업이 운영 지연으로 나타날 때
  - 원본 [engineering-axes/performance.md](../../engineering/engineering-axes/performance.md) 「성능 작업의 함정」의 "마이크로 벤치마크 맹신"
- 문서·소스
  - OpenJDK JMH 1.37 `jmh-core/src/main/java/org/openjdk/jmh/runner/Defaults.java`(포크 5·워밍업 5×10초·측정 5×10초·Throughput) <https://github.com/openjdk/jmh>
  - jmh-samples `JMHSample_08_DeadCode`, `_09_Blackholes`, `_10_ConstantFold`, `_11_Loops`, `_12_Forking`, `_13_RunToRun` <https://github.com/openjdk/jmh/tree/master/jmh-samples/src/main/java/org/openjdk/jmh/samples>
  - Georges, Buytaert, Eeckhout, "Statistically Rigorous Java Performance Evaluation", OOPSLA 2007, pp. 57–76 <https://dl.acm.org/doi/10.1145/1297027.1297033>
- 실험 목록
  - `jmh/bench/Pitfalls.java` — baseline·deadCode·returned·constantFold·twoWrong·twoBlackhole. JMH 1.37, `-f 1 -wi 3 -i 5`(1초)
  - `jmh/bench/Forking.java` — JMHSample_12 이식, Fork(0) 3개 + Fork(1) 2개
  - `Naive.java` — nanoTime 루프 워밍업 곡선, 결과 버림 vs 사용. 2회 실행
  - 환경: Docker eclipse-temurin:21-jdk(Temurin 21.0.12) `--cpus=2`, 공유 호스트(부하 평균 10 이상)
