# language/01-compile-interpret-jit — 컴파일·인터프리트·바이트코드·JIT — 정리 (힌트)

## 해결하는 문제

CPU는 기계어만 실행한다([architecture/09](../../architecture/09-isa-and-machine-code/2-summary.md)).\
사람이 쓴 소스는 글자의 나열이다. 누군가 이것을 기계어로 바꿔야 한다.

```text
  "x = 3 + 5 * 2"  ──(누군가 번역)──▶  mov / imul / add ...  ──▶  CPU
```

바꾸는 시점이 두 가지다.

- **미리 전부 바꾼다** = 컴파일(AOT).
  - *AOT(Ahead-Of-Time) 컴파일*: 실행 전에 프로그램 전체를 기계어로 번역해 두는 것. C의 `gcc`가 대표.
- **실행하면서 한 조각씩 해석한다** = 인터프리트.
  - *인터프리터(interpreter)*: 프로그램을 기계어로 바꿔 두지 않고, 명령을 하나씩 읽어 그 뜻대로 동작하는 프로그램.
- 둘을 섞은 것이 **바이트코드 + JIT**다.
  - *JIT(Just-In-Time) 컴파일*: 실행 중에 자주 도는 코드만 골라 그 자리에서 기계어로 번역하는 것.

쉬운 예: 외국어 책 읽기.
- 번역서를 먼저 만든다(AOT). 출간까지 오래 걸리지만 읽기는 빠르다.
- 통역사가 옆에서 한 문장씩 통역한다(인터프리트). 바로 시작하지만 매번 느리다.
- 통역사가 자주 나오는 문단을 적어 두고 다음부터 적어 둔 번역을 읽는다(JIT). 처음은 느리고, 갈수록 빨라진다.

똑같은 구조다.\
Java·JS(V8)는 세 번째 방식이다. 그래서 **같은 코드가 시작 직후에는 느리고, 데워진 뒤에는 빠르다.**

실무 예:
- 배포 직후 새 파드만 p99가 튄다. 평균은 멀쩡하다(JIT 워밍업 — [reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)).
- JVM에서 잘 돌던 Spring 앱을 GraalVM 네이티브 이미지로 빌드했더니, 리플렉션으로 클래스를 찾는 곳에서 실행 중 오류가 난다.
- 같은 반복문이 CPython에서는 데워진 JVM보다 훨씬 느리다. CPython 3.12는 JIT 없이 바이트코드를 해석해 실행한다.

## 동작·원리

### 1. 컴파일러 파이프라인 — 소스에서 기계어까지

```text
  소스 문자열
     │ ① 어휘 분석(렉서)          → 02
     ▼
  토큰열  [x] [=] [3] [+] [5] [*] [2]
     │ ② 구문 분석(파서)          → 03
     ▼
  AST        =
            / \
           x   +
              / \
             3   *
                / \
               5   2
     │ ③ 의미 분석(심벌 테이블·타입) → 04
     ▼
  IR(중간 표현)  t1 = 5*2 ; t2 = 3+t1 ; x = t2
     │ ④ 최적화(상수 접기 등)      → 22
     ▼
  IR'           x = 13
     │ ⑤ 코드 생성(명령 선택·레지스터 할당)
     ▼
  기계어 또는 바이트코드
```

- ①~③을 *프런트엔드*, ④를 *미들엔드*, ⑤를 *백엔드*라 부른다.
  - *프런트엔드*: 언어마다 다른 부분. 문법과 의미 규칙을 안다.
  - *백엔드*: CPU마다 다른 부분. 명령어 집합을 안다.
  - 가운데 IR을 두면 "언어 N개 × CPU M개"를 N+M개 부품으로 만들 수 있다. LLVM이 이 구조다(22).
- 기초 설명(한국어 문장 비유, 토큰·BNF·파스 트리)은 원고 [compiler-pipeline](../../foundations/compiler-pipeline/README.md) §1·§6에 있다.

### 2. 세 가지 실행 모델

