# reliability/36-profiling — CPU·off-CPU·락·할당 프로파일링과 플레임 그래프 — 정리 (힌트)

## 해결하는 문제

"느리다"는 말만으로는 어디를 고칠지 모른다. 추측으로 고치면 **병목이 아닌 곳**을 빠르게 만든다.

```text
 추측 최적화                                   프로파일링
 "JSON 파싱이 느릴 거야" → 파서 교체 2주         실제 시간을 함수별로 잰다
 결과: p99 그대로 (진짜 병목은 락 대기)          가장 넓은 칸 = 가장 많이 쓴 곳 → 거기부터
```

- *프로파일러(profiler)*: 프로그램이 시간을(또는 메모리를) **어디에** 쓰는지 함수·호출 경로 단위로 보여 주는 도구.
- *샘플링 프로파일러*: 일정 간격(예: CPU 시간 10ms마다)으로 각 스레드의 **호출 스택**을 찍어 센다. 많이 찍힌 경로가 많이 쓴 경로다.

쉬운 예: 하루 동안 1분마다 "지금 뭐 하고 있었지?"를 적는다.
- 저녁에 세어 보면 "메신저 312번, 코딩 140번"이 나온다. 체감("하루 종일 코딩했다")과 다르다.

똑같은 구조다.\
실무 예: CPU 100%인 서버에서 어떤 메서드가 CPU를 먹나, CPU는 한가한데 응답이 느린 서버에서 스레드가 어디서 기다리나, GC가 잦은 서버에서 누가 할당을 많이 하나.

## 동작·원리

### 1. 무엇을 세느냐에 따라 네 가지 프로파일

```text
 한 스레드의 1초
 ┌──────────┬───────────────┬──────────┬───────────────────┐
 │ CPU에서 실행 │  락 대기(블록)   │ CPU 실행  │  I/O·sleep 대기       │
 └──────────┴───────────────┴──────────┴───────────────────┘
   ▲ CPU 프로파일은 여기만 본다         ▲ off-CPU / wall 프로파일은 여기까지 본다

 CPU 프로파일      : CPU 시간 N ns마다 1샘플 → "누가 CPU를 태우나"
 wall-clock 프로파일: 벽시계 N ms마다 모든 스레드 1샘플(상태 무관) → "스레드가 시간을 어디서 보내나"
 락 프로파일       : 경합한 모니터 진입·park 기반 락(ReentrantLock 등) 대기 시간 → "누가 누구를 기다리나"
 할당 프로파일     : 평균 N 바이트 할당당 1샘플 → "누가 힙을 채우나"(GC 압박의 출처)
```

- *off-CPU 시간*: 스레드가 CPU에서 내려와 기다린 시간(I/O, 락, sleep, 비자발 문맥 전환). Gregg: off-CPU 분석은 CPU 분석과 **짝**이어서, 둘을 합쳐야 스레드 시간 100%가 설명된다.
- async-profiler 4.5 문서 기준 모드: `cpu`, `wall`, `lock`, `alloc`, `nativemem`(native 누수 — 37) 등. `wall`은 "실행·잠·블록 상태와 관계없이 모든 스레드를 같은 간격으로" 샘플한다.

### 2. 플레임 그래프 읽는 법

```text
           ┌────────┐
           │ mix    │                     ← 맨 위 = 실제로 CPU를 쓰던 함수
   ┌───────┴────────┴──────┐ ┌──────┐
   │ heavy                 │ │light │     ← 너비 = 그 프레임이 스택에 나타난 샘플 비율
 ┌─┴───────────────────────┴─┴──────┴─┐
 │ lambda$main$0 (cpu-worker)          │   ← 아래 = 호출자
 └─────────────────────────────────────┘
   x축: 시간 아님! 스택들을 알파벳순으로 정렬해 합친 것
```

- Gregg(brendangregg.com, CACM 59(6) 2016): x축은 스택 표본 모음을 **알파벳순**으로 정렬한 것이지 시간의 흐름이 아니다. y축은 스택 깊이. 프레임이 넓을수록 스택에 자주 있었다.
- 그래서 볼 것은 **넓은 꼭대기**(plateau)다. 자기 시간을 많이 쓴 함수다.
- x축이 시간인 것은 *플레임 차트*(Chrome 개발자 도구)다. 이름이 비슷하지만 다르다.

