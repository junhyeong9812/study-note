# language/23-jit-tiered-compilation-and-warmup — 정답

## 정답

### 1. 처음부터 C2로 하지 않는 이유

- 컴파일 비용: C2는 느리고 CPU를 많이 쓴다. 한두 번 도는 코드까지 C2로 컴파일하면 시작이 늦어진다. 그래서 카운터가 문턱을 넘은 뜨거운 코드만 컴파일한다.
- 프로파일: C2는 "이 분기는 거의 안 간다", "이 호출 지점엔 `Sq`만 온다" 같은 실행 정보를 가정으로 쓴다. 이 정보는 인터프리터·level 3에서 실행해 봐야 모인다.

### 2. 다섯 단계

```text
  level 0 인터프리터 ──▶ level 3 C1 + 전체 프로파일 ──▶ level 4 C2      (보통 경로)
  level 0 ──▶ level 2 C1 + 카운터만 ──▶ (C2 큐가 줄면) level 3 ──▶ level 4   (C2 큐가 길 때)
  level 0 ──▶ level 3 ──▶ level 1 C1 최종(프로파일 없음)                   (사소한 메서드)
  level 4 ──(가정 깨짐)──▶ 역최적화 → level 0 → 다시 올라감
```

- 근거: OpenJDK 21 `compilationPolicy.hpp` 주석.
- MDO(MethodData object): 메서드별 프로파일. 호출·분기 횟수, 호출 지점에 온 타입 등을 인터프리터와 level 3 코드가 계속 갱신하고, C1·C2가 컴파일할 때 읽는다.

### 3. 기본 / C1만 / 인터프리터만

- 실험 1(JDK 21.0.12, `--cpus=2`, 각 3회)의 마지막 구간(10001~100000번째)
  - 기본 3.0~3.3us, C1만 3.3~3.6us, `-Xint` 62.8~69.3us(사실 점검 재실행 2회: 2.8~3.2 / 3.5~3.8 / 62.1~62.8us).
  - 기본 ≈ C1만 ≪ `-Xint`(약 20배 차이). 이 루프는 반복마다 앞 값에 의존해 C2가 C1보다 크게 낫지 않았다(해석).
- 101~1000 구간: 기본 8.2~8.6us(재실행 6.7~7.5us), C1만 3.4~3.8us(재실행 3.8~3.9us).
  - 기본 경로는 이 구간을 주로 level 3(프로파일을 모으는 C1 코드)으로 돈다고 본다(해석 — 컴파일 로그 시각을 호출 구간과 맞추지 않아, 인터프리터·OSR·level 4가 섞였을 수 있다).
  - `compilationPolicy.hpp` 주석은 level 3이 level 2보다 약 30% 느리다고 적는다. C1만(level 1)은 프로파일 없이 바로 최종 코드다(해석).

### 4. `%`와 OSR

- `%` 있는 줄: OSR 컴파일. `@ 4`는 루프가 시작되는 바이트코드 위치다. 메서드가 아직 안 끝났는데 루프 중간에서 컴파일된 코드로 갈아탄다.
- `%` 없는 줄: 메서드 전체 컴파일. 다음 호출부터 쓴다.
- OSR 조건: 백엣지 수 `b > TierXBackEdgeThreshold · s`(JDK 21 기본 Tier3 60,000, Tier4 40,000).
- `s` = `queue_size_X / (TierXLoadFeedback · compiler_count_X) + 1`. 컴파일 큐가 길수록 커져 문턱을 올린다(큐가 밀릴 때 요청을 줄이는 되먹임).

### 5. 단형 → 혼합

- 실험 2(3회): 단형 2.07~2.24us → 섞인 직후 200회 23.91~26.16us(약 11~13배) → 재컴파일 뒤 6.12~6.92us(약 3배). 사실 점검 재실행 3회: 단형 1.86~2.30us → 22.48~31.66us(약 11~17배) → 5.98~8.42us(약 3~4배).
- 확인
  - 워밍업 뒤 `PrintInlining`: `Deopt$Sq::area (10 bytes) inline (hot)`, `TypeProfile (844846/844846 counts) = Deopt$Sq` — 단형 가정으로 인라인했다.
  - 섞인 직후 `-Xlog:deoptimization=debug`: `level=4 Deopt.total(...) trap_bci=27 class_check maybe_recompile` — 호출 지점(bci 27)의 타입 가드 실패로 역최적화.
  - 재컴파일 뒤 `PrintInlining`: `Deopt$Shape::area (0 bytes) virtual call` — 인라인을 포기하고 가상 호출.

### 6. `made not entrant`만으로는 모른다

