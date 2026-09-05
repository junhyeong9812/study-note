# sync-async-lab — 동기/비동기 동시성 모델 12종 서버 성능 실측

- 원본: `/home/jun/project/sync-async-lab` · 기간: 2026-04-05 ~ 2026-04-12 (git 커밋 기준) · 스택: Python(FastAPI·Django·Starlette 3.13t no-GIL), Java(Spring MVC·WebFlux·Virtual Threads·GraalVM Native), Go, Node.js, PostgreSQL, k6, Docker Compose
- 상태: **완료** (1차 가설 H1~H8 + 확장 실험 A1~A3·B1~B5·C1·풀 곡선·free-threaded 실측)

## 무엇을 알고 싶었나 — 질문·가설

"async 가 빠르다"는 통념을 워크로드 유형별로 분해해 실측한다. 가설을 **먼저 문서로 등록**(`report/hypotheses.md`)하고 검증하는 방식.

- H1~H2: FastAPI sync vs async — I/O-bound 에선 3~5배 차이, CPU-bound 에선 무차이일 것.
- H3~H4: Django 는 async+ORM 이 sync 와 비슷하고, raw async 는 훨씬 빠를 것.
- H5~H6: Java 는 WebFlux ≈ Virtual Threads > MVC (I/O 고부하), CPU 에선 무차이일 것.
- H7~H8: Go 는 I/O 최상위·CPU 는 Java 급, sync/async 코드 스타일 구분이 무의미할 것.
- 확장: 고부하(1000 VU)·실 DB(PostgreSQL)·ProcessPool·GraalVM Native·WebSocket·Graceful Shutdown·커넥션 풀 곡선·Python 3.13 free-threaded.

## 실험 환경과 방법

- 서버 12종을 동일 조건 Docker 컨테이너(2 CPU, 512MB RAM)로 실행, k6 는 별도 PC(192.168.55.158 → 192.168.55.114)에서 부하.
- 공통 엔드포인트: `GET /io`(sleep 200ms) / `GET /cpu`(fibonacci 38) / `GET /db`(pg_sleep 200ms) / `WS /ws`(에코).
- I/O 테스트 200 VU(확장은 500→1000), CPU 테스트 100 VU — ramp-up 30s → sustained 60s → ramp-down 30s.

## 결과

### 1차 — I/O-bound (sleep 200ms, 200 VU)

| Server | req/s | avg | p95 |
|--------|------:|----:|----:|
| go-server | 743.6 | 201.7ms | 203.0ms |
| java-spring-webflux | 741.8 | 202.1ms | 202.9ms |
| java-spring-mvc | 739.8 | 202.6ms | 202.4ms |
| python-fastapi-async | 735.6 | 203.7ms | 207.3ms |
| java-spring-virtual | 717.6 | 209.0ms | 221.0ms |
| python-django-sync | 648.4 | 231.4ms | 340.0ms |
| python-django-async-raw | 269.1 | 558.1ms | 750.2ms |
| python-django-async (ORM) | 260.6 | 576.8ms | 812.5ms |
| python-fastapi-sync | 188.5 | 798.3ms | 1011.7ms |

출처: `/home/jun/project/sync-async-lab/report/results.md`

- H1 입증: FastAPI async 가 sync 의 **3.9배** (가설 3~5배 적중).
- H3 **예상 외**: Django 는 sync(WSGI+gthread 200스레드)가 async+ORM 보다 **2.5배 빠름** — sync_to_async 오버헤드.
- H4 **기각**: raw async(269) ≈ ORM async(261) — 병목은 ORM 이 아니라 **Django ASGI 자체** (같은 asyncio.sleep 인데 FastAPI 의 1/2.7).
- H5 부분: 200 VU 에선 MVC=WebFlux=Virtual (스레드풀 200 이 충분) — 고부하로 재검 필요.

### 1차 — CPU-bound (fibonacci(38), 100 VU): Python 전 서버 ~1 req/s (GIL — 2코어에서도 사실상 싱글코어), Java 2.4~2.7 / Go 2.3 req/s (Python 의 2배+).

### 확장 A1 — 1000 VU 고부하 (여기서 진짜 차이가 드러남)

| 순위 | 서버 | req/s | 동시성 모델 |
|------|------|------:|------------|
| 1 | Go | 3179.5 | goroutine |
| 2 | Spring WebFlux | 3160.9 | Reactor 이벤트 루프 |
| 3 | Spring Virtual Threads | 2333.0 | M:N 가상 스레드 |
| 4 | FastAPI async | 1558.1 | asyncio 이벤트 루프 |
| 5 | Spring MVC | 953.5 | OS 스레드 200 (포화, p95 1004ms) |
| 6 | Django sync | 942.9 | gthread 200 (포화) |
| 7 | Django async-raw | 281.9 | ASGI 오버헤드 |
| 8 | FastAPI sync | 195.9 | 스레드풀 ~40 (극심한 포화) |

출처: `/home/jun/project/sync-async-lab/report/results-extended.md` §A1

### 확장 A2·#5 — 실 DB I/O 는 커넥션 풀이 왕

- pg_sleep 200ms · 풀 20 → Go/WebFlux 가 sleep 실험의 3000+ 에서 **~50-97 req/s 로 급락** (이론 상한 = 20/0.2s = 100 req/s). FastAPI async 만 954 req/s 예외(asyncpg 효율).
- 풀 크기 곡선(FastAPI async): 10→48.7 / 20→96.1 / 50→230.0 / 100→425.0 req/s — 이론 상한의 92~97% 선형 확장, 풀 100 에서 85%로 하락. 출처: §#5

### 확장 B·C·# — 나머지

| 실험 | 판정 | 핵심 수치 |
|------|------|----------|
| B1 ProcessPoolExecutor (CPU) | ⚠️ 부분 입증 | 0.133→0.178 req/s = **1.33x** (가설 2x 미달 — IPC·이벤트 루프 직렬화·CPU 스케일링). Docker 에선 fork hang 으로 실패, 로컬 재실험 |
| B2 GraalVM Native | ⚠️ 부분 입증 | 콜드 스타트 **346ms vs 6,520ms (18.8x)** · Idle 메모리 **37MB vs 212MB (5.7x)** · I/O 동률 · CPU 처리량 **20% 열세** (JIT 런타임 최적화) |
| B3 WebSocket 1000 VU | ✅ 입증 | RTT: Node 1.16ms / Go 2.81 / WebFlux 2.71 / **FastAPI 28.83ms 악화**. 메모리: Go 42MB / WebFlux 232MB |
| B5 Node.js | ✅ 부분 입증 | I/O 에서 FastAPI async 와 동급 (같은 싱글 스레드 이벤트 루프) |
| C1 Graceful Shutdown | ❌ 기각 | 전 서버 0% 드롭 — 동시성 모델 무관, 프레임워크 구현 품질 문제 |
| #1 Python 3.13 free-threaded | ✅ 입증 | ThreadPoolExecutor 로 **2.16x** 병렬화 성공, 대신 단일 스레드 성능 **~2x 느림** → 절대 처리량은 ProcessPool 과 비슷 |
| #6 JVM Warm-up | ⚠️ 관찰 미미 | CPU 절전 모드가 효과를 가림 |

출처: `report/results-extended.md` §B1·B2·B3·B5·C1·#1·#6

## 종합 결론

- **저부하는 모델 차이를 숨긴다**: 200 VU 에선 MVC=WebFlux=Go, 1000 VU 에서 3배+ 격차 — 스레드풀 포화 여부가 갈림길.
- **Django 에서 async 는 오히려 성능 악화** — 병목은 ORM 이 아니라 ASGI 파이프라인 자체(구조적).
- **실 DB I/O 에선 동시성 모델보다 커넥션 풀 크기가 처리량 상한을 결정** (풀 크기 ∝ 처리량, 상한의 92~97%).
- **Go 는 blocking 스타일 코드로 최상위** — goroutine+netpoller 가 sync/async 구분을 무의미하게 만든다.
- **GIL 우회의 두 길**: ProcessPool 1.33x vs no-GIL ThreadPool 2.16x — 그러나 no-GIL 은 단일 스레드 2x 페널티로 절대 성능은 비슷. 3.13t 는 아직 PoC 단계(pydantic 등 미호환).
- **GraalVM Native 의 자리**: 서버리스·스케일아웃(콜드 스타트 18.8x·메모리 5.7x) / long-running CPU 서버는 JIT 이 유리.

## 한계·남은 질문

- 원본 자체 경고: B1·#1·#6 재실험은 로컬 직접 실행이며 **CPU 가 절전 모드(~1200MHz)** — #6(JVM warm-up)은 이 때문에 "관찰 미미" 판정. Docker 1차 결과와 환경이 다르다.
- A2 에서 FastAPI async 만 954 req/s 로 풀 이론 상한(100)을 크게 초과한 원인은 "asyncpg 파이프라이닝 또는 커넥션 재활용 추정"으로만 기록 — 미규명. (p90 0.0ms 등 A2 표 일부 수치는 원본 그대로이나 이상치로 보임.)
- A3(Django ASGI flamegraph 프로파일링)은 가설만 있고 결과 절이 근거 서술 수준 — 미들웨어 원인 실증 미완.
- Java MVC VU 5000+ 극한 테스트, B4 부하 중 메모리 정밀 비교 등은 `report/future-work.md` 에 미완으로 남음.

## 원본 문서 지도

| 문서 | 내용 |
|------|------|
| `README.md` | 서버 12종 표 · 엔드포인트 · 핵심 결과 요약 |
| `report/hypotheses.md` | 1차 가설 H1~H8 (사전 등록) |
| `report/results.md` | 1차 실측 — I/O·CPU 원시 데이터 + 가설 판정 |
| `report/hypotheses-extended.md` | 확장 가설 A1~A3 · B1~B5 · C1 |
| `report/results-extended.md` | 확장 실측 820줄 — 고부하·DB·Native·WebSocket·no-GIL·풀 곡선 (주 출처) |
| `report/future-work.md` | 건너뛴 실험과 사유 |
| `docs/architecture.md` · `docs/project-overview.md` | 구성·개요 |
| `docs/plans/*/learned.md` | 작업 단위별 배운 것 (B1·B2·B3·pool-curve·free-threaded 등) |
| `servers/` | 서버 12종 구현 · `k6/` 부하 스크립트 |
