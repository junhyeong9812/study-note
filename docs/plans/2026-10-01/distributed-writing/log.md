# log — distributed-writing

| 시각 | 사건 | 결과 |
|------|------|------|
| 2026-10-01 | 인터뷰 4건(영역 분산 · 2차 리뷰 codex, 한도 시 Opus 대체 · 로컬 재현 허용 · 기존 노트 새 leaf 보강) + 추가 요청 "실험으로 데이터 기반 근거" → 명세 I7·V1b → 합의, auto | SPEC=1·MODE=auto |
| 2026-10-01 | 실험 환경 기동·스모크(A1·A1b): etcd 3.6.5 3노드(term 2, 리더 e2) · Kafka 4.1.0 KRaft(토픽 생성·삭제) · Redis 7.4.9(PONG) · Java 21은 temurin 일회용 컨테이너(호스트 java 8) | 브리핑 작성(briefing.md — 새 형식·실험 근거·공용/전용 컨테이너 규칙) |
| 2026-10-01 | 집필 발사(Opus 7병렬, 34편): 01·02·03·04·25 / 05·13·24·26·33 / 06·07·08·09·27 / 10·11·12·28·31 / 14·15·16·20·23·29 / 17·18·21·22·30 / 19·32·34 — 종합 35·36은 후속 · 프롬프트 scratchpad/dist/writer-prompt.md | 회수 대기 |
| 2026-10-01 | 집필 회수 1/7: 19·32·34(3 PASS, 각 9문항, [?] 0) — 실험: 19 상관 ID 없이 FIFO 매칭 오답 85~95/100·경쟁 소비자 순서 역행 320~360/2000·우선순위 기아(aging 137), Kafka 키 파티션·그룹 배정 · 32 Redis lease 에뮬레이션(경쟁 stale 3~4→0, herd 26→1 DB 읽기)·tracking 테이블 상한 무효화 900 · 34 Kafka 2MB 레코드 거부(콘솔 프로듀서 exit 0)·Claim Check 실패가 실제로 dangling 참조 발생·Aggregator 무타임아웃 버퍼 증가 | 전용 컨테이너·토픽·키 정리 확인 |
| 2026-10-01 | 집필 회수 2/7: 05·13·24·26·33(5 PASS, [?] 1 — Fidge 1988 원문 미열람) — 실험 11건: 05 벽시계 인과 역전·벡터 시계 동시성 판정(87k 쌍), 13 Snowflake 시계 역행 재시작 시 2500/2500 중복·worker ID 중복 3000/6000, PG 18.6 일회용 uuidv7 vs v4 B-tree 밀도·단편화 49%, Redis 시퀀스 블록 역순 247/499·JS 정밀도 손실, etcd txn worker ID 선점, 24 LWW 유실·G-Counter·OR-Set, 26 HLC 인과 역전 0·commit wait ε 초과 시 위반, 33 OT tie-break 누락 발산 354/354·Yjs(13.6.33, scratch 설치) 수렴·톰스톤·분수 위치 교차 · 원본 정정 3(13 노드 필드 DC5+worker5 등) · 이탈: postgres:18 이미지 사용(uuidv7 내장 필요, 로컬에 이미 있음) · 커리큘럼 rope 경로 41→실제 28 | 전용 컨테이너·키·lease 정리 확인 · 정합 대기열: curriculum rope 경로 |
| 2026-10-01 | 집필 회수 3/7: 01·02·03·04·25(5 PASS, [?] 1 — RFC 5905 STEPT/PANICT 실제 데몬 기본값) — 실험 9건: 01 타임아웃 없는 HttpClient 무한 대기·Redis 1000 GET vs MGET 23~43배, 02 전용 etcd 3노드 리더 docker pause → 약 1.0초 뒤 재선출 term 4→5·φ accrual vs 고정 타임아웃 오탐 18/86→0, 03 멱등 키 없는 재시도 결제 3회→1회·PING 2만 회 지연 분포로 타임아웃 선택, 04 libfaketime(전용 컨테이너)으로 벽시계 되감기 currentTimeMillis −1991ms vs nanoTime·Cloudflare 음수 srtt 예외 재현·호스트 timedatectl 조회, 25 두 장군 전수 조사·전달 의미론 유실/중복 수 · DDIA는 Vonng 1판 중국어 번역으로 대조 · 03 원본 한 줄 정정 | 전용 컨테이너·키 정리 확인 |
| 2026-10-01 | 집필 회수 4/7: 10·11·12·28·31(5 PASS, [?] 0) — 실험 10건: 10 전용 etcd 리더 kill → 재선출 1.06~1.58s·term+1, 리더 분할 → 두 리더 약 0.36s 겹침·옛 리더 pre-candidate로 term 불변, lease 선출 A 정지 후 B 승계(최소 TTL 2s), 11 정족수 상실 시 put·선형화 get 실패 vs serializable get 옛 값, learner·strict-reconfig, 선거 타임아웃 시뮬(150~150 선출 실패), 12 fencing 없으면 B 쓰기 조용히 유실·있으면 A 거절, Redis DEL 오삭제 vs Lua 소유자 확인, 28 Paxos 규칙 위반 3종 → 두 값 선택, 31 등가 정족수·Nakamoto 표 재계산 일치·몬테카를로 차이(해석 표시) · 출력 일부 잘라 실음(표시함) | 사실 점검 주의: DDIA 절 이름을 원서 미열람·기억으로 인용(10·11·12·28·31) — 대조 필요 |
| 2026-10-01 | 집필 회수 5/7: 06·07·08·09·27(5 PASS, [?] 1 — 27 랙 불균형 배치 추론) — 실험 10건: Redis 리더+복제본(지연 프록시 50ms) 복제본 읽기 stale 300/300·WAIT 후 0, 쿠폰 과발급 1313~1466/300 vs 리더 INCR 300, 3초 지연 페일오버로 확인된 1000건 전부 유실, 다중 리더 LWW 유실 28→82(시계 500ms), 선형화·순차 판정기, etcd 소수 쪽 serializable 읽기 옛 값·쓰기 실패, Redis min-replicas-to-write NOREPLICAS, etcd 선형화 vs serializable 지연, 정족수 시뮬(R+W>N 0%·sloppy 옛 값·Merkle 55 비교), 체인 복제 중간 노드 지연 전파·스트라이프 배치 편중 · 원본 정정(systems/striping Qa−1 등) | 전용 컨테이너 정리 확인 |
| 2026-10-01 | 집필 회수 6/7: 17·18·21·22·30(5 PASS, [?] 0) — 실험: 17 커밋 순서별 유실 15/중복 5·트랜잭션 read_committed 5 vs uncommitted 10·키→파티션 순서, 18 자동 커밋+스레드풀 처리 유실 50·poison 파티션 정지 vs DLT·CommitFailedException, 21 일회용 Kafka 4.1 클러스터(컨트롤러+브로커 3) acks=1 팔로워 pause+리더 kill → 확인된 1000건 유실(Truncating 로그)·acks=all+min.insync=2 유실 0·세그먼트/인덱스 덤프·retention 15s로 미처리 2990건 삭제, 22 PG 17.11 일회용 기대 버전 없을 때 잔액 −400 vs PK 23505·100만 재생 vs 스냅샷·필드 이름 변경 예외/조용한 0, 30 MapReduce 스큐·솔팅·Kafka Streams grace 밖 1건 버림 · 원본 정정(자동 커밋=at-most-once는 처리 분리 시만) | 정리: w17·w18 토픽/그룹 삭제, 공용 Kafka에 내부 토픽 __transaction_state 생성됨(유지), 자기 컨테이너의 익명 볼륨 13개 생성 시각·내용 대조 후 삭제 |
| 2026-10-01 | 사실 점검 브리핑(factcheck-briefing.md — 실험 재실행 의무 V1b, DDIA 인용 대조) · 점검 6묶음 발사(Opus, 집필 묶음과 같은 단위, 집필자와 다른 컨텍스트): 01·05·06·10·17·19 묶음 28편 | 14 묶음(6편)은 집필 회수 후 |
| 2026-10-01 | 사실 점검 회수 1/7: 19·32·34 — 중간 5(19 FIFO 매칭 오답 범위 85~95→80~96·경쟁 소비자 역행 320~360→310~380(재실행 12회), 32 lease 없는 herd 26→26~50(재실행 4/5회가 50 — 노트가 축소), stale 3~4→2~7, 34 Camel completionTimeout은 비활성 타임아웃), 경미 3 · 재실행 8건: 결정적 출력(우선순위 기아·Kafka 파티션·hold-off·tracking 900·Kafka 크기 제한 오류 문구·exit 0) 일치, 무작위 범위는 넓힘 · 미재현 2(34 AggregatorResequencer·Claim Check — 코드 소실, 산술 대조만) · 재부팅 전 재실행 수치는 세션 기록에서 복원 | 3 PASS · 전용 Redis·토픽·키 정리 |
| 2026-10-01 | 사실 점검 회수 2/7: 05·13·24·26·33 — 중간 1(33 클라이언트 ack 대기를 Jupiter로 → Wave의 변경, 5곳), 경미 약 7(05 IR2(b) 원문·89.5%는 이 워크로드 한정, 13 v4 재실행 편차, 26 HLC 48비트는 64비트 NTP 타임스탬프 상위, 33 Figma·Logoot 교차 원인·local-first 출처) · 24 오류 0 · 재실행 12건: 05·13·24·26 결정적 출력 일치(재부팅 전 원본 코드), 33은 코드 소실로 노트 기준 재구성 → 경향 일치·정확한 수치 미검증 · DDIA 장·절 이름 Vonng v1 목차로 대조 일치 · 정합 대기열: 05·13·24·26의 04·08·09 "미작성" 링크 → 실재 | 5 PASS · 전용 PG·키·lease 정리 |
| 2026-10-01 | 사실 점검 회수 3/7: 10·11·12·28·31 — 중간 3(10 리더 두 개 겹침 0.36s 단정 → 재실행 0.30s·겹침 없음(−0.22s)도 있어 범위로, 11 12~24ms 타임아웃이 타이밍 요구 위반이라는 서술 → 논문 §9.3은 그 값에서 평균 35ms 선출, 위반은 더 낮출 때 2곳), 경미 약 6(client-go "arbitrary" 복원, Paxos 절 위치, 31 몬테카를로 z=1 예외·음이항 정확 계산 일치) · 12 오류 0 · 재실행 12건(전용 etcd 재생성 — 재부팅 뒤 e3 DNS 실패): A1·A2·A3·D·C·C2 출력 일치, 시뮬 3종은 원본 소실로 독립 구현 → 판정·경향 일치 · DDIA 장·절 이름 Vonng v1 목차 대조 일치(수정 불요) · 이탈: curlimages/curl 이미지 사용(로컬에 있던 것) | 5 PASS · 전용 컨테이너 정리 |
| 2026-10-01 | 사실 점검 회수 4/7: 01·02·03·04·25 — 중간 5(02 재선출 "약 1.0s=선거 타임아웃" → etcd raft 무작위 [1,2)s·재실행 1.39/1.01s, 03 IETF Idempotency-Key 초안 -07 만료(RFC 아님)·Stripe 저장 조건·mean×2 오탐 4% → 4~8%, 04 RFC 5905 stepout WATCH 900s), 경미 약 8(01 DDIA 그림 8-1은 세 경우만·Joy&Lyon 4개·connectTimeout 문구, 04 smear 최대 0.5s, 25 Gray 쪽수) · 재실행 10건: Fallacies·PhiAccrual(바이트 동일)·etcd pause·faketime·TwoGenerals A 일치, 무작위·지연 값은 범위 넓힘, 3종은 노트 기준 재구성 | 5 PASS · 전용 컨테이너 정리 |
| 2026-10-01 | 사실 점검 회수 5/7: 06·07·08·09·27 — 중간 1(06 WAIT는 유실 확률을 크게 줄이지만 best-effort — 확인된 쓰기도 유실 가능), 경미 약 12(06 GitHub 954건은 자동/연락 분류, 07 쿠폰 과발급 범위 400~1100·리더 0~2, 08 after-* 4회·etcd 지연 범위·NotEnoughReplicasAfterAppend) · 재실행 11건: MultiLeaderLww·LinCheck·failover·partition-redis·quorum-etcd 정확 일치, Redis 프록시·etcd 지연은 경향 일치, Quorum·ChainSim·EtcdLat 재구성 경향 일치(Merkle 55 정확) · 27 원본 정정 줄 원문·BookKeeper 문서 대조 일치 · DDIA 목차 대조 일치 | 5 PASS · 전용 컨테이너 정리 |
| 2026-10-01 | 사실 점검 회수 6/7: 17·18·21·22·30 — **중대 1**(30 늦은 레코드 버림은 "로그 없음" → Kafka Streams 4.1.0은 WARN "Skipping record for expired window" — 집필자는 slf4j NOP로 돌려 못 봄, 재실행으로 확인, 5곳), 중간 3(17 파티션 묶음 소비 순서는 실행마다 다름, 21 소비자 가시성 조건 ISR≥min.insync, 22 Fowler External Queries 원뜻), 경미 약 6(18 리밸런스 직전 자동 커밋, 21 B+Tree 희소 인덱스는 내부 노드, 30 grace 경계 같을 때도 버림 등) · 16 "미작성" 링크 4곳 실재로 · 재실행 9건 일치(17·18 재부팅 전후 2회), 미재실행 4(21 acks=all·retention, 22 100만 재생, 30 MapReduce) | 5 PASS · 전용 클러스터·PG·토픽·그룹 정리 |
| 2026-10-01 | codex 2차 리뷰(high, 3병렬) 사실 점검 완료 28편 발사 — 러너 scratchpad/dist/codex(한도 감지 시 중단 → 남은 편 Opus 적대 리뷰, 명세 V3) | 진행 |
| 2026-10-01 | 집필 회수 7/7: 14·15·16·20·23·29(6 PASS, [?] 3) — 재부팅 뒤 실험 코드 재작성·전부 재실행 후 노트 대조(14 lock timeout 3.1~3.2s 범위화, 15 절대값 보상 +63 반영). 실험: 14 PG 2PC 코디네이터 사망 시 같은 행 쓰기 lock timeout·prepared 재시작 후 잔존·presumed abort 복구·dead tuple 1000 VACUUM 차단, 15 보상 없음 −60/절대값 +63~+100/상대값 0/중복 보상 +60/ID 중복 제거 0, 16 직접 발행 유실 20·outbox 중복 127·릴레이 2개 순서 역전 15·재발행 폭주(터미널 기록에서 옮김)·논리 슬롯 WAL 보유, 20 공유 DB 스키마·권한 오류·API 조합 41 vs 3 호출·뷰 지연 200/200, 23 skip-dup 10건 멈춤·인자 없는 commitSync 버그 PENDING 91, 29 dispatch log 상태 틀림 10→대조 배치 0 · 원본 정정 2(08-saga 절대값 보상, 비관적 뷰 정의) | 전용 컨테이너 정리 확인 · 사실 점검 발사 |
| 2026-10-01 | 판정 회수 26~28(codex 12건): 채택 9·부분 3·기각 0 — 26 HLC Corollary 1은 자기 물리 시계 기준·c 상한 가정·Spanner s ≥ TT.now().latest·CockroachDB read refresh, 27 중간 노드 "논다"→"덜 바쁘다", 28 진행 조건(distinguished proposer)·no-op은 제약 없는 빈칸만·Raft 투표 제한은 투표자별 검사 · 실험 없음 | 3 PASS |
| 2026-10-01 | 판정 회수 19·21·22·24·25(codex 26건): 채택 15·부분 6·기각 0 — 19 Azure 잠긴 메시지 만료 예외·RabbitMQ 만료 경합, 21 멱등 프로듀서는 앱 재전송 중복 못 막음·ELR(ISR→ELR→마지막 리더)·세그먼트 이름은 하한, 22 retention.bytes 기본 −1·compaction은 키별 적어도 마지막 값·PK=기대 버전 검사 조건, 24 Riak allow_mult=false≠LWW·bounded counter, 25 FLP 채널 정의·CT96 ◇W+과반·Ben-Or N>2t · 미확인 2(DDIA 11장, Kafka compaction 설계 원문) | 5 PASS |
| 2026-10-01 | 판정 회수 01~05(codex 14건): 채택 11·부분 3·기각 0 — 02 부분 동기 DLS 두 판·crash-recovery "돌아올 수 있다"·과반 교집합+임기당 한 표, 03 4xx 재시도 분기(408·409·429)·GitHub 2018 원인은 "설정대로 동작한 Orchestrator"(타임아웃 단정 철회, 1-question 8번 문구 수정)·φ accrual은 하트비트용, 04 초기 동기는 즉시 step·node_timex 지표 해석·오차 범위, 05 같은 프로세스 순서·진단 SQL 원인 후보 · 05 "04번 미작성" 링크 실재로 | 5 PASS |
| 2026-10-01 | 판정 회수 06~10(codex 24건): 채택 19·부분 5·기각 0 — 06 Dynamo 동시 판 병합(§4.4)·읽기 복구 §5·RYW 예제 WAIT 수·min-replicas는 거부 조건, 07 etcd serializable 예외·ZooKeeper sync 엄밀 선형화 아님·WFR/MW 세션 밖 영향·쿠폰은 조건부 원자 연산, 08 GitHub 정족수는 제어(리더 선출)·24h11m 구간 분리·결제 C 예 etcd Txn으로, 09 Cassandra Auto Repair 5.0.8 백포트·Unavailable 재시도 정책·힌트 3시간 의미, 10 과반 투표는 term당 리더 하나 · 미확인: Raft §9.3 원문, 09·10 전문 재독 안 함(정합 패스에서 대조) | 5 PASS |
| 2026-10-01 | 판정 회수 11·12·13·17·18(codex 21건): 채택 15·부분 6·기각 0 — 11 커밋은 현재 term 조건·etcd PreVote/CheckQuorum 예외, 12 ZK 레시피 토큰은 czxid·etcd create_revision 재사용·Unlock은 키 고유성으로 안전, 13 UUIDv7 무작위 최대 74비트·블록 카운터 내구성, 17 **인박스 SQL 0행일 때도 UPDATE로 중복 적립**(CTE로 수정, PG 17 실행 확인)·새 그룹 기본 latest(공용 Kafka 실험), 18 정적 멤버 재할당은 세션 타임아웃 뒤·DLT 순서 · 정합 대기열: 17 그룹 실험이 --from-beginning이었는지 미확인 | 5 PASS · a11 컨테이너·토픽 정리 |
| 2026-10-01 | Opus 적대 리뷰 회수 30~34(codex 대체, 노트 수정 없음): 지적 4 — 31 PBFT 진행 가정은 "delay(t)가 t보다 빨리 무한히 커지지 않음"(유계 지연 아님), 30 grace 판정 기호 ≤ → < (본문·소스와 모순), 32·34 이미 있는 노트를 "미작성"으로 · 33 지적 0 · 6.5840 강의 번호·memcache 수치·EIP/Azure/Kafka 기본값 대조 일치 | 판정 발사 |
| 2026-10-01 | 판정 회수 30~34(Opus 지적 4): 채택 4·기각 0 — 30 grace 받는 조건 `<`(KStreamWindowAggregate 4.1.0 소스), 31 PBFT delay(t) 가정 원문대로, 32·34 실재 노트 직접 링크 | 5 PASS |
| 2026-10-01 | 종합 35·36 집필 발사(Opus) — 35 역색인(34편 장애 절 전수), 36 GitHub 2018·Cloudflare 2017 윤초·AWS EBS 2011·metastable failure 원문 대조, database/57과 모순 금지 · 실험 의무 면제(I7 예외) | 회수 대기 |
| 2026-10-01 | 종합 35·36 회수(2 PASS, [?] 0) — 35: 장애 시나리오 156개 전부 링크(스크립트 대조)·오독 사전 19행·메시지 원문 소스 대조(etcd·raft·Kafka 4.1·Cassandra 드라이버·PG 17·Redis 7.4), 대사 SQL·SymptomGuard 실행 확인 · 36: GitHub 2018·Cloudflare 2017·AWS 2011·Bronson HotOS21·Huang OSDI22 원문 대조, database/57과 수치 불일치 0, metastable 유체 모델(Node, 결정적 — 자체 모델 명시) · 이탈: alpine:latest pull 후 삭제 · 정합 대기열 추가: 26 "04번 미작성", 02 etcd 제거 문구(문서 vs 소스), 04 "most affected machines", 18 CommitFailedException 줄인 인용, **database/57의 "distributed 36(미작성)" 2곳 — DB 영역이라 이 작업 금지영역(읽기만), NEXT로** | 사실 점검 발사 |
| 2026-10-01 | 사용자 지시("진행하고"): DB 브랜치 main fast-forward + push(f3ae23b5..69df46fb — 사용자 커밋 d8b9653b·5c741169 포함) · 명세대로 docs/distributed-writing 브랜치 생성(main 69df46fb) | DB push 기록은 이 log에 남김(db log 커밋 후 발생) |
| 2026-10-01 | 사실 점검 회수 7/7: 14·15·16·20·23·29 — **중대 1**(15 절대값 보상 출력 +94/+100은 out 파일에 없고 5회 재실행 +56~+63 → 실제 출력으로 교체), 중간 3(14 KIP-939: kafka-clients 4.1.0에 prepare/complete API 없어 2PC 참가 불가 — [?] 해소, 15 좌석 예는 논문 1절, 16 CDC 출력 3007kB → out·재실행 2548kB), 경미 약 6 · 터미널 기록에서 옮긴 출력 2건(16 재발행 폭주·20 nodelay 없음) **재현 일치** · 23·29 수정 0 · DDIA 9장 Vonng v1 대조 일치 | 6 PASS · f14 컨테이너 정리 |
| 2026-10-01 | 사실 점검 회수(종합): 35·36 — 35 오류 0(약 190 링크·에러 문구 소스 전수 대조), 36 경미 2(EBS 원문 문장 대상, RDS 분할 문구) · 재실행: retry-meta.js 바이트 동일(결정적)·SymptomGuard·recon.sql·etcd/Kafka 명령 일치 · database/57과 일치 | 2 PASS |
| 2026-10-01 | Opus 적대 리뷰 회수 14·15·16·20·23·29·35·36(codex 대체): 지적 1(16 CDC 그림 — 슬롯이 WAL을 붙잡는 경계는 restart_lsn, confirmed_flush 아님), 7편 no findings(35 링크·에러 문구·36 시각·수치 원문 대조 일치) · 판정: 메인이 PG 17 pg_replication_slots 문서 직접 확인 → 채택, 그림 한 줄 수정 | 16 PASS |
| 2026-10-01 | 정합 패스 발사(Opus): 대기열 8항목(낡은 미작성 링크 전수, 02 etcd 제거 문구 문서 vs 소스, 04 most affected machines, 18 CommitFailedException 인용, 17 그룹 실험 시작 방식(필요시 재실행), 09·10 전문 재독, 노트 간 공통 사실(Kafka 기본값·etcd 타이밍·GitHub 2018·HLC·CDC 슬롯·2PC/사가), 영역 밖 후속(database/57 미작성 2곳·커리큘럼 rope 경로)은 보고만) | 회수 대기 |
| 2026-10-01 | 정합 패스 회수: 링크 12곳 실재로(남은 미작성 6은 실제 부재), 02 etcd 제거 문구 문서 예시 vs 3.6.5 실제 JSON 로그 분리(일회용 etcd 재현, exit 1), 04 "가장 영향이 큰 머신", 18 인용 표시·rebalance 경로 문구, 17 그룹 실험 재실행(--from-beginning 15건 vs 기본값 0건, 명령 명시), 09 첫 문장 모순 해소, 10 inLease는 CheckQuorum 시만, 08 ELR 단서(21과 정합) · Kafka·etcd·GitHub 2018·HLC·CDC·2PC 공통 사실 일치 · 영역 밖 후속(NEXT): database/57 212·348행 미작성 → 36 링크, curriculum §10·데이터 구조 표 rope 41→28, distributed/03의 reliability 07·08 링크는 신뢰성 작업 후 재점검 | 36 PASS · 링크 856 깨짐 0 |
| 2026-10-02 | 사용자 승인 → main fast-forward + push(69df46fb..d2733634 — 이 세션의 다른 실행이 남긴 후속 소정정 커밋 d2733634 포함) | |
| 2026-10-02 | 후속 소정정 5곳(재부팅 뒤 이 세션의 다른 실행이 분산을 커밋한 뒤 돌린 판정 재확인에서): 06 Dynamo 장바구니 절 §6·충돌 판 "고르거나 합치게"·근거 목록, 09 근거 줄, 13 표 "재시작 시 남은 구간 공백"(본문과 모순 해소), 18 DLT 뒤 키 순서 단서(정답과 모순 해소), 22 핵심 문장 정본 구성 한정(Fowler) | 커밋 |
| 2026-10-01 13:15 | 세션 재시작 후 상태 확인: 34편 존재·34 PASS · codex 2차 리뷰 22편 완료(01~13·17~19·21·22·24~28), 30·31에서 한도(리셋 17:07) · 14 묶음 집필 작업자 미회수(파일 6편은 12:46~12:55 작성·PASS) → 재개 · 명세 V3대로 남은 30~34는 Opus 적대 리뷰 발사 · 판정 브리핑 adjudicate-briefing.md(DB판 이식) + 판정 5묶음 발사(01~05·06~10·11~13·17·18·19·21·22·24·25·26~28) | 14 묶음은 사실 점검 → Opus 리뷰 순서로 후속 |
| 2026-10-01 12:05 | **재부팅**: /tmp 소실 — 집필자 실험 코드·출력(scratchpad/dist/*)과 점검 산출물 사라짐, 노트 본문·수정은 저장소에 있어 보존 · 컨테이너 전부 정지 → 공용·전용 재기동(etcd health·Redis·Kafka 확인), bind mount가 root 소유로 다시 만든 dist/14 소유권 정리 · 프롬프트 재작성 · 작업자 7개 SendMessage 재개(실험 코드는 노트의 코드로 재구성, 재구성 여부를 packet에 표시) | V1b 영향: 실험 출력 원본(out 파일) 대조 불가 → 재실행 결과와 노트 출력 대조로 대체 |

## 리뷰 ledger

| 대상 | 리뷰어 | 중대 | 중간 | 경미 | [?] 전→후 | 비고 |
|---|---|---|---|---|---|---|
| 19·32·34 | Opus 독립 | 0 | 5 | 3 | 0→0 | 웹 표본 9 · 실험 재실행 8 |
| 05·13·24·26·33 | Opus 독립 | 0 | 1 | ~7 | 1→1 | 웹 표본 16 · 실험 재실행 12(33 재구성) |
| 10·11·12·28·31 | Opus 독립 | 0 | 3 | ~6 | 0→0 | 웹 표본 15 · 실험 재실행 12(시뮬 3 독립 구현) |
| 01·02·03·04·25 | Opus 독립 | 0 | 5 | ~8 | 1→1 | 웹 표본 15 · 실험 재실행 10(3종 재구성) |
| 06·07·08·09·27 | Opus 독립 | 0 | 1 | ~12 | 1→1 | 웹 표본 15 · 실험 재실행 11(3종 재구성) |
| 17·18·21·22·30 | Opus 독립 | 1 | 3 | ~6 | 0→0 | 웹 표본 16 · 실험 재실행 9 |
| 26~28 판정 | Opus(codex 지적 12) | 채택 9 | 부분 3 | 기각 0 | | |
| 19·21·22·24·25 판정 | Opus(codex 지적 26) | 채택 15 | 부분 6 | 기각 0 | | |
| 01~05 판정 | Opus(codex 지적 14) | 채택 11 | 부분 3 | 기각 0 | | |
| 06~10 판정 | Opus(codex 지적 24) | 채택 19 | 부분 5 | 기각 0 | | |
| 11~13·17·18 판정 | Opus(codex 지적 21) | 채택 15 | 부분 6 | 기각 0 | | |
| 30~34 판정 | Opus(Opus 적대 리뷰 지적 4) | 채택 4 | 부분 0 | 기각 0 | | codex 한도로 Opus 대체 |
| 14·15·16·20·23·29 | Opus 독립 | 1 | 3 | ~6 | 4→2 | 웹 표본 18 · 실험 재실행 12 |
| 35·36 | Opus 독립 | 0 | 0 | 2 | 0→0 | 웹 표본 6 · 실험 재실행 6 |
| 14 묶음·35·36 판정 | 메인(Opus 지적 1) | 채택 1 | 부분 0 | 기각 0 | | codex 한도로 Opus 대체 |

## 생략한 검증

- V1b 일부: 재부팅(12:05)으로 집필자 실험 원본(out 파일·코드) 소실 → 출력 원본 대조 대신 노트 코드로 재구성·재실행해 노트 출력과 대조. 재구성 실험(33 일부·10 시뮬 3종·01/06 각 3종)은 경향 일치까지만 확인.
- V3 일부: codex는 22편, 나머지 14편은 명세대로 Opus 적대 리뷰로 대체(한도 리셋 17:07 대기 안 함).
- 컨테이너 정리: 공용 sn-dw-* 컨테이너·네트워크 삭제. 공용 Redis 등이 만든 익명 볼륨은 소유 판별이 불확실해(같은 시각대 다른 작업 볼륨 다수) 지우지 않음 — 다음 정리 때 생성 시각·내용으로 판별.

## 완료 요약

- **산출**: `cs/distributed/01~36` 36편(신규 19·보강 17, 각 4파일) + 영역 표 재생성(초안 36) · 커밋 48b4b4dc.
- **파이프라인**: Opus 집필 ×8(+종합 1, 재부팅 후 재개 1) → Opus 사실 점검+실험 재실행 ×8 → codex high 22 + Opus 대체 리뷰 14 → 판정 ×7(+메인 1) → 정합 패스 → 웹 교차 38.
- **수치**: 1차 점검 중대 2(30 Kafka Streams 늦은 레코드는 WARN 로그 남김, 15 재현 불가 출력 교체)·중간 약 22 · 2차 지적 약 102건 → 채택 74·부분 28·기각 0 · 정합 정정 약 20(링크 12) · 웹 38/38 · check 36 PASS · 링크 892 깨짐 0.
- **실험 근거(사용자 요청 I7)**: 편당 1~5개, etcd 3노드 리더 kill·분할, Kafka acks/ISR 유실, PG 2PC 블로킹, Redis 복제 지연·lease, HLC·CRDT·Paxos 시뮬 등 — 출력은 실행 결과만.
- **사고**: 재부팅으로 /tmp 소실(외부 요인) — 실험 원본 재구성.
- **CS 이슈 아카이브**: 0건 — 사건형 문제 없음(발견 사실은 노트 본문에 반영, 재부팅·codex 한도는 도구 사정).