```text
  (a) AOT — C (gcc 13)
      main.c ─gcc─▶ main.o ─링커─▶ a.out(기계어) ───────────────▶ CPU가 직접 실행
                     [빌드 시점]                        [실행 시점]

  (b) 바이트코드 + 인터프리터 — CPython 3.12
      app.py ─컴파일─▶ 코드 객체(바이트코드, .pyc로 캐시) ─▶ 평가 루프가 한 명령씩 해석
                     [import 시점, 실행 중]

  (c) 바이트코드 + 인터프리터 + JIT — Java 21 HotSpot
      App.java ─javac─▶ App.class(바이트코드) ─▶ 인터프리터 ─(자주 돌면)─▶ C1 ─▶ C2 기계어
                [빌드 시점]                       [실행 시점: 해석하며 세고, 세다가 번역]
```

- "컴파일 언어 vs 인터프리터 언어"는 **언어가 아니라 구현**의 성질이다.
  - CPython도 실행 전에 소스를 바이트코드로 컴파일한다. 원고 §12의 "1. 컴파일 단계"가 그것이다.
  - 같은 Java도 HotSpot(JIT)으로 돌릴 수 있고, GraalVM Native Image(AOT)로 미리 기계어로 만들 수도 있다(24).
- 참고: 원고 §3의 "인터프리터 언어는 컴파일 타임이 따로 없다"는 정확하지 않다. CPython은 모듈을 처음 import할 때 컴파일을 먼저 끝내고 실행한다. 이미 import한 모듈은 `sys.modules`에서 꺼내고, 소스와 맞는 `.pyc`가 있으면 컴파일 없이 그 바이트코드를 읽는다(Python 3.12 import 시스템 문서). 다만 그 컴파일이 **실행 중에** 일어나고, 별도 빌드 단계가 없을 뿐이다.
- 링커가 목적 파일을 묶는 과정은 원고 §4와 [os/29](../../os/29-linking-and-loading/2-summary.md)에 있다.

### 3. 바이트코드 — 가상 CPU의 명령어

바이트코드는 실제 CPU가 아니라 **가상 머신**을 위한 명령어다. JVM과 CPython 모두 *스택 머신*이다.

- *스택 머신*: 피연산자를 레지스터가 아니라 스택에 올려 두고 계산하는 기계. `3 + 5`는 "3을 올림, 5를 올림, 둘을 꺼내 더해 올림"이 된다([data-structure/03-stack](../../data-structure/03-stack/2-summary.md)).

```java
static int work(int[] a) {
    int s = 0;
    for (int x : a) s += (x * x) ^ (x >>> 3);
    return s;
}
```

`javap -c`(JDK 21.0.12)로 본 반복문 몸통:

```text
  22: iload_1          // s를 스택에 올림
  23: iload 5          // x
  25: iload 5          // x
  27: imul             // x*x
  28: iload 5
  30: iconst_3
  31: iushr            // x>>>3
  32: ixor             // (x*x) ^ (x>>>3)
  33: iadd             // s + ...
  34: istore_1         // s에 저장
  35: iinc 4, 1        // 인덱스 ++
  38: goto 10          // 반복문 처음으로 (← 백엣지)
```

- 이 명령어 집합은 JVMS 6장이 정한다. 어느 CPU에서든 같은 `.class`가 돈다([architecture/09](../../architecture/09-isa-and-machine-code/2-summary.md) "바이트코드는 이식되고 JNI .so는 아키텍처를 탄다").
- Python 3.12의 `dis`로 본 `def add(a, b): return a + b`:

```text
  0 RESUME          0
  2 LOAD_FAST       0 (a)
  4 LOAD_FAST       1 (b)
  6 BINARY_OP       0 (+)
 10 RETURN_VALUE
```