### 3. 세이프포인트 편향 — 샘플이 "찍을 수 있는 곳"에서만 찍히면

- *세이프포인트(safepoint)*: JVM이 스레드를 멈춰 스택을 안전하게 볼 수 있는 지점. JIT 코드에서는 주로 메서드 반환과 (일부) 루프 되돌아가는 곳에 검사 코드가 있다.
- JVisualVM·YourKit·JProfiler의 샘플링 CPU 프로파일러처럼 JVMTI로 스택을 얻는 전통적 샘플러는 세이프포인트에서만 스택을 본다(Wakart 2016-02). 아래 실험의 `Thread.getStackTrace()` 샘플러도 같은 모양으로 치우쳤다. 그러면 실제로 뜨거운 곳 대신 **다음 세이프포인트**가 책임을 진다.
- async-profiler는 시그널로 스레드를 아무 때나 끊고 스택을 걷는다. README: "Safepoint bias problem을 겪지 않는다."
  - 스택 걷기: CPU 모드 문서는 `perf_events` 스택과 `AsyncGetCallTrace`(HotSpot 비공식 API) 결합으로 설명한다. 4.2부터 HotSpot에서 기본 스택 걷기는 JVM 내부 구조를 직접 읽는 `vm` 모드다(AGCT가 JVM을 죽이거나 스택을 놓치는 문제 때문 — StackWalkingModes 문서).

### 4. 실험: 같은 프로그램, 세 가지 시선

대상 프로그램(`Hot.java`):
- `cpu-worker`: `heavy()`가 `light()`보다 같은 루프를 **3배** 돈다(30만 회 vs 10만 회).
- `lock-holder`: 락을 쥔 채 50ms씩 바쁘게 돈다(CPU 사용).
- `waiter`: 30ms 자고, 그 락을 잡으려 기다린다.

```java
static long mix(long s, int n) {            // 실제 CPU를 쓰는 곳
    for (int i = 0; i < n; i++) s = s * 6364136223846793005L + 1442695040888963407L ^ (s >>> 17);
    return s;
}
static long heavy(long s) { return mix(s, 300_000); }
static long light(long s) { return mix(s, 100_000); }
```

```bash
# 에이전트로 띄워 끝날 때 collapsed(접힌 스택) 텍스트로 저장
java -agentpath:/ap/lib/libasyncProfiler.so=start,event=cpu,interval=10ms,threads,collapsed,file=cpu.txt Hot 6000
java -agentpath:/ap/lib/libasyncProfiler.so=start,event=wall,interval=10ms,threads,collapsed,file=wall.txt Hot 6000
```

- *collapsed 형식*: 한 줄 = `프레임1;프레임2;...;맨위 샘플수`. 플레임 그래프의 입력이다. 아래 숫자는 이 파일을 스레드·프레임별로 합산한 것이다(`agg.py`).

(실험, async-profiler 4.5 + JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 6초, 2026-10-01)

```text
== cpu.txt 총 샘플 1193
  스레드 lock-holder      595 (49.9%)
  스레드 cpu-worker       592 (49.6%)
  스레드 DestroyJavaVM      3 ( 0.3%)
  스레드 C2 CompilerThre     2 ( 0.2%)
  스레드 C1 CompilerThre     1 ( 0.1%)
  cpu-worker: heavy          434
  cpu-worker: light          156
  cpu-worker: 기타               2
== wall.txt 총 샘플 12666
  스레드 DestroyJavaVM    604 ( 4.8%)
  스레드 Reference Handler   604 ( 4.8%)
  스레드 Service Thread   604 ( 4.8%)
  스레드 C2 CompilerThre   604 ( 4.8%)
  스레드 tid=49]          604 ( 4.8%)
  스레드 GC Thread#0      604 ( 4.8%)
  cpu-worker: heavy          438
  cpu-worker: light          157
  waiter: sleep               37
  waiter: 락 대기(monitor)      564
```

