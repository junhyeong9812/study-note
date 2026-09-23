# reliability — 실패가 삼켜지는 곳

실패가 조용히 삼켜지거나, 상태가 원본과 어긋나거나, 자원이 고갈되는 패턴이다.\
공통 원리: **성공 신호·캐시·부분 결과를 산출물 자체로 착각하지 않는다** — 판정 불가는 거부하고, 다단계 변경은 실패해도 복구 가능한 순서로, 정리는 모든 종료 경로에 묶는다.

## 공통 원리

```
  작업 ──▶ 성공 신호 (로그·exit 0·2xx·"완료")
             │
             ├─ 산출물 확인 없음      → silent failure
             ├─ 판정 불가를 통과 처리 → fail-open
             ├─ 절단 결과를 완전한 척 → 조용한 누락
             ├─ 중간 실패 (비원자)    → 반쪽 상태
             └─ 정리 경로 일부 누락   → 누수
                          ▼
          검증 기준 = 신호가 아니라 산출물
```

## 패턴 카드

- [atomic-file-replace](atomic-file-replace/) — 덮어쓰기는 원자적이지 않다 — 같은 파일시스템의 유니크 temp에 완성한 뒤 rename으로 게시하고(디렉토리는 displaced rename+복원), 교체 창의 동시 writer·옛 fd·내구성(fsync)까지 다룬다.
- [change-detection-key-design](change-detection-key-design/) — 변경 감지·캐시 키는 결과에 영향을 주는 입력 전부를 반영해야 하고(mtime·길이·합산값은 불완전), 잠금·정체성 키에는 가변값을 넣지 않는다 — 한쪽이면 갱신 누락, 반대면 무한 루프.
- [cleanup-on-every-exit-path](cleanup-on-every-exit-path/) — 종료 경로가 여럿이면 경로마다 정리를 흩어 두지 말고 스코프 소멸(RAII·try/finally·trap)에 묶어 모든 경로(에러·취소·spawn 실패·예외)에서 정확히 한 번 해제한다.
- [closed-state-model](closed-state-model/) — 상태 공간을 타입·전이 규칙으로 닫아라 — 불법 상태·누락된 조합·종단 재전이·검사 없는 set·비단조 guard는 오보고와 교착을 만든다.
- [debounce-trailing-contract](debounce-trailing-contract/) — 디바운스·보류 전송은 "마지막 변경 뒤 반드시 한 번 더"와 종결 이벤트와의 순서라는 새 계약을 만든다 — 지키지 못하면 마지막 변경이 무음 유실되거나 순서가 뒤집힌다.
- [derived-cache-staleness](derived-cache-staleness/) — 파생 캐시·사본·비동기 로그는 원본보다 늦으며 실패 결과를 캐시하면 일시 장애가 영구화된다 — 완결성·최신성이 필요한 판정은 정본(이벤트 페이로드·원본)을 직접 읽는다.
- [deserialization-trust-boundary](deserialization-trust-boundary/) — 역직렬화 경계에서 타입 보장이 끊긴다 — 영속·외부 데이터는 로드 시 검증·정규화하고, 부분 손상은 격리하되 드롭은 관측하며, 모르는 값·깊이 공격·스키마 진화를 명시 처리한다.
- [edge-detection-on-raw-signals](edge-detection-on-raw-signals/) — 여러 신호를 스칼라로 접거나 매 tick 덮어쓰거나 주기 샘플링하면 사건(edge)이 사라진다 — 기저 신호별 edge 판정·래치·세대 ID·지속 조건으로 감지한다.
- [event-before-subscriber-loss](event-before-subscriber-loss/) — 보관·replay가 없는 이벤트 채널(pub/sub·fire-and-forget)에서는 구독 완료 전·구독자 부재 중 발생한 사건이 영구히 사라진다 — 구독 먼저·backfill·내구성 있는 스트림을 쓴다.
- [fail-closed-guard](fail-closed-guard/) — 안전 판정에서 "모름·조회 실패·설정 누락·default 분기"를 통과로 삼키면 장애가 곧 우회가 된다 — 판정 불가는 거부하고, 허용은 양성 증명(allowlist)으로만 부여하며, 폴백은 특정 오류에만 건다.
- [idempotent-retry-design](idempotent-retry-design/) — 재시도·재처리 가능한 연산은 멱등으로 설계하고(at-least-once+멱등 키), 진행 표지(워터마크)는 전량 성공 후에만 전진시켜 재시도가 자동 복구 루프가 되게 한다.
- [lifecycle-signal-contract](lifecycle-signal-contract/) — 준비·완료·종결 신호는 부수 사건(첫 출력·EOF·started·무활동 시간)에서 추론하지 말고 명시적 계약으로 모든 경로에서 정확히 한 번 보낸다.
- [non-transactional-multi-step](non-transactional-multi-step/) — 트랜잭션 없는 다단계 변경은 순서로 실패를 격리한다 — 새것 확보·성공 확인 뒤에 파괴하고, 실패 가능한 쪽을 먼저 하며, 중간 잔해는 보상·회수한다.
- [process-memory-scope](process-memory-scope/) — 프로세스 메모리 상태(세션 저장소·in-flight future·락)는 재시작·다중 워커·스케일아웃 경계를 넘지 못한다 — 수명·공유 범위가 필요한 상태는 영속·공유 저장소에 둔다.
- [reference-graph-not-text](reference-graph-not-text/) — 삭제·이동 범위는 이름·문자열 치환이 아니라 실제 참조 그래프(컴파일러·빈 이름·FQCN·문자열 참조 전수)로 결정한다.
- [resource-bounding-last-defense](resource-bounding-last-defense/) — 클라이언트 타임아웃·취소는 서버측 작업을 멈추지 못하므로, 외부 입력에 비례해 커지는 자원(메모리·큐·연결·시간)은 서버 쪽 상한이 유일한 방어선이다.
- [retry-policy-design](retry-policy-design/) — 재시도는 실패를 영구/일시로 정확히 분류해야 한다 — 영구 실패·poison 메시지를 재시도하면 무한 루프·아군 차단이 되고, 백오프는 실패 시점 기준이어야 한다.
- [self-feedback-loop](self-feedback-loop/) — 처리기가 자기 입력 공간에 산출물을 남기거나(부산물 재처리), 측정 대상이 측정 결과로 바뀌거나, 브로드캐스트가 보낸 쪽에도 돌아오면 양의 피드백 루프가 생긴다.
- [shutdown-backstop-independence](shutdown-backstop-independence/) — 종료 경로는 정상 정리(unmount·close 이벤트·이벤트 루프)를 보장받지 못한다 — 최후 백스톱은 고장 지점과 독립된 층에 best-effort·비블로킹으로 둔다.
- [sibling-path-invariant-drift](sibling-path-invariant-drift/) — 같은 불변식을 지켜야 하는 형제 경로(분기·setter·오버로드·국가별 복붙·포팅 원본) 중 하나만 가드가 빠지는 비대칭이 결함이 된다 — 형제 전수를 대조한다.
- [silent-failure-vs-artifact](silent-failure-vs-artifact/) — 성공 로그·exit 0·2xx·"완료" 표시는 산출물이 아니다 — 성공은 실제 산출물(저장소·파일·화면·행 수)로 검증해야 한다.
- [silent-truncation-marker](silent-truncation-marker/) — 상한·예산·링버퍼로 자른 결과를 완전한 결과와 같은 모양으로 반환하면 호출자는 절단을 모른다 — 절단 표식을 동반하고, 절단은 표시 경계에서만 하며, 단계 간 상한을 정렬한다.
- [value-binding-time](value-binding-time/) — 값은 해석·고정되는 시점(빌드·import·컨테이너 생성·프로세스 기동·작업 생성)에 박제된다 — 이후 변경은 그 시점을 다시 거치지 않으면 반영되지 않는다.

> 이 폴더의 메타 태그: `silent-failure`(7) · `resource-bounding`(5) · `fail-closed`(1) · `environment-drift`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