- 참고: 원고 §5의 `BINARY_ADD`는 3.10까지의 이름이다. 3.11부터 이항 연산자가 `BINARY_OP` 하나로 합쳐졌다(Python 3.12 `dis` 문서 "Added in version 3.11"). 문서는 "바이트코드는 CPython 구현 세부이며 버전 사이에 바뀔 수 있다"고 적는다. 바이트코드 출력을 외우지 말고 **자기 버전에서 `dis`로 본다.**
- 평가 루프(원고 §11의 `for (;;) switch (opcode)` — 개념 모형)는 바이트코드 한 개마다 "꺼내기 → 분기 → 실행"을 반복한다. 명령 하나당 이 비용이 붙어서 인터프리터가 느리다.
  - 실제 CPython 3.12는 컴파일러가 지원하면(gcc 등) `switch` 대신 *computed goto*(명령마다 다음 명령 처리 코드로 바로 점프)로 분기한다(`Python/ceval_macros.h`의 `USE_COMPUTED_GOTOS`). 3.11부터는 자주 보는 타입에 맞춘 특수화 명령으로 바꿔 끼우기도 한다(PEP 659).

### 4. JIT — 세다가, 넘으면 번역한다

HotSpot은 메서드마다 **호출 횟수**와 **백엣지 횟수**를 센다.

- *백엣지(back-edge)*: 반복문 끝에서 처음으로 되돌아가는 점프. 위 바이트코드의 `38: goto 10`이다. 이걸 세면 "한 번 불렸지만 안에서 오래 도는" 메서드를 잡는다.

```text
  JDK 21 HotSpot 계층 컴파일 (compilationPolicy.hpp 주석)
   level 0  인터프리터            ── 세면서 프로파일도 모은다
   level 1  C1, 프로파일 없음      ── 단순(trivial) 메서드
   level 2  C1 + 호출·백엣지 카운터 ── C2 큐가 밀릴 때 잠시
   level 3  C1 + 전체 프로파일     ── 보통 0 → 3 → 4
   level 4  C2, 프로파일 기반 최적화 ── 최고 속도

  넘는 기준(예): Tier3InvocationThreshold = 200, Tier4InvocationThreshold = 5000,
               Tier3BackEdgeThreshold = 60000 (compiler_globals.hpp 기본값, 컴파일 큐 길이에 따라 배율 s가 붙는다)
```

- *C1·C2*: HotSpot의 두 JIT 컴파일러. C1은 빨리 번역하고 최적화를 덜 한다. C2는 오래 걸리지만 인라이닝·탈출 분석 등으로 빠른 코드를 만든다.
- *프로파일*: 실제로 어느 분기를 탔는지, 어떤 타입이 들어왔는지 모은 기록. C2는 이걸 믿고 "이 분기는 안 탄다"고 가정한 코드를 만든다. 가정이 깨지면 *역최적화*로 인터프리터로 돌아간다(23).
- *OSR(On-Stack Replacement)*: 실행 중인 반복문을 멈추지 않고, 그 자리에서 컴파일된 코드로 갈아타는 것. `PrintCompilation`에서 `%` 표시와 `@ bci`로 보인다.
- 계층 전이·인라이닝·역최적화·코드 캐시의 자세한 얘기는 [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md)이 맡는다.

### 실험: 같은 메서드를 세 모드로 — 해석 / C1만 / 계층(기본)

- 환경: `eclipse-temurin:21-jdk`(Temurin 21.0.12+8), `docker --cpus=2 --network none`, 호스트 i7-13700HX. 위 `work(int[1000])`를 200번 부르는 묶음을 40번 잰다. 각 모드 6회 실행(집필 3회 + 점검 재실행 3회, 호스트 부하가 다른 시점).

```bash
javac -d out Hot.java
java -Xint                     -cp out Hot   # 해석만
java -XX:TieredStopAtLevel=1   -cp out Hot   # C1(level 1)까지만
java                           -cp out Hot   # 기본(0→3→4)
java -XX:+PrintCompilation     -cp out Hot > pc.txt 2> rounds.txt
```

묶음 하나(work 200회)의 시간, 6회 실행 범위:

| 모드 | 묶음 0 | 묶음 1~9 | 묶음 19~39 |
|---|---|---|---|
| `-Xint` | 6.7~10.4 ms | 6.3~11.0 ms | 6.8~11.1 ms (내내 같은 수준) |
| `-XX:TieredStopAtLevel=1` | 3.8~5.6 ms | 0.35~0.77 ms | 0.35~0.77 ms |
| 기본(계층) | 4.3~7.3 ms | 1.1~3.4 ms (6회 중 2회는 9번째부터 0.06~0.15 ms) | 0.052~0.16 ms |

`-XX:+PrintCompilation`(기본 모드, 4회 실행 중 1회 — 나머지 3회도 같은 순서, 시각만 다름):

```text
  시각(ms) ID  표시 단계  메서드
   67      5   %    3    Hot::work @ 10 (43 bytes)    ← level 3, 반복문 안에서 OSR
   68      6        3    Hot::work (43 bytes)         ← level 3, 일반 진입
   69      7   %    4    Hot::work @ 10 (43 bytes)    ← level 4(C2) OSR
   84      5   %    3    Hot::work @ 10   made not entrant
  202    160        4    Hot::work (43 bytes)         ← level 4(C2) 일반 진입
  213      6        3    Hot::work (43 bytes)   made not entrant   ← level 3 판은 퇴역
```

- 관찰 1 — 해석만 하면 처음부터 끝까지 묶음당 약 6~11ms다. 데워지지 않는다.
- 관찰 2 — 기본 모드의 마지막 구간(0.052~0.16ms)은 `-Xint`보다 **약 40~210배** 빠르다(이 코드·이 호스트·6회 범위 한정).
- 관찰 3 — 기본 모드의 묶음 1~9(1.1~3.4ms)는 C1만 쓴 판(0.35~0.77ms)보다 느리다. 이 구간이 프로파일을 모으는 level 3 코드였기 때문으로 **해석**한다(시간 측정과 `PrintCompilation`은 다른 실행이라, 묶음별 단계를 같은 실행에서 대조하지는 않았다). 소스 주석도 "level 2가 level 3보다 보통 약 30% 빠르다"고 적는다. 이 루프에서 차이가 더 큰 것은 반복마다 카운터를 갱신하기 때문으로 **해석**한다.
- 관찰 4 — `made not entrant`는 "새 호출은 이 코드로 들어오지 말라"는 표시다. 여기서는 level 3 코드가 level 4로 **대체**되며 붙었다. 가정이 깨져서 생기는 역최적화와 출력 모양이 같으니, 원인은 앞뒤 줄로 구분한다(23).
- 관찰 5 — C1만 쓴 모드와 기본 모드에서는 첫 묶음이 가장 느리다. 클래스 로딩·첫 실행 비용이 섞여 있다. `-Xint`는 첫 묶음(6.7~10.4ms)도 뒤 구간(6.3~11.1ms)과 같은 수준이었다.

### 5. AOT와 JIT의 맞바꿈

| | AOT (C, Native Image) | JIT (HotSpot, V8) |
|---|---|---|
| 시작 | 빠름 | 해석부터 시작 → 워밍업 필요 |
| 최고 속도 | 빌드 때 아는 정보만으로 최적화 | 실행 프로파일로 "실제로 도는 경로"에 맞춤 |
| 번역 비용 | 빌드 때 1회 | 실행 중 CPU를 쓴다(컴파일 스레드) |
| 동적 기능 | Native Image: 빌드 때 보이는 것만 포함(닫힌 세계). C: `dlopen`으로 실행 중 공유 라이브러리 로드 가능 | 실행 중 클래스 로딩·리플렉션 자유 |
| 이식성 | 아키텍처별 바이너리 | 바이트코드 하나 + 아키텍처별 VM |

- *닫힌 세계 가정(closed-world assumption)*: "실행 중에 쓰일 클래스는 빌드할 때 전부 알 수 있다"는 가정. GraalVM 문서는 Native Image에서 실행 중 새 클래스를 정의할 수 없는 이유를 이것으로 설명한다.
- 그래서 `Class.forName(설정 파일에서 읽은 문자열)`처럼 빌드 때 상수가 아닌 리플렉션은 **메타데이터로 미리 알려 줘야** 한다. 안 알려 주면 `MissingReflectionRegistrationError`가 난다(GraalVM Reachability Metadata 문서). 상세는 [24-aot-native-image-and-startup](../24-aot-native-image-and-startup/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **핫스팟 카운터** — 메서드마다 호출 수·백엣지 수를 세는 정수 카운터. 문턱(위 기본값 × 배율 s)을 넘으면 컴파일 요청을 큐에 넣는다. 프로파일은 메서드별 *MDO(MethodData)* 객체에 쌓인다(compilationPolicy.hpp).
- **피연산자 스택** — JVM·CPython 바이트코드의 계산 공간. [data-structure/03-stack](../../data-structure/03-stack/2-summary.md).
- **디스패치 루프** — `for(;;) switch(opcode)`(개념 모형, CPython 3.12 gcc 빌드는 computed goto). 원고 §11. 분기 예측이 성능을 가른다([architecture/18](../../architecture/18-pipelining-and-branch-prediction/2-summary.md)).
- **컴파일 큐와 코드 캐시** — 컴파일 요청 대기열, 완성된 기계어를 두는 메모리 영역. `jcmd <pid> Compiler.queue`·`Compiler.codecache`로 본다.
- **호출 그래프 도달성** — AOT 빌더가 "어디까지 쓰이나"를 정하는 그래프 탐색([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)·[data-structure/08-graph](../../data-structure/08-graph/2-summary.md)). 리플렉션은 이 그래프에 간선이 안 보인다.

## 적용 — 풀어나가는 법

1. **증상이 "시간이 지나면 나아지는가"를 먼저 본다.**
   - 새 인스턴스만 느리고 몇 분 뒤 정상 → 워밍업(JIT·캐시·커넥션)이다. 코드 버그보다 배포 절차 문제다.
   - 계속 느리다 → JIT이 꺼졌거나, 해석 모드거나, 애초에 알고리즘 문제다.
2. **JVM이 실제로 어떤 모드인지 확인한다.**

   ```bash
   java -XX:+PrintFlagsFinal -version | grep -E ' TieredCompilation | TieredStopAtLevel | ReservedCodeCacheSize | CICompilerCount '
   # 이 컨테이너(--cpus=2): TieredCompilation=true, CICompilerCount=2(ergonomic), ReservedCodeCacheSize=251658240
   jcmd <pid> VM.flags               # 실행 중인 JVM의 실제 플래그 (JAVA_TOOL_OPTIONS로 -Xint가 끼었는지)
   jcmd <pid> Compiler.codecache     # 코드 캐시 사용량
   ```

   - `jcmd <pid> Compiler.codecache` 출력 예(JDK 21.0.12, 막 시작한 JVM): `CodeCache: size=245760Kb, used=3412Kb, max_used=3427Kb, free=242345Kb`.
3. **워밍업이 언제 끝나는지 로그로 본다.** `-XX:+PrintCompilation`(또는 `-Xlog:jit+compilation=debug`)에서 핫 메서드가 level 4에 도달하는 시각과 지연이 떨어지는 시각을 맞춰 본다(위 실험의 방식).
4. **바이트코드로 "실제로 무엇이 실행되나"를 본다.**
   - Java: `javap -c -p 클래스` — 오토박싱, 문자열 연결, 람다가 어떤 명령으로 바뀌었는지 보인다.
   - Python: `python -m dis 파일.py` 또는 `dis.dis(함수)`.
5. **AOT로 바꿀 때는 동적 기능 목록부터 만든다.** 리플렉션·동적 프록시·리소스 로딩·직렬화를 찾아 메타데이터를 등록한다. Spring Boot는 빌드 때 AOT 처리로 힌트를 만든다([software-design/35](../../software-design/35-annotation-and-metadata-programming/2-summary.md)).

## 장애 시나리오와 대처

### 1. 배포·스케일아웃 직후 p99 급등 (⚠)

- **현상**: 새 파드가 트래픽을 받기 시작한 1~몇 분 동안 p99가 튄다. 평균과 기존 파드는 멀쩡하다.
- **보이는 형태**: 새 파드만 CPU가 높다. 스레드 덤프·프로파일에 `C2 CompilerThread`가 보인다. `PrintCompilation` 로그에 컴파일이 몰려 있다.
- **원인**: 요청 처리 코드가 아직 해석 또는 level 3에서 돈다. 위 실험에서 같은 코드가 데워지기 전 수십 배 느렸다. 컴파일 스레드도 요청과 CPU를 나눠 쓴다(`--cpus` 작으면 더 심하다).
- **대처**: 대표 요청으로 예열한 뒤 readiness를 연다. 트래픽을 천천히 늘린다. JDK 21에서는 CDS·AppCDS로 시작 비용을 줄인다(AOT 캐시는 JDK 24+, JEP 483). 세부와 실측은 [reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)와 [language 23](../23-jit-tiered-compilation-and-warmup/2-summary.md).

### 2. 네이티브 이미지에서만 리플렉션 실패 (⚠)

- **현상**: JVM에서 통과한 테스트가 네이티브 바이너리에서 특정 기능만 실패한다.
- **보이는 형태**: `MissingReflectionRegistrationError`(GraalVM 문서: `java.lang.Error` 하위, 잡아서 처리하지 말 것), 또는 빌드 때 상수로 접힌 `Class.forName`의 `ClassNotFoundException`.
- **원인**: AOT 빌더는 빌드 때 보이는 호출 그래프만 이미지에 넣는다. 문자열로 고르는 클래스는 그래프에 안 보인다.
- **대처**: `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`에 등록하거나, 추적 에이전트로 수집하거나, 프레임워크 AOT 힌트(Spring `RuntimeHints`)를 쓴다. 가능하면 리플렉션을 명시 코드로 바꾼다.

### 3. 운영에 `-Xint`·`TieredStopAtLevel=1`이 남아 처리량이 바닥

- **현상**: 특정 환경에서만 CPU가 높고 처리량이 수십 배 낮다.
- **보이는 형태**: `jcmd <pid> VM.flags`나 시작 로그(`Picked up JAVA_TOOL_OPTIONS: ...`)에 해당 옵션. `java -Xint -version`이면 버전 줄에 `interpreted mode`가 찍힌다(기본은 `mixed mode` — Temurin 21.0.12에서 확인).
- **원인**: 디버깅·시작 시간 단축용 옵션이 이미지나 환경 변수에 남았다. 위 실험에서 `-Xint`는 데워진 기본 모드보다 약 40~210배 느렸다. `TieredStopAtLevel=1`은 C2가 없어 데워진 기본 모드보다 약 2~15배 느렸다(6회 범위).
- **대처**: 기본 이미지·차트의 JVM 옵션을 점검 목록에 넣는다. 시작 시간이 목적이면 C1 제한보다 CDS·AppCDS(JDK 24+면 AOT 캐시, JEP 483)를 먼저 검토한다(24).

### 4. 오래 돈 서버가 갑자기 느려짐 — 코드 캐시 가득

- **현상**: 며칠 돈 뒤 새로 핫해진 코드가 느린 채로 남는다.
- **보이는 형태**: 로그에 `CodeHeap 'non-profiled nmethods' is full. Compiler has been disabled.` 꼴의 경고(문구 틀은 HotSpot 21 `codeCache.cpp`의 `"%s is full. Compiler has been disabled."`). `jcmd <pid> Compiler.codecache`의 `free`가 0 근처.
- **원인**: 동적으로 생성되는 클래스·람다·프록시가 많아 컴파일된 코드가 코드 캐시(`ReservedCodeCacheSize`, 이 환경 240MB)를 채웠다.
- **대처**: 원인(클래스 생성 폭주)을 먼저 찾는다. 필요하면 `ReservedCodeCacheSize`를 키운다. 코드 캐시 정리 동작은 23에서 다룬다.

## 핵심 문장

- "컴파일 언어 vs 인터프리터 언어"는 구현의 성질이다. CPython도 바이트코드로 컴파일하고, Java도 AOT로 만들 수 있다.
- 바이트코드는 가상 스택 머신의 명령어다. 인터프리터는 명령 하나마다 꺼내고 분기하는 비용을 낸다.
- JIT는 호출·백엣지 카운터로 핫 코드를 골라 실행 중에 기계어로 바꾼다. HotSpot은 보통 해석 → C1(프로파일) → C2 순서다.
- 그래서 JIT 런타임은 시작 직후 느리다. 이 실험에서 해석은 데워진 C2 코드보다 약 40~210배 느렸다.
- Native Image 같은 AOT는 빠른 시작을 얻는 대신 닫힌 세계를 가정한다. 리플렉션처럼 빌드 때 안 보이는 것은 미리 알려 줘야 한다.

## 관련 주제·근거

- 선행
  - [architecture/09-isa-and-machine-code](../../architecture/09-isa-and-machine-code/2-summary.md) — 기계어·ISA, 바이트코드 이식성
- 후속(이 영역)
  - [02-lexing-and-regular-languages](../02-lexing-and-regular-languages/2-summary.md) · [03-parsing-grammars-ast](../03-parsing-grammars-ast/2-summary.md) · [04-semantic-analysis-and-scopes](../04-semantic-analysis-and-scopes/2-summary.md) · [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md) — 파이프라인 각 단계
  - [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md) · [24-aot-native-image-and-startup](../24-aot-native-image-and-startup/2-summary.md) · [25-lto-pgo-and-binary-size](../25-lto-pgo-and-binary-size/2-summary.md)
- 연결
  - [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) — 서버 단위 워밍업·AppCDS·AOT 캐시 실측
  - [reliability/38-microbenchmarking](../../reliability/38-microbenchmarking/2-summary.md) — JIT 때문에 마이크로벤치마크가 속는 이유
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) · [software-design/35](../../software-design/35-annotation-and-metadata-programming/2-summary.md)(리플렉션·AOT 힌트)
  - 원고 [foundations/compiler-pipeline](../../foundations/compiler-pipeline/README.md) §3(컴파일·인터프리트) · §4(링커) · §5·§11(PVM·dis) · §12(FastAPI 실행 흐름)