- 관찰 1 — CPU: `heavy:light` = 434:156 ≈ 2.8:1. 설계한 3:1에 가깝다. `waiter`는 CPU 프로파일에 **아예 없다**(0샘플).
- 관찰 2 — wall: `waiter`가 나타난다. 시간의 대부분(564샘플)이 `ObjectMonitor::enter`에서 락을 기다리는 데 쓰였다. 이 스레드가 느린 이유는 CPU가 아니라 `lock-holder`다.
- 관찰 3 — wall은 상태와 무관하게 스레드마다 똑같이 센다(위 상위 6개가 각 604샘플 ≈ 6초 ÷ 10ms, `tid=49]`는 이름 없는 스레드를 `agg.py`가 잘못 자른 것). GC·컴파일러 스레드도 다 섞이므로 `threads` 옵션으로 스레드별로 나눠 본다(문서도 "per-thread mode에서 가장 유용"이라 적는다).
- 관찰 4 — 컨테이너 기본 seccomp에서는 `perf_event_open`이 막혔다(`event=cpu-clock` 시도: `Perf events unavailable`). 문서대로 `cpu`는 자동으로 `ctimer` 엔진으로 내려간다. 그래서 커널 스택은 없다.

### 5. 실험: 세이프포인트 편향을 일부러 키우면

JDK 21 C2는 기본으로 긴 루프 안에도 세이프포인트 검사를 넣는다(`UseCountedLoopSafepoints=true`, `LoopStripMiningIter=1000` — 같은 JVM의 `-XX:+PrintFlagsFinal`로 확인). 이 상태에서는 순진한 샘플러도 비율을 비슷하게 맞혔다(`mix <- heavy` 338~411 : `mix <- light` 102~154, 집필 3회 + 재실행 2회).\
검사를 빼면(`-XX:-UseCountedLoopSafepoints -XX:LoopStripMiningIter=0`) 같은 실행에서 두 샘플러가 이렇게 갈린다.

(실험, 같은 환경, 한 JVM 안에서 두 샘플러 동시 실행)

```text
순진한 샘플러(getStackTrace) 맨 위 프레임 <- 호출자: {heavy <- heavy=355, light <- light=72, mix <- heavy=1}
== cpu-nopoll.txt 총 샘플 1001
  스레드 lock-holder      483 (48.3%)
  스레드 cpu-worker       482 (48.2%)
  스레드 naive-sampler     23 ( 2.3%)
  ...
  cpu-worker: heavy          351
  cpu-worker: light          131
$ grep cpu-worker cpu-nopoll.txt | (샘플 수 순 상위 4줄, 앞부분 생략)
Hot.heavy;Hot.mix 303
Hot.light;Hot.mix 118
Hot.heavy;Hot.mix 45
Hot.light;Hot.mix 13
```

- 첫 줄은 순진한 샘플러, 나머지는 async-profiler 결과다.
- 같은 문자열의 줄이 둘씩인 것은 프레임의 **실행 형태**(인터프리터·컴파일 단계)가 달라 따로 집계됐기 때문이다. 기본 collapsed 출력은 그 표시를 지운다. `ann` 옵션을 켜고 다시 돌리면 이렇게 갈린다(같은 환경, 기본 플래그, 3초): `…Hot.heavy_[1];Hot.mix_[j] 162`, `…Hot.heavy_[0];Hot.mix_[j] 45`. async-profiler 4.5 `ProfilerOptions.md`의 `ann` 설명: `_[j]` JIT 컴파일, `_[i]` 인라인, `_[0]` 인터프리터, `_[1]` C1 컴파일. 즉 `heavy`가 C1 단계와 인터프리터 단계에서 따로 찍힌 것이다.

- 관찰 1 — 순진한 샘플러는 맨 위 프레임을 `mix`가 아니라 `heavy`/`light`로 보고했다. 루프 안에 세이프포인트가 없으니, 스택은 `mix`가 끝나고 돌아온 지점에서야 찍힌다.
- 관찰 2 — 비율도 틀어졌다. 순진한 샘플러 355:72 ≈ 4.9:1, async-profiler 351:131 ≈ 2.7:1(실제 일의 비 3:1). 다른 실행의 순진한 샘플러 값은 359:71, 362:46(집필), 430:85, 407:48, 441:52(재실행)로 흔들렸다 — 4.9~8.5:1. async-profiler 쪽은 재실행에서도 2.9~3.1:1이었다.
- 해석: 세이프포인트 위치가 샘플 위치를 정하면, 표본이 "시간을 쓴 곳"이 아니라 "멈출 수 있는 곳"을 가리킨다. 편향의 크기는 JIT 옵션·코드 모양에 따라 달라서, 기본 설정에서는 이 실험처럼 작을 수도 있다.

