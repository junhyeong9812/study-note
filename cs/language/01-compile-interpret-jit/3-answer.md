# language/01-compile-interpret-jit — 정답

## 정답

### 1. 세 실행 모델 비교

| | AOT | 인터프리트 | 바이트코드 + JIT |
|---|---|---|---|
| 번역 시점 | 실행 전 전체 | 번역 안 함(명령마다 해석) | 실행 중, 자주 도는 코드만 |
| 시작 | 빠름 | 빠름 | 해석부터 → 워밍업 필요 |
| 최고 속도 | 높음(빌드 때 정보로 최적화) | 낮음(명령마다 디스패치 비용) | 높음(실행 프로파일로 최적화) |
| 동적 기능 | Native Image는 빌드 때 보이는 것만(닫힌 세계). C는 `dlopen`으로 실행 중 로드 가능 | 자유 | 자유 |

- 예: C(gcc) = AOT, CPython 3.12 = 바이트코드 + 인터프리트, Java 21 HotSpot·V8 = 바이트코드(또는 소스) + 인터프리트 + JIT.

### 2. "Python은 컴파일 단계가 없다"

- 맞는 부분: 별도 빌드 단계가 없다. 소스와 입력 데이터가 같은 실행 안에서 처리된다.
- 틀린 부분: CPython도 모듈을 실행하기 전에 소스 → AST → 바이트코드로 **컴파일한다**. `.pyc`가 그 캐시다. 다만 처음 import할 때, 즉 실행 중에 한다. 이미 import했거나(`sys.modules`) 소스와 맞는 `.pyc`가 있으면 다시 컴파일하지 않는다.
- Java는 반대로 `javac`가 빌드 때 바이트코드를 만들고, 실행 중에 HotSpot이 한 번 더(바이트코드 → 기계어) 컴파일한다.
- 결론: 컴파일/인터프리트는 언어가 아니라 **구현**의 성질이다. 원고 §3의 "컴파일 타임이 따로 없다"는 "별도 빌드 단계가 없다"로 읽어야 한다.

### 3. 바이트코드와 스택

```text
  22 iload_1   [s]
  23 iload 5   [s, x]
  25 iload 5   [s, x, x]
  27 imul      [s, x*x]
  28 iload 5   [s, x*x, x]
  30 iconst_3  [s, x*x, x, 3]
  31 iushr     [s, x*x, x>>>3]
  32 ixor      [s, (x*x)^(x>>>3)]
  33 iadd      [s + ...]
  34 istore_1  []            ← s에 저장
  35 iinc 4,1                ← 인덱스++
  38 goto 10                 ← 백엣지
```

- 연산자는 스택 위 두 값을 꺼내 결과 하나를 올린다. 레지스터 이름이 없어 어느 CPU에서든 같은 명령이다(JVMS 6장).
- 백엣지는 `38: goto 10`이다. 반복문 끝에서 처음으로 뒤로 뛴다.

### 4. 세 모드 예측과 실측

- 실측(Temurin 21.0.12, `--cpus=2`, 모드별 6회 범위):
  - `-Xint`: 첫 묶음부터 끝까지 약 6.3~11.1ms. 빨라지지 않는다.
  - `TieredStopAtLevel=1`: 첫 묶음 3.8~5.6ms 뒤 0.35~0.77ms로 떨어져 유지.
  - 기본: 첫 묶음 4.3~7.3ms → 묶음 1~9는 1.1~3.4ms → C2 코드가 들어온 뒤 0.052~0.16ms.
- 기본 모드 초반이 C1만 쓴 모드보다 느린 이유(해석): 초반은 **level 3**(C1 + 전체 프로파일) 코드로 돌았을 것이다. 반복마다 프로파일 카운터를 갱신한다. 시간 측정과 컴파일 로그는 다른 실행이라 묶음별 단계를 직접 대조하지는 않았다. `TieredStopAtLevel=1`은 프로파일 없는 level 1이다.
  - HotSpot 소스 주석은 "level 2가 level 3보다 보통 약 30% 빠르다"고 적는다. 이 루프에서 차이가 더 큰 것은 해석이다.

### 5. `PrintCompilation` 읽기

- `69  7 %  4  Hot::work @ 10 (43 bytes)`
  - 69 = JVM 시작 후 ms, 7 = 컴파일 ID, `%` = OSR(반복문 실행 중 갈아타기), 4 = level 4(C2), `@ 10` = 진입 바이트코드 위치(반복문 머리), 43 bytes = 바이트코드 크기.
- `213  6  3  Hot::work (43 bytes)   made not entrant`
  - ID 6의 level 3 코드에 새 호출이 못 들어오게 막았다는 뜻이다.
  - 반드시 역최적화는 아니다. 이 실험에서는 202ms에 level 4 판(ID 160)이 완성돼 level 3 판이 **대체**된 것이다. 프로파일 가정이 깨진 역최적화도 같은 문구를 내므로, 바로 앞뒤에 더 높은 단계의 같은 메서드가 생겼는지로 구분한다(23).

### 6. 무엇을 세나

- 메서드 **호출 횟수**와 **백엣지 횟수**를 센다(compilationPolicy.hpp).
- 호출 횟수만 세면 "한 번 불려서 안에서 수백만 번 도는" 메서드(예: `main` 안의 큰 반복문)를 놓친다. 백엣지를 세서 잡고, 반복문 도중에 OSR로 갈아탄다.
- 문턱 예(JDK 21 기본): `Tier3InvocationThreshold` 200, `Tier3BackEdgeThreshold` 60000, `Tier4InvocationThreshold` 5000. 컴파일 큐가 길면 배율 s가 커져 문턱이 올라간다.

### 7. 배포 직후 p99 급등

- 가설: 새 JVM의 요청 처리 코드가 아직 해석·level 3에서 돈다. C2 컴파일 스레드가 요청과 CPU를 나눠 쓴다.
- 확인:
  - 새 파드만 느린지, 시간이 지나면 나아지는지 본다.
  - `-XX:+PrintCompilation`(또는 `-Xlog:jit+compilation=debug`)에서 핫 메서드가 level 4가 된 시각과 지연이 떨어진 시각을 맞춘다.
  - 프로파일·스레드 덤프에 `C2 CompilerThread`가 CPU를 쓰는지 본다.
- 대처: 대표 요청으로 예열 후 readiness 열기, 점진적 트래픽 투입, CDS·AppCDS로 시작 비용 줄이기(AOT 캐시는 JDK 24+, JEP 483)([reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)).

### 8. 네이티브 이미지의 리플렉션 실패

- 원인: Native Image는 빌드 때 호출 그래프로 도달 가능한 것만 이미지에 넣는다(닫힌 세계 가정). `Class.forName(설정값)`처럼 문자열로 고르는 대상은 그래프에 간선이 없다. 등록 안 된 리플렉션 호출은 `MissingReflectionRegistrationError`(`java.lang.Error` 하위)를 던진다(GraalVM Reachability Metadata 문서).
- 대처
  1. `META-INF/native-image/<groupId>/<artifactId>/reachability-metadata.json`에 대상을 등록한다(추적 에이전트로 수집 가능).
  2. 프레임워크 AOT 힌트(Spring `RuntimeHints`)를 쓰거나, 리플렉션을 명시 코드로 바꾼다.

### 9. 처리량이 수십 배 낮은 환경

- 의심: `-Xint`(해석만), `-XX:TieredStopAtLevel=1`(C2 없음), 너무 작은 `ReservedCodeCacheSize`(가득 차면 컴파일이 꺼진다). 흔히 `JAVA_TOOL_OPTIONS`나 베이스 이미지에 숨어 있다.
- 확인
  - `jcmd <pid> VM.flags` — 실제 적용된 플래그.
  - 시작 로그의 `Picked up JAVA_TOOL_OPTIONS: ...`.
  - `java -Xint -version`처럼 옵션을 준 버전 줄에는 `interpreted mode`가 찍힌다(Temurin 21.0.12 확인).
  - `jcmd <pid> Compiler.codecache`로 코드 캐시가 가득 찼는지.
- 근거 수치: 이 영역 실험에서 `-Xint`는 데워진 기본 모드보다 약 40~210배 느렸다(코드·호스트·6회 범위 한정).
