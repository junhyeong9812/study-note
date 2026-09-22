# proto-bench — HTTP vs gRPC 성능 역전 포인트를 7개 Phase로 추적

- 원본: `/home/jun/project/proto-bench` · 기간: 2026-01-14 \~ 2026-01-17 (git 커밋 기준) · 스택: Kotlin + Spring Boot 3.x, grpc-kotlin, Gradle(Kotlin DSL), k6
- 상태: **완료** (Phase 1\~7 측정 완료 — GC 가설 검증 등은 별도 프로젝트 제안으로 종료)

## 무엇을 알고 싶었나 — 질문·가설

- "gRPC는 HTTP/2 + Protobuf니까 HTTP/JSON보다 빠를 것이다"라는 통념이 실제로 어떤 조건에서 성립하는가.
- 페이로드 크기·동시 사용자 수·데이터 구조 복잡도 3축에서 **HTTP ↔ gRPC 성능이 역전되는 지점**을 수치로 찾는다.
- Phase별 가설: ①대용량 1MB에서 gRPC 우위? ②소용량에서 HTTP 헤더 오버헤드로 gRPC 유리? ③고동시성에서 HTTP/2 멀티플렉싱 효과? ④100\~500KB 사이 역전? ⑤복잡 구조에서 Protobuf 파싱 유리? ⑥극한 복잡도에서 HTTP 역전? ⑦역전 원인은 CPU 사용량?

## 실험 환경과 방법

- 구조: `k6 → apiServer(Gateway) → dataServer(Data Gen)`, 구간별로 HTTP 또는 gRPC 선택. 비교 4종: HTTP/JSON(Base64), HTTP/Binary(raw bytes), gRPC/Unary, gRPC/Stream(64KB 청크).
- 기본 조건: VU 10, 각 30초, JIT 워밍업 5초 (Phase 3만 VU 50→500 가변, Phase 7은 CPU 100ms 샘플링 + 2회 반복).

## 결과 — Phase별

### Phase 1: 대용량 1MB — 가설 기각

| 프로토콜 | Throughput (req/s) | Latency avg | Latency p95 |
|----------|-------------------|-------------|-------------|
| **HTTP/Binary** | **2,506.24** | **2.70ms** | **4.00ms** |
| gRPC/Unary | 1,186.64 | 6.87ms | 11.23ms |
| HTTP/JSON | 514.54 | 17.42ms | 23.81ms |
| gRPC/Stream | 210.72 | 44.53ms | 67.08ms |

출처: `/home/jun/project/proto-bench/docs/phase/PHASE1_RESULT.md` (README에도 동일 표)

HTTP/Binary가 gRPC/Unary의 약 2배 — 직렬화 없는 raw bytes vs Protobuf 직렬화+HTTP/2 프레이밍 비용.

### Phase 2: 소용량 1KB·10KB — 가설 검증

| 크기 | 1위 | Throughput | HTTP/Binary | gRPC 우위 |
|------|-----|-----------|-------------|-----------|
| 1KB | gRPC/Unary | 5,876.83 | 3,695.04 | +59% |
| 10KB | gRPC/Unary | 5,748.21 | 4,026.66 | +43% |

출처: `/home/jun/project/proto-bench/README.md` (Phase 2 절) · 상세: `docs/phase/PHASE2_RESULT.md`

1KB에서 HTTP 헤더가 페이로드의 \~40%인 반면 gRPC 프레이밍은 \~5%.

### Phase 3: 고동시성 50\~500 VU — 역전 포인트 100\~200 VU

| VU | HTTP/JSON | HTTP/Binary | gRPC/Unary | 승자 |
|----|-----------|-------------|------------|------|
| 50 | 10,081 | **12,151** | 10,775 | HTTP (+13%) |
| 100 | 11,358 | **13,840** | 13,423 | HTTP (+3%) |
| 200 | 12,573 | 14,147 | **15,388** | gRPC (+9%) |
| 500 | 12,558 | 14,325 | **16,052** | gRPC (+12%) |

출처: `/home/jun/project/proto-bench/README.md` (Phase 3 절) · 상세: `docs/phase/PHASE3_RESULT.md`

gRPC/Unary만 50→500 VU에서 +49% 스케일 — HTTP는 200 VU부터 포화, 500 VU에서 gRPC p95가 HTTP보다 36% 낮음.

### Phase 4: 페이로드 크기 역전 탐색 — 역전 포인트 100\~200KB

| 크기 | HTTP/Binary | gRPC/Unary | 승자 |
|------|-------------|------------|------|
| 10KB | 3,745 | 6,268 | gRPC (+67%) |
| 50KB | 4,089 | 5,628 | gRPC (+38%) |
| 100KB | 3,904 | 5,067 | gRPC (+30%) |
| 200KB | 4,714 | 4,128 | HTTP (+14%) |
| 500KB | 3,883 | 2,430 | HTTP (+60%) |

