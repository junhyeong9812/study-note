# 02. Payment Consistency Lab

결제 시스템에서 발생할 수 있는
중복 요청 / 부분 실패 / 재처리 / 정산 불일치를 다룬 실험 프로젝트

## Load Baseline (근거)

| 사례 | 관찰된 수치 | 출처 |
|------|-----------|------|
| 국내 패션 커머스 세일 (11일) | 온라인 판매 775만 개, 평균 분당 약 489개 | [주간한국](https://weekly.hankooki.com/news/articleView.html?idxno=7171654) |
| 같은 행사 겨울 시즌 첫날 | 25시간 동안 분당 600개 이상 판매 | [뉴스톱](https://www.newstopkorea.com/news/articleView.html?idxno=41103) |
| 글로벌 상한 참고 | 피크 초당 58.3만 건 주문 생성 | [Chain Store Age](https://chainstoreage.com/alibabas-singles-day-event-breaks-records-74-billion-sales) |
| PG 웹훅 재전송 규약 | 2xx 응답이 없으면 재전송, 7회 실패 시 '실패' 처리 | [토스페이먼츠 문서](https://docs.tosspayments.com/blog/virtual-account-webhook) |
| PG 호출 타임아웃 설정 사례 | 연결 3초, 읽기 10초 (결제 대기 만료보다 짧게) | [GitHub PR 사례](https://github.com/ccommit/stylehub/pull/65) |
| PG 응답 지연 사례 | 수백 ms ~ 수 초 | [GitHub 이슈 사례](https://github.com/hkjbrian/gongu/issues/146) |

> 국내 세일 수치는 기간 평균이다. 오픈 순간 피크는 평균의 수십 배로 가정한다(추정).

**채택 기준 (제안값)**: 평시 50 TPS, 세일 오픈 피크 500 TPS, 한계 탐색 2,000 TPS

## Questions

1. 결제 API를 사용자가 10번 눌렀다면?
2. PG 결제는 성공했는데 우리 DB commit이 실패했다면?
3. DB commit 직후 서버가 죽었다면?
4. 이벤트가 두 번 소비됐다면?
5. 결제 원장과 PG 정산 결과가 다르다면?
6. PG 응답이 타임아웃이라 성공인지 실패인지 모른다면?
7. PG가 느려질 때 결제와 무관한 API까지 느려진다면?

## Architecture

```
Client
  ↓
Payment API
  ↓
Payment Transaction
 ├── Payment
 └── Outbox
        ↓
      Worker
        ↓
     Mock PG  ←── 지연 / 실패 / 응답 유실 주입
        ↓
     Webhook

PG Settlement
      ↓
Reconciliation Batch
      ↓
Ledger comparison
```

## Load Profile

| 항목 | 값 |
|------|---|
| 평시 부하 | 50 TPS, 10분 |
| 피크 부하 | 500 TPS, 5분 |
| 한계 탐색 | 2,000 TPS까지 단계 증가 |
| 중복 클릭 | 전체 사용자의 10%가 1초 안에 동일 요청 10회 |
| Mock PG 지연 | p50 300ms / p99 3s |
| Mock PG 장애 | 5xx 1%, 응답 유실(승인됐지만 응답 없음) 1% |
| 타임아웃 | 연결 3s / 읽기 10s |
| 서버 장애 주입 | DB commit 직후 프로세스 강제 종료, N회 반복 |
| 정산 대조 | 1일 결제 10만 건 중 0.1% 불일치 인위 주입 |

## Results

| # | Question | 시도한 방식 | 측정 결과 | 최종 선택 | 선택 이유 / 감수한 단점 |
|---|----------|------------|----------|----------|----------------------|
| 1 | 결제 API 10회 중복 요청 | | | | |
| 2 | PG 성공 + DB commit 실패 | | | | |
| 3 | DB commit 직후 서버 다운 | | | | |
| 4 | 이벤트 중복 소비 | | | | |
| 5 | 원장 ↔ PG 정산 불일치 | | | | |
| 6 | 결과 불명(Unknown) 결제 | | | | |
| 7 | PG 지연의 장애 전파 | | | | |

## Load Test Results

| 부하 | PG 지연 | TPS | p99 | 에러율 | 커넥션 풀 포화 | 중복 승인 |
|------|--------|-----|-----|-------|-------------|---------|
| | | | | | | |
| | | | | | | |

## Consistency Checks

| 검증 항목 | 기대값 | 실제값 | 통과 |
|----------|-------|-------|-----|
| 동일 결제 요청의 중복 승인 건수 | 0 | | |
| PG 승인 건수 = 결제 원장 건수 | 일치 | | |
| 처리되지 않고 남은 Outbox 이벤트 | 0 | | |
| 결과 불명 상태로 방치된 결제 | 0 | | |
| 정산 불일치 탐지율 | 100% | | |

## Decisions (ADR)

- ADR-001:
- ADR-002:
