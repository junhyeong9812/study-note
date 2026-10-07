# language/25-lto-pgo-and-binary-size — LTO·PGO와 바이너리 크기: 파일 경계를 넘는 최적화, 프로파일, 심볼 — 정리 (힌트)

## 해결하는 문제

C 컴파일러는 보통 **파일(번역 단위) 하나씩** 컴파일한다. 그래서 파일을 넘는 최적화를 못 한다.

```text
  main.c                      util.c
  for (...) s += scale(i);    int scale(int x) { return x * 3 + 1; }
         │                    int unused_helper(int x) { ... }   ← 아무도 안 부름
         ▼
  main.o: call scale   ← scale의 본문을 모른다 → 인라인 불가
  util.o: scale, unused_helper 둘 다 기계어로 → 링커는 받은 대로 붙인다
```

- *번역 단위(translation unit)*: 컴파일러가 한 번에 보는 소스 하나(전처리 뒤 `.c` 파일 하나).
- 해결책 세 가지
  - *LTO(link-time optimization)*: 컴파일러 중간 표현(IR)을 목적 파일에 넣어 두고, **링크 때** 전체를 한 덩어리로 보고 최적화한다.
  - *링크 단계 데드 코드 제거*: 아무도 참조하지 않는 함수·데이터를 링커가 버린다.
  - *PGO(profile-guided optimization)*: 대표 실행에서 모은 "어디가 뜨거운가" 정보로 다시 컴파일한다.
- 그리고 크기: 디버그 심볼·정적 링크가 바이너리를 키운다. 컨테이너 이미지 pull 시간에 그대로 들어간다.

쉬운 예: 책 편집.
- 장마다 다른 편집자가 따로 다듬으면, 장을 넘나드는 중복이나 안 쓰는 부록을 못 잡는다(파일별 컴파일).
- 마지막에 한 사람이 전체를 읽으면 잡는다. 대신 그 사람이 병목이 된다(full LTO).
- 독자가 실제로 많이 읽는 장을 조사해 그 장을 더 공들여 다듬는다(PGO). 조사 대상이 엉뚱하면 엉뚱한 장을 다듬는다.

똑같은 구조다.

실무 예:
- 릴리스 빌드에 full LTO를 켰더니 링크 단계만 수 분, 메모리 수백 MB~수 GB로 늘었다(예시).
- 성능 테스트용 합성 입력으로 PGO를 했더니 실제 운영 경로가 오히려 느려졌다.
- 디버그 심볼이 든 채 배포해 바이너리·이미지가 수배로 커졌다.

컴파일러 최적화 자체(인라이닝·데드 코드 제거·SSA)는 [language/22](../22-ir-and-optimization/2-summary.md), 링커·로더의 동작(심볼 테이블·재배치·정적/동적 링크)은 [os/29](../../os/29-linking-and-loading/2-summary.md)가 다룬다. 이 노트는 **빌드 끝 단계의 최적화와 그 대가**를 본다.

## 동작·원리

### 1. LTO — IR을 목적 파일에 넣어 두고 링크 때 합친다

```text
  보통 빌드                         gcc -flto                              clang -flto=thin (ThinLTO)
  .c ─(최적화+코드 생성)─▶ .o(기계어)   .c ─▶ .o( .gnu.lto_* 절에 GIMPLE )    .c ─▶ .o( LLVM IR 비트코드 + 요약 )
  .o + .o ─(링커)─▶ 실행 파일        .o + .o ─(링크 때 합쳐 최적화·코드 생성)   요약만 합쳐 전역 분석 → 모듈별 병렬 최적화
```

- GCC 13.3 문서(`-flto`): 소스를 컴파일하면 GIMPLE(내부 표현)을 목적 파일의 특수 ELF 절에 쓴다. 링크할 때 모든 함수 본문을 읽어 **한 번역 단위인 것처럼** 다룬다. 그래서 `bar.o`의 함수를 `foo.o`에 인라인할 수 있다.
  - 이 호스트의 gcc 13.3에서 `main_lto.o`에는 `.gnu.lto_*` 절이 15개 있었고, 크기는 5,744바이트(보통 `main.o` 1,808바이트)였다. 크기는 빌드 경로 문자열에 따라 몇 바이트 달라진다(사실 점검 재빌드 5,736바이트, 절 15개는 같음).
  - 같은 문서: 컴파일 단계와 링크 단계 모두에 `-flto`와 최적화 옵션을 주라고 권한다.
- 링크 때 할 일을 병렬로 나누는 법(GCC 13.3)
  - `-flto=n`: 링크 시 최적화·코드 생성을 n개 병렬 작업으로. `-flto=auto`는 make 작업 서버를 쓰거나 CPU 스레드 수를 감지한다.
  - `-flto-partition=`: 기본 `balanced`(크기가 고른 조각), `1to1`(원래 파일대로), `one`, `none` 등.
- Clang ThinLTO 문서
  - monolithic(full) LTO는 모든 입력을 한 모듈로 합치므로 시간·메모리 면에서 확장되지 않고, 빠른 증분 컴파일도 막는다.
  - ThinLTO는 컴파일 때 모듈 요약을 덧붙이고, 링크 때 요약만 합쳐 전역 분석을 한다. 함수 가져오기(importing)를 포함한 변환은 이후 모듈별로 완전히 병렬로 한다.
  - 이 호스트에서 `clang -flto=thin -c`의 결과 `.o`는 `file` 기준 `LLVM IR bitcode`였다. 링크는 `-fuse-ld=gold`(LLVMgold 플러그인)로 했다.

### 2. 링크 단계 데드 코드 제거

```text
  -ffunction-sections : 함수마다 자기 절(.text.scale, .text.unused_helper ...)
  -Wl,--gc-sections   : 진입점에서 참조를 따라 닿지 않는 절을 버림
  LTO                 : 전체 호출 그래프를 보고 쓰이지 않는 함수를 아예 만들지 않음
```

- GCC 문서(`-ffunction-sections`): 링커의 `--gc-sections`와 함께 쓰면 (strip 뒤) 정적 링크 실행 파일이 작아질 수 있다.
- 원리는 "뿌리에서 닿는 것만 남긴다"는 도달성이다. 네이티브 이미지의 닫힌 세계 분석과 같은 생각이다([24번](../24-aot-native-image-and-startup/2-summary.md)).

### 3. PGO — 계측 → 대표 실행 → 재컴파일

```text
  ① gcc -O2 -fprofile-generate   →  계측 바이너리(흐름 그래프 간선 일부에 카운터)
  ② 대표 입력으로 실행             →  .gcda (어느 함수·분기가 몇 번)
  ③ gcc -O2 -fprofile-use         →  뜨거운 곳: 속도 최적화·배치,  안 돈 곳: 크기 최적화
```

- GCC 13.3 문서(`-fprofile-arcs`): 함수마다 흐름 그래프의 신장 트리를 구하고, 트리에 없는 간선만 계측한다. 나머지 간선의 횟수는 그 값에서 계산된다.

- GCC 13.3 문서(`-fprofile-partial-training`): `-fprofile-use`에서는 **훈련 실행에서 실행되지 않은 부분 전부가 속도 대신 크기로 공격적으로 최적화된다.**
  - 이 옵션을 주면 훈련에서 안 돈 함수는 프로파일이 없던 것처럼 최적화된다. 문서는 "훈련이 대표적이지 않을 때 성능이 낫지만 코드가 상당히 커진다"고 적는다.
- LLVM 문서("How To Build Clang and LLVM with Profile-Guided Optimizations"): PGO는 수집한 프로파일이 실제 사용 방식을 대표할 때 가장 잘 된다. x86_64 코드 생성만 훈련하면 ARM을 타깃할 때는 크게 도움이 안 된다는 예를 든다.
- JIT는 실행 중에 프로파일을 모으므로 이 단계가 따로 없다. 대신 워밍업이 필요하다([23번](../23-jit-tiered-compilation-and-warmup/2-summary.md)).