- 문서·소스
  - JVMS SE21 6장(명령어 집합) <https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-6.html>
  - `java` 도구 문서(JDK 21) — `-Xint`("interpreted-only mode"), `-Xss`, `-XX:CompileCommand` <https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html>
  - OpenJDK jdk21u `src/hotspot/share/compiler/compilationPolicy.hpp`(level 0~4 정의, 전이 조건, "level 2 is generally faster than level 3 by about 30%") · `compiler_globals.hpp`(`Tier3InvocationThreshold` 200, `Tier3CompileThreshold` 2000, `Tier3BackEdgeThreshold` 60000, `Tier4InvocationThreshold` 5000, `Tier4BackEdgeThreshold` 40000, `TieredStopAtLevel` 4) · `compileTask.cpp`(`%` = OSR) · `codeCache.cpp`(코드 캐시 가득 경고)
  - Python 3.12 `dis` 문서 — `BINARY_OP` "Added in version 3.11", 바이트코드는 구현 세부 <https://docs.python.org/3.12/library/dis.html>
  - GraalVM Native Image Reachability Metadata — 닫힌 세계 가정, `MissingReflectionRegistrationError`, `reachability-metadata.json` <https://www.graalvm.org/latest/reference-manual/native-image/metadata/>
  - Aho 외 『Compilers』(Dragon Book) 1장 `[?]`
- 실험 목록
  - JIT 세 모드 비교 + `PrintCompilation` — `Hot.java`, Temurin 21.0.12, `--cpus=2 --network none`, 모드별 6회(집필 3 + 점검 3) + PrintCompilation 4회
  - `javap -c`로 본 `work` 바이트코드(JDK 21.0.12) · Python 3.12.3 `dis`(호스트)로 본 `add`
  - `-XX:+PrintFlagsFinal`(TieredCompilation·CICompilerCount·ReservedCodeCacheSize)과 `jcmd Compiler.codecache`(Temurin 21.0.12 컨테이너)
