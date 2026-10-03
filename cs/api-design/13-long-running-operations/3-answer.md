# api-design/13-long-running-operations — 정답

## 정답

### 1. 동기 처리 + LB 타임아웃

- 클라이언트: 60초에 LB가 포기하고 `504 Gateway Timeout`을 준다.
- 서버: 연결이 끊긴 줄 모르고 90초까지 일해 리포트를 만든다. 그 결과는 아무도 받지 못한다.
- `504`의 뜻: "게이트웨이가 상류의 응답을 제때 받지 못했다"(RFC 9110 §15.6.5). 작업이 실패했다는 뜻이 **아니다**. 결과 불명이다.
- 그래서 클라이언트가 재시도하면 같은 일이 한 번 더 돈다.

### 2. 시퀀스

```text
  POST /reports  (Idempotency-Key: k1)
    <── 202 Accepted, Location: /operations/7, Retry-After: 2, 본문 {name, done:false}
  GET /operations/7
    <── 200, Retry-After: 2, 본문 {name, done:false, metadata(진행률)}
  GET /operations/7
    <── 200, 본문 {name, done:true, response 또는 error}
```

- 핵심 필드: 작업 ID(name/id), 끝났는지(done 또는 status), 진행 정보(metadata/progress), 결과(response/result) 또는 오류(error).

### 3. 실험

- 동기 두 번: 둘 다 `504`(첫째 약 3.2~3.5초, 둘째 3.0초 — 실행마다 조금 다르다). 서버 집계 `syncReports: 2` — 리포트 두 개, 클라이언트는 하나도 못 받음.
- 비동기: 두 POST 모두 `202 Location=/operations/op-1`(같은 작업). Retry-After 2초 간격으로 폴링, 약 6초 뒤 `done:true, response: r-async-1`. 서버 집계 `asyncReports: 1`.

### 4. 202의 약속

- 약속: 처리를 위해 **받아들였다**.
- 약속하지 않음: 처리가 끝났다는 것, 나중에 실제로 처리된다는 것(처리 시점에 거부될 수도 있다). 그래서 "noncommittal"이다.
- 이유: HTTP 응답은 요청 하나에 하나다. 비동기 작업의 결과가 나올 때 같은 요청에 상태 코드를 다시 보낼 수단이 없다(§15.3.3).
- 그래서 결과는 별도 자원(상태 모니터·작업 자원)에 둔다. 202 응답은 그것을 가리키거나 담는 것이 좋다(RFC 9110의 "ought to").

### 5. AIP vs Azure

| | AIP-151 `Operation` | Azure status monitor |
|---|---|---|
| ID | `name` | `id` |
| 끝났나 | `done` (bool) | `status` 열거(NotStarted·Running·Succeeded·Failed·Canceled) |
| 결과 | `response` (oneof, 모든 LRO가 타입 선언) | `result`(성공한 액션형 LRO에만. 자원 생성·삭제 LRO는 자원 자체가 결과) |
| 오류 | `error` (oneof, google.rpc.Status) | `error` |
| 진행 | `metadata` | 추가 속성 |
| 시작 응답 | `Operation` 반환 | DELETE·POST 액션은 `202` + `operation-location`, PUT은 생성 `201`·교체 `200` + 자원 본문 + `operation-location` |

- "오래 걸린다" 경험칙: 10초.
- 완료 작업 만료 경험칙: 30일(만료는 may). Azure는 끝난 상태 모니터를 문서에 적은 기간(최소 24시간) 남기라고 한다.

### 6. 상태 기계

```text
  PENDING ──> RUNNING ──> SUCCEEDED
     │           ├──────> FAILED
     └───────────┴──────> CANCELED
  끝 상태에서는 움직이지 않는다.
```

```sql
UPDATE operations SET state = 'SUCCEEDED', result = :r, finished_at = now()
WHERE id = :id AND state = 'RUNNING';
```

- 영향받은 행이 0이면 다른 경로(취소·만료)가 먼저 끝냈다.
- 취소와 완료가 동시면 먼저 커밋한 쪽이 이긴다. 다른 쪽 UPDATE는 0행이다. 그래서 취소 응답만으로 최종 상태를 단정할 수 없다.

### 7. Cancel·Wait가 보장하지 않는 것

- `CancelOperation`: 취소 성공을 보장하지 않는다. 지원하지 않으면 `UNIMPLEMENTED`. 성공하면 작업은 지워지지 않고 `error.code = 1`(CANCELLED)로 남는다.
- `WaitOperation`: best-effort. 지정 시간 전에(즉시라도) 돌아올 수 있고, 돌아왔다고 끝났다는 보장이 없다.
- 클라이언트는 `GetOperation`으로 `done`과 `error`/`response`를 확인한다.

### 8. 폴링 폭주

- 원인: 클라이언트가 `Retry-After`를 무시하고 바쁜 루프로 폴링하거나, 서버가 `Retry-After`를 주지 않는다. 작업이 길수록 요청이 선형으로 쌓인다.
- 서버: 작업 종류·진행률에 맞는 `Retry-After`, 조회 API 속도 제한(429 + Retry-After), 완료 웹훅 제공.
- 클라이언트: `Retry-After` 준수, 최소 간격·지터·전체 대기 상한.

### 9. 멈춘 작업

```sql
SELECT id, state, lease_until, now() - created_at AS age FROM operations
WHERE state = 'RUNNING' AND lease_until < now() ORDER BY created_at;
```

- 원인: 워커가 죽었다(배포·OOM·노드 장애). 상태를 끝낼 주체가 없다.
- 막는 법: 임대(`lease_until`)와 하트비트, 만료 스캐너가 재실행하거나 FAILED로 끝내기, 단계별 체크포인트.

### 10. 순번 작업 ID

- 위험: ID를 하나씩 올려 조회하면 남의 작업 상태·결과 링크가 보인다(열거 공격). 소유자 검사가 없으면 바로 유출이다.
- 고치기: 추측 불가능한 ID(UUID 등) + 조회 시 소유자·권한 검사(남의 작업은 404로 존재도 숨김) + 결과 파일은 짧은 수명의 서명 URL.