- 두 경우 모두 찍힌다.
  - 정상 교체: 더 높은 단계 코드가 생겨 낮은 단계 코드를 더는 진입하지 않게 할 때(실험 1에서 level 3 코드).
  - 역최적화: level 4 코드의 가정이 깨졌을 때(실험 2).
- 구별: 어느 단계 코드가 그렇게 됐나(level 3 → 정상 교체일 가능성, level 4 → 역최적화일 가능성), 그리고 `-Xlog:deoptimization=debug`의 `reason`(`class_check`, `unstable_if` 등)이 같은 시각에 있나.

### 7. 추측과 되돌리기

- 셋 다 "과거에 자주 그랬으니 이번에도 그럴 것"에 걸고 빠른 경로를 미리 준비한다.
  - 분기 예측: 예측한 방향의 명령을 미리 실행한다. 틀리면 파이프라인의 그 명령들을 버린다([architecture/18](../../architecture/18-pipelining-and-branch-prediction/2-summary.md)).
  - 인라인 캐시: 지난번 타입의 메서드 주소를 호출 지점에 적어 둔다. 틀리면 조회 경로로 간다.
  - C2 단형 인라인: 타입 가드 + 본문 인라인. 틀리면 그 실행은 역최적화로 인터프리터 프레임으로 돌아가고, 재컴파일된다. 기존 컴파일 코드는 트랩 동작에 따라 바로 무효화(`made not entrant`)되거나 당분간 유지된다(`maybe_recompile`). 되돌리는 범위가 가장 크다.

### 8. 새 파드만 p99 3배

- 확인
  - 인스턴스별 지연: 새 파드만 높고 시간이 지나면 내려가나.
  - 새 파드의 CPU: C1/C2 컴파일 스레드 사용. `-XX:+PrintCompilation`에 level 3·4 컴파일이 몰리나. `jcmd <pid> Compiler.queue`에 요청이 쌓였나.
  - 첫 요청 수십 ms(클래스 로딩)와 이후 수천 요청의 점진적 감소(JIT)를 나눠 본다([reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md)).
- 막기
  - 대표 요청으로 스스로 데운 뒤 Ready. 운영 타입·분기를 고루 포함한다.
  - 새 파드 트래픽 가중치를 천천히 올린다.
  - AOT 캐시(JDK 24 JEP 483, JDK 25 JEP 515 프로파일 포함).
  - 시작 직후 CPU 여유를 둔다.

### 9. 코드 캐시 가득 참

- 무슨 일: C2 최종 코드(와 level 1 코드)가 사는 'non-profiled nmethods' 구역이 가득 차 JIT 컴파일이 멈췄다. 새로 뜨거워지는 코드는 인터프리터·하위 단계에 머문다. JDK 21에서 `UseCodeCacheFlushing`(기본 true)이면 코드 언로딩으로 공간이 생길 때 컴파일이 다시 켜지지만(`restarted_count`), 공간이 계속 모자라면 느린 상태가 이어진다.
- 볼 것: `jcmd <pid> Compiler.codecache`의 구역별 `used`·`max_used`, `full_count`, `Compilation: enabled/disabled`. 클래스 수가 계속 느는지(`jcmd <pid> VM.classloader_stats` 등)도 본다.
- 대처: `-XX:ReservedCodeCacheSize`나 경고가 알려 준 구역 플래그를 늘린다. 동적 클래스(프록시·람다·스크립트 엔진) 생성 누수를 고친다.
- 문구: OpenJDK 21 `codeCache.cpp` 기준으로 분할 캐시는 `CodeHeap '<이름>' is full. Compiler has been disabled.` + 구역 플래그 안내, 분할하지 않은 캐시는 `CodeCache is full. Compiler has been disabled.` + `-XX:ReservedCodeCacheSize=` 안내.

### 10. 새 결제 수단 켜자 스파이크

- 가설: 기존 결제 처리 경로의 호출 지점·분기가 "기존 수단만"으로 단형·편향 프로파일이 굳었다. 새 수단이 오자 타입 가드(`class_check`)나 분기 가드(`unstable_if`)가 실패해 역최적화 → 느린 코드 → 재컴파일이 일어난다.
- 확인: `-Xlog:deoptimization=debug`에 결제 메서드의 `reason` 줄, `PrintCompilation`에 같은 메서드의 level 4 `made not entrant`와 재컴파일. 스파이크 시각과 맞춰 본다.
- 대처: 워밍업·카나리 트래픽에 새 수단을 포함한다. 같은 메서드가 반복해 재컴파일되면 수단별로 경로를 나눠(분기를 앞으로 빼서) 각 호출 지점을 단형에 가깝게 만든다.