### 4. 바이너리 크기 — 무엇이 차지하나

```text
  실행 파일(ELF) = 코드(.text) + 데이터 + 심볼 테이블(.symtab) + 디버그 정보(.debug_*)
                                          └──────── strip이 지우는 부분 ────────┘
  동적 링크: libc는 실행 시 로더가 붙인다(ldd에 libc.so.6)   정적 링크: libc 코드가 파일 안에
```

- *strip*: 실행에 필요 없는 심볼 테이블·디버그 정보를 지운다. 크래시 스택을 함수 이름으로 보려면 디버그 정보를 **따로 보관**해야 한다(해석 — 분리 보관 방식은 도구마다 다르다).
- 정적·동적 링크의 장단(배포 단순성 vs 크기·보안 패치)은 [os/29](../../os/29-linking-and-loading/2-summary.md).

### 실험 1: 파일을 넘는 인라인 — `-O2` vs `-O2 -flto` (gcc 13.3)

```bash
gcc -O2 -c main.c && gcc -O2 -c util.c && gcc main.o util.o -o app_o2
gcc -O2 -flto -c main.c -o main_lto.o && gcc -O2 -flto -c util.c -o util_lto.o && gcc -O2 -flto main_lto.o util_lto.o -o app_lto
objdump -d --no-show-raw-insn app_o2 | awk '/<main>:/,/^$/'
```

환경: i7-13700HX 호스트에서 직접 실행(컨테이너·`--cpus` 제한 없음, 다른 작업과 동시에 돌았을 수 있음), gcc 13.3.0, objdump(binutils), 단일 스레드 프로그램, 3회(+ 사실 점검 재실행 3회: 0.55~0.59s / 0.28~0.32s).

```text
  -O2 (LTO 없음): main 안          -O2 -flto: main 안
    call   11e0 <scale>              lea    0x1(%rdx,%rdx,2),%ecx     ← x*3+1이 루프 안에 펼쳐짐
  남은 심볼: scale unused_helper     남은 심볼: (없음)
  실행 시간(3억 회): 0.57~0.64s      0.25~0.33s
```

- LTO가 `scale`을 `main`에 인라인했다. `lea 0x1(%rdx,%rdx,2)`는 `rdx*3 + 1`이다.
- 쓰이지 않는 `unused_helper`도, 인라인된 뒤 남은 `scale`도 사라졌다.
- 같은 두 파일을 clang 18 ThinLTO(`-flto=thin`, gold 플러그인)로 링크해도 `main`에 `call scale`이 없었고 `unused_helper`는 사라졌다. `scale` 심볼은 남았다.
- LTO 없이 `-ffunction-sections` + `-Wl,--gc-sections`만 써도 `unused_helper`는 사라졌다(`scale`은 호출되므로 남음).

### 실험 2: full LTO의 대가 — 링크 단계로 일이 몰린다 (gcc 13.3)

생성한 C 파일 61개(파일마다 함수 250개가 사슬로 호출)를 `-O2 -g`로 빌드했다. 호스트에서 직접 순차 실행(컨테이너·`--cpus` 제한 없음), `/usr/bin/time`의 경과 시간과 최대 RSS, 1회. 사실 점검에서는 다시 돌리지 않았다(생성 파일이 남아 있지 않음).

```text
                           컴파일 61개(순차)          링크
  -O2 -g                   275.8s, maxRSS  61MB       0.28s, maxRSS  31.7MB
  -O2 -g -flto (링크 -flto=2)  35.7s, maxRSS  33MB     168.4s, maxRSS 184.6MB
```

- LTO는 컴파일 단계에서 코드 생성을 미루고 IR만 쓴다. 미룬 일이 링크 단계로 옮겨 가 링크가 0.28초 → 168초, 최대 RSS가 약 6배가 됐다.
- 전체 합은 이 생성 코드에서 오히려 LTO가 짧았다(276s vs 204s). 하지만 **파일 하나만 고쳐도** 보통 빌드는 그 파일 컴파일(평균 약 4.5초) + 링크 0.28초면 되고, full LTO는 링크 168초를 통째로 다시 한다(계산값 — 해석). CI 타임아웃·증분 빌드 저하의 모양이다.
- `maxRSS`는 `/usr/bin/time`이 보고한 값으로, 링크 중 가장 큰 단일 프로세스의 최대 RSS다(합계 아님 — 해석).
- 생성 코드가 인위적이라 절대값보다 "링크 단계로 이동"이라는 모양을 본다.

### 실험 3: 대표성 없는 프로파일 — 운영 경로가 2배 느려졌다 (gcc 13.3)

```c
__attribute__((noinline)) long path_a(int rounds) { ... s += a[i] ^ r; ... }           // 훈련에서만 도는 경로
__attribute__((noinline)) long path_b(int rounds) { ... s += (a[i] * 7 + r) >> 1; ... } // 운영에서 뜨거운 경로
int main(int argc, char **argv) { ... strcmp(argv[1], "a") == 0 ? path_a(rounds) : path_b(rounds); }
```

```bash
gcc -O2 -fprofile-generate -fprofile-update=single -c pgo.c && gcc -fprofile-generate pgo.o -o pgo_gen
./pgo_gen b 2000      # 대표 훈련(운영과 같은 B)      / 비대표 훈련: ./pgo_gen a 2000
gcc -O2 -fprofile-use -c pgo.c && gcc pgo.o -o pgo_use_b
gcc -O2 -fprofile-use -fprofile-partial-training -c pgo.c ...   # 비대표 훈련 + 부분 훈련 옵션
```

환경: 호스트에서 직접 실행(컨테이너·`--cpus` 제한 없음), gcc 13.3.0, 운영 입력 B(20만 라운드), 각 3회 + 사실 점검 재빌드·재실행 각 3회(아래 범위에 포함).

```text
                                    실행 시간          path_b 명령 수   xmm/ymm 명령
  PGO 없음                           0.55~0.69s         37              20
  PGO, 대표 훈련(B)                   0.62~0.70s         85 (재빌드 83)   21
  PGO, 비대표 훈련(A만)                1.14~1.22s         21               0   ← 벡터화 사라짐
  PGO, 비대표 + -fprofile-partial-training  0.63~0.67s    83              21
```

- 훈련에서 한 번도 안 돈 `path_b`가 크기 우선으로 컴파일됐다. 벡터 명령이 0개가 되고 약 2배 느려졌다. GCC 문서의 `-fprofile-partial-training` 설명과 같은 결과다.
- `-fprofile-partial-training`을 주자 `path_b`가 프로파일 없는 것처럼 컴파일되어 원래 속도로 돌아왔다.
- 대표 훈련 PGO는 이 작은 커널에서 PGO 없음보다 빠르지 않았다. PGO의 이득은 작업 부하와, 프로파일이 바꾸는 최적화(분기 배치·인라인·루프 언롤·벡터화 등 — GCC `-fprofile-use` 목록)에 따라 다르다(해석 — 이 실험은 이득이 아니라 **위험**을 보인다).
- 첫 시도에서는 `-o` 이름을 바꾸며 빌드해 `.gcda` 이름이 맞지 않아 프로파일이 적용되지 않았다. `-Wno-missing-profile`이 그 경고를 숨겼다. 목적 파일 이름을 훈련·재빌드에서 같게 맞춰야 한다(GCC 문서: `.gcda` 이름은 `-o`로 준 출력 이름에서 만든다).

### 실험 4: 크기 — 디버그 정보·strip·정적 링크

```text
  작은 프로그램(main.c + util.c)                    바이트
  -O2                                               16,112
  -O2 -g                                            19,152   (빌드 경로에 따라 몇 바이트 다름 — 재빌드 19,160)
  -O2 -g 후 strip                                   14,472
  -O2 + -ffunction-sections --gc-sections           15,960
  -O2 -flto                                         15,976
  -O2 -static                                      785,416   (size: text 667,989 — libc 코드가 들어옴)
  -O2 -static 후 strip                             706,576

  실험 2의 큰 프로그램                               바이트
  -O2 -g                                        13,309,872   (text 2,750,940)
  -O2 -g 후 strip                                2,762,888   ← 약 79%가 디버그 정보·심볼
  -O2 -g -flto                                   5,860,856   (text 1,183,695)
  -O2 -g -flto 후 strip                          1,194,120
```

