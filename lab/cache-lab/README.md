# cache-lab — Spring 캐시 구현체(Caffeine·Redis·Multi-Level) k6 부하 비교

- 원본: `/home/jun/project/cache-lab` · 기간: 2026-01-19 (git 커밋 기준, 단일 세션) · 스택: Java 21 + Spring Boot 3.5.0, Caffeine 3.1.8, Redis 7, H2, k6, Prometheus + Grafana
- 상태: **완료** (시나리오 5종 + 캐시 4종 비교 측정 완료)

## 무엇을 알고 싶었나 — 질문·가설

- 캐시가 실제로 얼마나 빨라지게 하는가 — DB 50ms 지연 대비 캐시 조회의 정량 효과.
- 워크로드 유형(읽기 집중 / 읽기·쓰기 혼합 / Hot Key / Cold Start)에 따라 캐시 효과가 어떻게 달라지는가.
- 캐시 구현체(Caffeine 로컬 / Redis 분산 / Caffeine+Redis 다층) 중 어떤 환경에 무엇이 적합한가.

학습 목표 성격의 실험: 캐시 개념 → Spring Cache Abstraction → 구현체별 이론 문서를 먼저 정리하고, k6 로 정량 측정해 이론을 확인하는 구조.

## 실험 환경과 방법

| 항목 | 값 |
|------|-----|
| 실행 일시 | 2026-01-19 20:43 ~ 20:59 |
| 데이터 | 1,000개 상품 (H2 인메모리) |
| DB 시뮬레이션 지연 | 50ms |
| 부하 도구 | k6 (시나리오 스크립트 + 캐시별 스크립트) |
| 프로파일 | `local`(Caffeine) / `redis` / `multi-level` / `no-cache` |

```
k6 ──► Spring Boot 앱 ──► 캐시(프로파일별) ──► H2 (+50ms 지연)
                              │
                              └─ Redis 7 (redis / multi-level 프로파일)
```

## 결과 — 시나리오/캐시별

### 시나리오별 (Caffeine 기준)

| 시나리오 | p95 Latency | RPS | 에러율 | 총 요청 |
|---------|-------------|-----|--------|--------|
| 1. 읽기 집중 (95%) | **3.52ms** | 349/s | 0% | 83,872 |
| 2. 읽기/쓰기 혼합 (70/30) | 53.87ms | 208/s | 0% | 50,058 |
| 3. Hot Key (90% 집중) | **3.83ms** | **1,887/s** | 0% | 339,799 |
| 4. Cold Start | 51.65ms → 3.7ms | 480/s | 0% | 86,460 |
| 5. Cache vs No-Cache | 51.26ms vs 51.78ms | 105/s | 0% | 18,958 |

출처: `/home/jun/project/cache-lab/docs/result/00-summary.md`

- 캐시 효과: DB 조회 50ms → 캐시 조회 ~3.5ms — **93% 향상 (14배)**.
- 쓰기 30% 혼합 시 p95 3.52ms → 53.87ms (**15배 느려짐**) — 캐시 무효화로 인한 miss 증가.
- Hot Key (90/10): Hot p95 3.77ms · 1,698/s vs Cold p95 4.78ms · 189/s — Cache Stampede 현상 없음.
- Cold Start: 워밍업 약 30초 (Cold 구간 p95 51.65ms → Warm 3.7ms).

### 캐시 구현체별 비교

| 순위 | 캐시 | p95 | 평균 | RPS | No Cache 대비 |
|------|------|-----|------|-----|---------------|
| 1 | **Multi-Level** (Caffeine+Redis) | **2.06ms** | 2.05ms | 216.5/s | 96.1% 개선 |
| 2 | Caffeine | 3.11ms | 2.63ms | 215.5/s | 94.1% 개선 |
| 3 | Redis | 4.95ms | 3.92ms | 212.1/s | 90.7% 개선 |
| - | No Cache | 53.15ms | 52.08ms | 153.7/s | (Baseline) |

출처: `/home/jun/project/cache-lab/README.md` · `docs/result/cache-comparison-result.md`

## 종합 결론

- **캐시 효과는 확실하다** — 어떤 구현체든 No Cache(p95 53.15ms) 대비 90%+ 개선(10~25배).
- **환경이 선택을 정한다**: 단일 서버 → Caffeine(간편·충분히 빠름, p95 3ms) / 다중 서버 → Redis(일관성·관리 용이, p95 5ms) / 다중 서버 + 극한 성능 → Multi-Level(p95 2ms, 복잡성 감수).
- **쓰기 비율이 캐시의 적** — 읽기 100% 대비 쓰기 30% 혼합에서 15배 저하. `allEntries` 전체 무효화 대신 부분 무효화·짧은 TTL 전략 필요.
- **Cold Start 는 실측으로 확인된 리스크** — 워밍업 30초. 프로덕션은 워밍업 전략(기동 시 인기 데이터 선조회) 필요.
- Multi-Level 은 최고 성능이지만 Spring Cache 추상화 미지원(직접 구현)·메모리 2배(L1+L2) — 단일 서버라면 Caffeine 만으로 충분.

## 한계·남은 질문

원본 `00-summary.md`의 "다음 단계"에 명시된 미수행 항목:

- TTL 변화 테스트 (1분/5분/30분 TTL별 Hit Ratio 비교) — 미수행.
- 실제 DB 테스트 (H2 → PostgreSQL 재측정) — 미수행. DB 지연이 고정 50ms 시뮬레이션이라 실 DB 의 캐시·커넥션 풀 효과는 반영 안 됨.
- 부하 생성기(k6)와 SUT 분리 여부는 문서에 명시 없음 — 단일 머신 측정으로 보임.
- Multi-Level 의 L1 Hit Rate 는 "~90% 이상 추정"으로만 기록 (실측 수치 문서에 없음).

## 원본 문서 지도

| 문서 | 내용 |
|------|------|
| `README.md` | 결과 요약 + 실행 방법 + 프로파일 설정 |
| `docs/01-cache-concept.md` ~ `06-cache-strategy.md` | 이론 6편 — 캐시 개념·Spring Cache·Caffeine·Redis·Ehcache·전략 |
| `docs/scenarios/01~05-*.md` | 시나리오 설계 5편 (읽기 집중·혼합·Hot Key·Cold Start·구현체 비교) |
| `docs/result/00-summary.md` | 시나리오별 통합 결과 (주 출처) |
| `docs/result/scenario-0N-result.md` | 시나리오별 상세 결과 5편 |
| `docs/result/cache-comparison-result.md` | 캐시 구현체 비교 통합 결과 |
| `docs/result/cache-{no-cache,caffeine,redis,multi-level}-result.md` | 구현체별 상세 결과 |