출처: `/home/jun/project/proto-bench/README.md` (Phase 4 절) · 상세: `docs/phase/PHASE4_RESULT.md`

대용량에서 Protobuf 직렬화·`ByteString.copyFrom()` 복사 비용이 지배적.

### Phase 5·6: 데이터 구조 복잡도 — \~150 필드에서 HTTP 역전

| 복잡도 (필드 수) | HTTP/JSON | HTTP/Binary | gRPC/Unary | 승자 |
|-----------------|-----------|-------------|------------|------|
| Simple (5) | 3,602 | 3,627 | **6,007** | gRPC +67% |
| Medium (13) | 3,273 | 3,393 | **5,527** | gRPC +69% |
| Complex (50) | 3,154 | 2,955 | **4,415** | gRPC +40% |
| Ultra (\~150) | **2,074** | 2,154 | 1,847 | HTTP/JSON +12% |
| Extreme (\~500) | **419** | 482 | 407 | HTTP/JSON +3% |

출처: `/home/jun/project/proto-bench/README.md` (Phase 5·6 절) · 상세: `docs/phase/PHASE5_RESULT.md`, `PHASE6_RESULT.md`

원본 추정 원인: Protobuf Builder 객체 생성/해제 비용 누적(Extreme은 빌더 호출 \~800회). Complex에서 HTTP/Binary < HTTP/JSON 역전도 관찰.

### Phase 7: CPU 사용량 분석 — "CPU 때문" 가설 부분 기각

Ultra 복잡도, 2차 테스트 기준:

| 프로토콜 | Throughput | Avg Process CPU | CPU 효율 (req/s/%) |
|----------|-----------|-----------------|--------------------|
| HTTP/Binary | 2,248 | 11.9% | **188.4** |
| HTTP/JSON | 2,013 | 16.8% | 120.1 |
| gRPC/Stream | 1,913 | 13.8% | 139.1 |
| gRPC/Unary | 1,880 | 13.8% | 135.8 |

출처: `/home/jun/project/proto-bench/README.md` (Phase 7 절) · 상세: `docs/phase/PHASE7_RESULT.md`

gRPC가 CPU를 더 쓰는 게 아니라 **HTTP/JSON이 가장 높은 CPU(16.8%)로도 gRPC보다 빠름** → CPU 사용량은 역전의 직접 원인이 아님. GC Count와 성능의 반비례 상관은 확인, 인과는 미검증(별도 프로젝트 A 제안). 1·2차 재현성 확인(Ultra +4%/+7%, Extreme +5%/+6% HTTP 우위 일관).

## 종합 결론

- **"gRPC가 항상 빠르다"는 오해** — gRPC 우위는 ①소용량(≤100KB) ②고동시성(200+ VU) ③중간 복잡도(≤50 필드)에서만.
- 3축의 역전 포인트: **페이로드 100\~200KB · 동시성 100\~200 VU · 복잡도 \~150 필드**.
- 대용량 전송(≥200KB)은 HTTP/Binary가 14\~60% 우위 — 직렬화 오버헤드 부재.
- 극한 복잡도(≥150 필드)에서 HTTP가 12\~18% 역전 — 빌더 비용 추정이나, Phase 7에서 CPU 원인은 기각되어 **GC 압박 가설로 이관**.
- CPU 효율은 HTTP/Binary가 압도적(188 vs 136 req/s/%) — CPU 제한 환경에선 HTTP/Binary.

## 한계·남은 질문

- 역전의 진짜 원인(GC 압박 가설) 미검증 — Heap/GC 알고리즘 변경·프로파일링은 "향후 별도 프로젝트 A"로만 제안됨.
- localhost 측정 — 실네트워크 지연·손실 환경에서 Protobuf 크기 절감 효과 미검증(제안 B).
- DB 조회 등 I/O 포함 현실 시나리오 없음(제안 D).
- ⚠️ `docs/phase/EXPERIMENT_ROADMAP.md`는 낡은 문서(Phase 2 "진행 중" 표기) — 현황 파악용으로 인용 불가. 최신 종합본은 README.

## 원본 문서 지도

| 문서 | 내용 |
|------|------|
| `README.md` | 전체 요약 — Phase 1\~7 결과표·선택 가이드·핵심 인사이트 (최신 정본) |
| `docs/phase/PHASE1_RESULT.md` | 1MB 대용량 상세 (GC·Heap 수치 포함) |
| `docs/phase/PHASE2~7_DESIGN.md` | 각 Phase 가설·조건 설계 |
| `docs/phase/PHASE2~7_RESULT.md` | 각 Phase 상세 결과 (2\~4는 1,500\~3,800줄 대형 문서) |
| `docs/phase/EXPERIMENT_ROADMAP.md` | ⚠️ 낡음 — 인용 금지 |
| `docs/GRPC_GUIDE.md`, `docs/K6_GUIDE.md` | 도구 가이드 |