- 작은 프로그램은 페이지 정렬·ELF 머리 같은 고정 비용이 대부분이라 차이가 작다.
- 큰 프로그램에서는 디버그 정보가 크기의 약 4/5였다. LTO는 `size` 기본(Berkeley) 형식의 text를 약 57% 줄였다. 이 text 열에는 읽기 전용 데이터도 들어가므로, 기계어(`.text` 절)만의 감소율은 따로 재지 않았다(인라인 뒤 남는 함수가 적어짐 — 해석).

## 쓰이는 자료구조·알고리즘

- **전역 호출 그래프** — LTO의 인라이닝·상수 전파·죽은 함수 제거는 전체 프로그램의 호출 그래프 위에서 한다. ThinLTO는 그래프 대신 **요약 인덱스**(함수 위치·참조)를 합쳐 메모리를 줄인다.
- **도달성 기반 제거** — 진입점(공유 라이브러리면 보이는 심볼 전부, 실행 파일은 `--gc-keep-exported`를 줄 때 내보낸 심볼까지 — GNU ld 문서)을 뿌리로, 참조를 따라 닿지 않는 절·함수를 버린다. 그래프 탐색이다([algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)).
- **그래프 분할(partitioning)** — GCC LTO의 `balanced` 분할은 함수를 크기가 고른 조각으로 나눠 병렬 코드 생성한다.
- **카운터 배열(프로파일)** — 계측 바이너리는 일부 간선(신장 트리 밖)에 카운터를 두고 `.gcda`로 쓴다. 나머지 간선 횟수는 계산으로 복원한다. 이 빈도로 뜨거운/차가운 경로, 블록 배치, 인라인 예산을 정한다.

## 적용 — 풀어나가는 법

### 1. 빌드 설정을 고르는 순서

1. **배포 바이너리에서 디버그 정보를 분리한다.** 가장 싸고 효과가 크다(실험 4: 약 79%).
2. **링크 단계 데드 코드 제거**(`-ffunction-sections -fdata-sections -Wl,--gc-sections`). 빌드 비용이 거의 없다.
3. **LTO**: 릴리스 빌드에만. 큰 코드베이스면 ThinLTO(clang)나 `-flto=auto`·분할(gcc)로 링크 병렬화. 링크 시간·메모리를 CI 지표로 남긴다.
4. **PGO**: 운영과 같은 경로를 지나는 훈련 입력을 만들 수 있을 때만. 못 만들면 `-fprofile-partial-training`(gcc)을 검토한다.

### 2. 확인 명령

```bash
objdump -d --no-show-raw-insn app | awk '/<main>:/,/^$/' | grep call   # 인라인됐나(call이 남았나)
nm app | grep ' T '                                                    # 남은 함수 심볼
size app                                                               # text·data·bss
readelf -S app | grep debug                                            # 디버그 절이 남았나
file main.o                                                            # LLVM IR bitcode면 ThinLTO 목적 파일
/usr/bin/time -v gcc -flto=auto ... 2>&1 | grep -E 'Elapsed|Maximum resident'   # 링크 비용
```

### 3. 컨테이너 이미지에서

- 빌드 단계(디버그 포함)와 실행 단계(strip된 바이너리만)를 나누는 멀티 스테이지 빌드로 이미지를 줄인다.
- 정적 링크는 라이브러리 의존성을 없애지만 크기가 늘고 libc 보안 패치를 재빌드로만 받는다([os/29](../../os/29-linking-and-loading/2-summary.md)).

## 장애 시나리오와 대처

### 1. full LTO를 켜자 링크 시간·메모리가 급증 → CI 타임아웃 (⚠)