## 쓰이는 자료구조·알고리즘

- **스택 표본 → 트라이(접두사 트리)** — 스택을 아래(루트)부터 위로 읽은 문자열로 보고, 같은 접두사를 합쳐 세면 호출 트리가 된다. 각 노드의 너비 = 그 접두사를 가진 표본 수. 플레임 그래프는 이 트리를 그린 것이다 → [data-structure/09-trie](../../data-structure/09-trie/2-summary.md).
- **해시맵 집계** — collapsed 형식은 "스택 문자열 → 개수" 맵을 그대로 쓴 것이다. 실험의 `agg.py`도 이 맵을 스레드·프레임으로 다시 묶었다.
- **샘플링 = 일정 간격의 표본 추출** — 무작위 추출이 아니라 정해진 간격으로 찍으므로, 표본 오차에 더해 실행이 주기적이면 그 주기와 맞물려 치우칠 수 있다. 표본 수가 적으면 작은 칸은 오차가 크다. 10ms 간격 6초 = 스레드당 명목상 약 600표본(실험 wall은 604 — 실제 수는 기록 구간에 따라 다르다). 1% 칸(6표본)의 순위는 믿지 않는다.
- **시그널 + 링 버퍼** — `perf_events`는 커널이 샘플을 링 버퍼로 넘긴다([os/31-os-observability-tools](../../os/31-os-observability-tools/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **무엇이 느린가를 먼저 잰다**(19의 측정: p99, 처리량). 프로파일은 "어디서"를 답하지 "얼마나"를 답하지 않는다.
2. CPU 사용률을 본다.
   - 높다 → CPU 프로파일.
   - 낮은데 느리다 → wall-clock 또는 off-CPU(락·I/O 대기). 락이 의심되면 `lock`.
   - GC가 잦다 → `alloc` 프로파일, 힙 누수는 37.
3. 부하를 **재현한 상태에서** 30~60초(예시) 프로파일한다. 한가한 서버의 프로파일은 정상 시 모습일 뿐이다.
4. 넓은 꼭대기부터 본다. 고친 뒤 **같은 조건으로 다시** 잰다(20: 한 가지만 바꾸기).

### 2. 명령

```bash
# 실행 중인 JVM에 붙여 30초 CPU 프로파일 → 플레임 그래프 HTML
asprof -d 30 -e cpu -f /tmp/cpu-%t.html <pid>
# 스레드별 wall-clock (대기 포함)
asprof -e wall -t -i 50ms -d 30 -f /tmp/wall.html <pid>
# 락 경합
asprof -e lock -d 30 -f /tmp/lock.html <pid>
# 할당(평균 512KB 할당당 1샘플)
asprof -e alloc --alloc 512k -d 30 -f /tmp/alloc.html <pid>
# 컨테이너에서 perf_events가 막혔을 때 — CPU 엔진을 명시
asprof -e ctimer -d 30 -f /tmp/cpu.html <pid>
# JDK 내장 JFR로 같은 시간대 기록(GC·락·I/O 이벤트까지)
jcmd <pid> JFR.start duration=60s filename=/tmp/rec.jfr
```

- 컨테이너 안 프로파일: Docker 기본 seccomp가 `perf_event_open`을 막는다. 문서의 선택지는 seccomp 완화(+`SYS_ADMIN`), `--fdtransfer`, 또는 `ctimer`(async-profiler "Profiling In Container").
- 운영 부하: 샘플 간격을 너무 짧게 잡지 않는다. `--all`(모든 모드 동시)은 문서가 운영에 권하지 않는다.

### 3. 코드에서 프로파일 범위를 좁히기 (Java)

```java
// 문제 요청만 프로파일하고 싶을 때: 한 엔드포인트에서 짧게 켜고 끈다(async-profiler Java API)
AsyncProfiler p = AsyncProfiler.getInstance();
p.execute("start,event=wall,interval=5ms,threads,file=/tmp/slow-%t.html");
try { handleSlowRequest(); }
finally { p.execute("stop"); }
```

- 이 방식은 라이브러리를 앱에 넣는 비용이 있다. 보통은 밖에서 `asprof`로 붙이는 편이 간단하다.

## 장애 시나리오와 대처

### 1. ⚠ 추측 최적화 → 병목이 아닌 곳을 고친다

- 현상: 2주 걸려 직렬화 라이브러리를 바꿨는데 p99가 그대로다.
- 보이는 형태: 변경 전후 지연 분포가 같다. 나중에 wall 프로파일을 떠 보니 시간의 대부분이 커넥션 풀 대기였다.
- 원인: CPU 프로파일만 봤거나, 아예 재지 않았다. CPU 프로파일에는 기다리는 스레드가 보이지 않는다(실험: `waiter` 0샘플).
- 대처: 먼저 CPU가 바쁜지 본다. 한가하면 wall·lock·off-CPU부터. 고친 뒤 같은 조건으로 다시 잰다.

### 2. ⚠ 세이프포인트 편향 프로파일러가 엉뚱한 메서드를 지목한다

- 현상: 프로파일러가 지목한 작은 메서드(`setResult` 같은)를 고쳤는데 아무것도 안 바뀐다.
- 보이는 형태: 맨 위 프레임이 루프를 가진 함수가 아니라 그 **호출자**나 바로 다음 호출. 위 실험에서 `mix` 대신 `heavy`/`light`가 맨 위에 찍히고 비율이 4.9~8.5:1로 부풀었다(실행마다 다르다).
- 원인: 세이프포인트에서만 스택을 찍는 샘플러(JVMTI 기반 JVisualVM 류 — Wakart 2016-02, 실험의 `Thread.getStackTrace` 샘플러).
- 대처: 세이프포인트 밖에서 찍는 프로파일러(async-profiler)를 쓴다. 세이프포인트 밖에서 찍는 다른 프로파일러 — AsyncGetCallTrace 기반 프로파일러, 그리고 AGCT가 아닌 자체 샘플러(스레드를 잠깐 멈추고 `JfrGetCallTrace`로 스택을 읽음 — JDK 21 소스 `jfrThreadSampler.cpp`)를 쓰는 JFR(JMC) — 도 `-XX:+UnlockDiagnosticVMOptions -XX:+DebugNonSafepoints`가 꺼져 있으면 디버그 정보 해상도(PC → 바이트코드 위치 변환) 때문에 위치가 흐려진다 — Wakart 2016-06 후속 글은 이것이 세이프포인트 편향과는 다른 문제라고 적는다. JDK 21에서는 JFR을 켜도 이 플래그 기본값은 `false`였다(`-XX:StartFlightRecording -XX:+PrintFlagsFinal`로 확인) [?: JDK 21 JFR에서의 효과 수치는 확인하지 않음].

### 3. 컨테이너에서 CPU 프로파일이 안 되거나 커널 시간이 안 보인다

- 현상: `asprof -e cpu`가 경고를 내거나, 시스템 콜에서 쓰는 시간이 프로파일에 없다.
- 보이는 형태: `perf_event_open ... failed: Operation not permitted`, `Perf events unavailable`(위 실험).
- 원인: Docker 기본 seccomp·`kernel.perf_event_paranoid`. `ctimer`로 내려가면 커널 스택이 없다.
- 대처: 커널 스택이 필요하면 호스트에서 특권으로 붙이거나 seccomp를 조정한다. 아니면 `ctimer`로 사용자 공간만 본다.

### 4. 프로파일이 "평소 모습"만 보여 준다

- 현상: 장애 때 느렸는데, 다음 날 뜬 프로파일은 깨끗하다.
- 보이는 형태: 넓은 칸이 정상 업무 코드뿐. 지연 그래프의 스파이크와 프로파일 시각이 안 겹친다.
- 원인: 문제 구간이 지나간 뒤 떴다. 프로파일은 그 시간대의 표본만 담는다.
- 대처: 지속 프로파일링(낮은 빈도로 상시 기록, 예: async-profiler `loop` 옵션·JFR 상시 기록)으로 장애 시각의 표본을 남긴다. 사고 때는 완화 전에 짧게 떠 둔다(26의 증거 보존).

## 핵심 문장

- 프로파일링은 "어디서" 시간을 쓰는지 함수·호출 경로로 답한다. "얼마나 느린가"는 측정(19)이 먼저다.
- CPU 프로파일은 기다리는 스레드를 보지 못한다. 실험에서 락을 기다리던 `waiter`는 CPU 프로파일 0샘플, wall 프로파일에서는 대부분이 락 대기였다.
- 플레임 그래프의 x축은 시간이 아니라 알파벳순 정렬이고, 넓은 꼭대기가 자기 시간을 많이 쓴 함수다.
- 세이프포인트에서만 찍는 샘플러는 뜨거운 함수 대신 다음 세이프포인트를 지목한다. 실험에서 루프 검사를 빼자 순진한 샘플러는 3:1을 4.9~8.5:1로 보고했다.
- 컨테이너에서는 perf_events가 막혀 있는 경우가 많다. 엔진(cpu/ctimer)과 커널 스택 유무를 확인하고 해석한다.

## 관련 주제·근거

- 선행
  - [19-performance-measurement](../19-performance-measurement/2-summary.md) — 지연 분포·벤치마크 방법
  - [os/31-os-observability-tools](../../os/31-os-observability-tools/2-summary.md) — `perf`·`perf_event_paranoid`·스택 표본 집계
- 후속·연결
  - [37-memory-leak-and-heap-analysis](../37-memory-leak-and-heap-analysis/2-summary.md) — 힙 분석 심화
  - [20-performance-method-and-amdahl](../20-performance-method-and-amdahl/2-summary.md), [38-microbenchmarking](../38-microbenchmarking/2-summary.md)
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — 사고 중 증거 보존
  - [os/36-server-concurrency-architectures](../../os/36-server-concurrency-architectures/2-summary.md) — 이벤트 루프가 막히는 모양(wall 프로파일로 보인다)
- 논문·글
  - Brendan Gregg, "The Flame Graph", Communications of the ACM 59(6):48–57, 2016 (ACM Queue 게재본) — 정의·해석
  - brendangregg.com "Flame Graphs"(x축 = 알파벳순, 플레임 차트와 차이), "Off-CPU Analysis"(CPU 분석과 짝) <https://www.brendangregg.com/flamegraphs.html> · <https://www.brendangregg.com/offcpuanalysis.html>
  - Nitsan Wakart, "Why (Most) Sampling Java Profilers Are Fucking Terrible", 2016-02 — 세이프포인트 편향, Mytkowicz 외 PLDI 2010 "Evaluating the Accuracy of Java Profilers" 인용 <http://psy-lob-saw.blogspot.com/2016/02/why-most-sampling-java-profilers-are.html>
  - Nitsan Wakart, "The Pros And Cons of AsyncGetCallTrace Profilers", 2016-06 — `DebugNonSafepoints` <http://psy-lob-saw.blogspot.com/2016/06/the-pros-and-cons-of-agct.html>
- 문서·소스
  - async-profiler v4.5 README·docs(`ProfilingModes.md`, `CpuSamplingEngines.md`, `StackWalkingModes.md`, `ProfilingInContainer.md`, `ProfilerOptions.md`, `FlamegraphInterpretation.md`) <https://github.com/async-profiler/async-profiler/tree/v4.5/docs>
  - JDK 21 `jcmd` 매뉴얼(JFR.start, Thread.print) <https://docs.oracle.com/en/java/javase/21/docs/specs/man/jcmd.html>
- 실험 목록
  - E1 CPU vs wall: `Hot.java`(heavy 3 : light 1, lock-holder·waiter) + async-profiler 4.5 에이전트 `event=cpu`/`event=wall`, `collapsed` 출력을 `agg.py`로 합산. JDK 21.0.12 temurin 컨테이너 `--cpus=2`, 6초. `event=cpu-clock`으로 perf_events 차단 확인
  - E2 세이프포인트 편향: 같은 JVM 안에서 `Thread.getStackTrace` 10ms 샘플러 vs async-profiler. 기본 플래그 3회, `-XX:-UseCountedLoopSafepoints -XX:LoopStripMiningIter=0` 3회