- **현상**: 릴리스 파이프라인의 링크 단계만 수 분~수십 분, 러너 OOM 또는 타임아웃.
- **보이는 형태**: 컴파일 로그는 빨리 지나가고 마지막 `ld`/`lto1`·`ld.lld` 프로세스가 오래 돈다. `Maximum resident set size`가 크다.
- **원인**: LTO는 코드 생성을 링크 때로 미룬다. full LTO는 모든 모듈을 한 덩어리로 합친다(Clang ThinLTO 문서: 시간·메모리 면에서 확장되지 않는다). 실험 2에서 링크가 0.28초 → 168초, 최대 RSS 약 6배.
- **대처**: ThinLTO(clang) 또는 `-flto=auto`·분할(gcc), 릴리스 빌드에만 LTO, 링크 단계를 큰 러너로. 커리큘럼의 "CI 타임아웃"은 일반 사례로 확인하지 못했고[?], 이 노트는 모양만 실험으로 보였다.

### 2. 대표성 없는 프로파일로 PGO → 실제 핫 경로가 느려짐 (⚠)

- **현상**: PGO 빌드 배포 뒤 특정 기능·고객군만 느려졌다. 벤치마크(훈련 입력)는 빨라졌다.
- **보이는 형태**: 프로파일러에서 그 경로의 함수가 이전보다 명령이 적고 루프가 벡터화되지 않음(`objdump`에 xmm/ymm 사라짐).
- **원인**: 훈련에서 안 돈 코드는 크기 우선으로 최적화된다(GCC 문서). 실험 3: 운영 경로가 0.55~0.69초 → 1.14~1.22초.
- **대처**: 훈련 입력을 운영 트래픽 표본(재생)으로, 정기적으로 다시 수집. 불가하면 `-fprofile-partial-training`. 릴리스 전 운영 대표 시나리오로 회귀 측정.

### 3. 디버그 심볼이 든 채 배포 → 바이너리 수배·이미지 pull 지연 (⚠)

- **현상**: 새 버전 이미지가 갑자기 커졌고, 스케일 아웃 때 새 노드의 pull이 오래 걸린다.
- **보이는 형태**: `readelf -S`에 `.debug_*` 절, `size`의 text에 비해 파일 크기가 몇 배. 실험 4: 13.3MB 중 text 2.75MB.
- **원인**: 빌드 플래그에 `-g`가 들어간 채 strip 단계가 빠졌다.
- **대처**: 배포 산출물은 strip, 디버그 정보는 별도 보관(심볼 서버·아티팩트 저장소). 이미지 크기를 CI 검사로 막는다. pull 시간이 콜드 스타트에 주는 영향은 [reliability/42](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md).

### 4. PGO 프로파일이 조용히 적용되지 않는다

- **현상**: PGO를 켰다는데 성능도 코드도 그대로다.
- **원인**: `.gcda` 이름·경로가 재빌드의 목적 파일과 맞지 않았다. `-Wno-missing-profile`로 경고를 숨겼다(실험 3의 첫 시도).
- **대처**: 훈련·재빌드의 출력 이름·경로를 같게 맞춘다(`-fprofile-dir`는 프로파일 **디렉터리**만 바꾸므로 이름이 다르면 해결하지 못한다). 경고를 숨기지 않는다. 적용 여부를 `objdump`로 한 번은 눈으로 확인한다.

## 핵심 문장

- 파일 단위 컴파일은 파일을 넘는 인라인과 죽은 함수 제거를 못 한다. LTO는 IR을 목적 파일에 넣어 두고 링크 때 전체를 한 번역 단위처럼 최적화한다.
- LTO의 대가는 코드 생성이 링크 단계로 옮겨 가는 것이다. full LTO는 그 단계에 일이 몰려 병목이 되고(gcc는 `-flto=n`으로 링크 때 코드 생성을 병렬로 나눌 수 있지만, 실험 2는 `-flto=2`에서도 링크 168초), ThinLTO는 요약 인덱스와 병렬 백엔드로 이를 줄인다.
- PGO는 훈련 실행에서 돈 곳을 뜨겁다고 믿는다. GCC는 안 돈 곳을 크기 우선으로 컴파일하므로, 대표성 없는 프로파일은 운영 경로를 느리게 만든다.
- 링크 단계 데드 코드 제거는 "진입점에서 닿는 것만 남긴다"는 도달성 분석이다.
- 배포 바이너리 크기의 큰 몫은 디버그 정보일 수 있다. strip하고 디버그 정보는 따로 보관한다.

## 관련 주제·근거

- 선행
  - [22-ir-and-optimization](../22-ir-and-optimization/2-summary.md)
  - [os/29-linking-and-loading](../../os/29-linking-and-loading/2-summary.md) — 심볼·재배치·정적/동적 링크
- 후속·연결
  - [23-jit-tiered-compilation-and-warmup](../23-jit-tiered-compilation-and-warmup/2-summary.md) — 실행 중 프로파일로 하는 최적화(JIT)
  - [24-aot-native-image-and-startup](../24-aot-native-image-and-startup/2-summary.md) — 닫힌 세계 도달성 분석
  - [architecture/09-isa-and-machine-code](../../architecture/09-isa-and-machine-code/2-summary.md) · [architecture/21-simd-and-gpu](../../architecture/21-simd-and-gpu/2-summary.md)(벡터 명령)
  - [reliability/42-cold-start-and-scale-from-zero](../../reliability/42-cold-start-and-scale-from-zero/2-summary.md) — 이미지 pull과 콜드 스타트
- 근거
  - GCC 13.3 "Options That Control Optimization" — `-flto[=n]`(GIMPLE을 ELF 절에, 링크 때 한 번역 단위처럼, `-flto=auto`·jobserver), `-flto-partition`(기본 balanced), `-fuse-linker-plugin`, `-ffunction-sections`(`--gc-sections`와 함께), `-fprofile-use`, `-fprofile-partial-training` <https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Optimize-Options.html>
  - GCC 13.3 "Program Instrumentation Options" — `-fprofile-arcs`(신장 트리 밖 간선만 계측, `.gcda` 이름은 출력 이름에서), `-fprofile-dir`(프로파일 디렉터리) <https://gcc.gnu.org/onlinedocs/gcc-13.3.0/gcc/Instrumentation-Options.html>
  - GNU ld `--gc-sections`·`--gc-keep-exported`(뿌리 집합) <https://sourceware.org/binutils/docs/ld/Options.html> · GNU `size`(Berkeley 형식 text에 읽기 전용 데이터 포함) <https://sourceware.org/binutils/docs/binutils/size.html>
  - Clang "ThinLTO" — monolithic LTO의 시간·메모리 확장성 문제, 요약·결합 인덱스·병렬 백엔드, `-flto=thin`, gold 플러그인 <https://clang.llvm.org/docs/ThinLTO.html>
  - LLVM "How To Build Clang and LLVM with Profile-Guided Optimizations" — 'benchmark' 선택: 프로파일이 실제 사용을 대표해야 한다 <https://llvm.org/docs/HowToBuildWithPGO.html>
- 실험 목록(i7-13700HX 호스트, 컨테이너 없이 호스트 gcc 13.3.0·clang 18.1.3·binutils — CPU 제한 없음, 시간 값은 호스트 부하에 따라 흔들린다)
  - 실험 1: `main.c`+`util.c` — `-O2` vs `-O2 -flto` objdump·nm·실행 시간 3회, clang `-flto=thin -fuse-ld=gold`, `-ffunction-sections --gc-sections`
  - 실험 2: 생성 C 파일 61개 — `-O2 -g` vs `-O2 -g -flto`(링크 `-flto=2`) 컴파일·링크 시간과 최대 RSS(`/usr/bin/time`), 1회
  - 실험 3: `pgo.c` — PGO 없음 / 대표 훈련 / 비대표 훈련 / 비대표 + `-fprofile-partial-training`, 각 3회 + objdump 명령 수
  - 실험 4: 위 산출물의 파일 크기·`size`, `-g`·strip·`-static`
