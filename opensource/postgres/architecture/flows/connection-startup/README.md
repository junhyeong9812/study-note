# 연결과 backend 기동

상위: [PostgreSQL 아키텍처 지도](../../README.md)

클라이언트 하나가 TCP 로 붙어서 **첫 `ReadyForQuery` 를 받을 때까지, 그리고 그 뒤 메시지 루프를 돌다 끊길 때까지**의 흐름이다. PostgreSQL 은 연결 하나에 **OS 프로세스 하나**를 붙인다. 이 흐름에는 **프로세스 경계가 딱 한 번** 있다. postmaster 는 `accept` 하고, 자리(PMChild 슬롯)를 잡고, `fork` 하는 데까지만 한다. 시작 패킷을 읽고, 인증하고, 데이터베이스에 붙고, 메시지 루프를 도는 일은 전부 fork 된 자식 backend 가 한다. 흐름은 [07] `PostgresMain` 의 `for (;;)` 루프에서 `'Q'` 메시지를 받으면 [쿼리 실행 파이프라인](../query-pipeline/README.md)으로 넘어가고, 그 일이 끝나면 다시 루프로 돌아와 `ReadyForQuery` 를 보낸다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

```text
 postmaster 프로세스 (모든 연결이 지나는 하나뿐인 입구)
 ------------------------------------------------------------------
 [01] ServerLoop                                   postmaster.c L1653
      +-- WaitEventSetWait                         L1667  리슨 소켓과 latch 를 함께 기다린다
      +-- WL_SOCKET_ACCEPT 이면                    L1698
      |     AcceptConnection -> accept()           L1702  (libpq/pqcomm.c L794)
      |     [02] BackendStartup                    L1703
      |       +-- canAcceptConnections             L3536  서버 상태로 CAC_* 를 정한다
      |       +-- AssignPostmasterChildSlot        L3540  B_BACKEND 풀에서 슬롯 하나
      |       |     없으면 CAC_TOOMANY, AllocDeadEndChild  L3547, L3552
      |       +-- [03] postmaster_child_launch     L3569
      |             +-- fork_process               launch_backend.c L246
      |             부모: pid 를 돌려받아 bn->pid  postmaster.c L3595
      +-- closesocket(s.sock)                      L1708  부모는 클라이언트 소켓을 바로 닫는다
 ------------------------------------------------------------------
                 프로세스 경계 (fork, 자식이 소켓과 startup_data 를 물려받는다)
 ------------------------------------------------------------------
 backend 프로세스 (자식)
 [03] postmaster_child_launch 의 pid == 0 쪽      launch_backend.c L247
      +-- ClosePostmasterPorts, InitPostmasterChild L260, L263
      +-- child_process_kinds[B_BACKEND].main_fn   L290  = BackendMain
 [04] BackendMain                                  backend_startup.c L76
      +-- [05] BackendInitialize                   L110
      |     +-- pq_init                            L177  Port 를 만든다
      |     +-- enable_timeout_after(STARTUP_PACKET_TIMEOUT)  L285  authentication_timeout
      |     +-- ProcessSSLStartup                  L288  첫 바이트 0x16 이면 직접 TLS
      |     +-- [06] ProcessStartupPacket          L295  user, database, 옵션을 Port 에
      |     +-- cac != CAC_OK 이면 여기서 FATAL    L302-L348
      +-- InitProcess                              L116  PGPROC 하나 (max_connections 의 진짜 검사)
      +-- [07] PostgresMain                        L124  postgres.c L4188
            +-- BaseInit                           L4259
            +-- 취소 키 생성                       L4269-L4282
            +-- [08] InitPostgres                  L4293  postinit.c L712
            |     +-- InitProcessPhase2            L730   ProcArray 에 올라 다른 backend 에 보인다
            |     +-- StartTransactionCommand      L847   첫 트랜잭션
            |     +-- [09] PerformAuthentication   L900
            |     |     +-- ClientAuthentication   L253   pg_hba.conf 규칙대로 인증 (libpq/auth.c L379)
            |     +-- 예약 슬롯 검사               L937-L952
            |     +-- GetDatabaseTuple, LockSharedObject  L1012, L1058
            |     +-- CheckMyDatabase, process_startup_options  L1188, L1197
            |     +-- CommitTransactionCommand     L1236
            +-- BackendKeyData 전송                L4332-L4343
            +-- sigsetjmp                          L4397  ERROR 가 되돌아오는 자리
            +-- for (;;)                           L4520
                  ReadyForQuery                    L4687  'Z' (첫 바퀴면 여기서 연결 완료)
                  ReadCommand                      L4702  여기서 다음 메시지를 기다린다
                  switch (firstchar)               L4752
                    'Q'  exec_simple_query         L4770  --> [쿼리 실행 파이프라인]
                    'P' 'B' 'E' 'S' ...            L4778-L4976  확장 질의 프로토콜
                    'X' / EOF  proc_exit(0)        L4983-L5006

 [01] [02] 의 줄은 postmaster/postmaster.c, [03] 은 postmaster/launch_backend.c,
 [04] [05] [06] 은 tcop/backend_startup.c, [07] 은 tcop/postgres.c,
 [08] [09] 는 utils/init/postinit.c 의 줄이다
```

연결 하나가 지나는 문은 셋이다. 셋 다 "몇 개까지 받는가"를 정하지만 세는 대상과 위치가 다르다.

```text
 연결 수를 거르는 세 자리 (기본값: max_connections 100, max_wal_senders 10,
                            superuser_reserved_connections 3, reserved_connections 0)

 1  postmaster   AssignPostmasterChildSlot   pmchild.c L171
       B_BACKEND 풀 크기 = 2 * (max_connections + max_wal_senders)   pmchild.c L100
                         = 2 * (100 + 10) = 220
       비면 CAC_TOOMANY 로 dead-end 자식을 fork 하고,
       그 자식이 시작 패킷을 읽은 뒤 "sorry, too many clients already"  backend_startup.c L340-L343
       2배인 이유: 인증 중이거나 곧 끝날 연결이 있으니 넉넉히 받는다 (pmchild.c L91-L97 주석)

 2  backend      InitProcess                 storage/lmgr/proc.c L436-L458
       freeProcs 리스트 = PGPROC max_connections 개 (proc.c L328)
       비면 FATAL "sorry, too many clients already"
       이것이 max_connections 의 진짜 경계다 (pmchild.c L95-L96 주석)

 3  backend      InitPostgres, 인증 뒤       postinit.c L937-L952
       PGPROC 를 이미 하나 쥔 뒤, 남은 freeProcs 가 3 개 미만이면
       superuser 가 아닌 역할은 FATAL
       기본값이면 일반 역할은 97 번째 연결까지, 98~100 번째는 superuser 몫
```

## 어디에서 쓰이는가

```text
 [쿼리 실행 파이프라인]  PostgresMain 의 'Q' 분기가 exec_simple_query 를 부른다 (postgres.c L4770)
 [커밋]                  InitPostgres 가 StartTransactionCommand / CommitTransactionCommand 로
                         인증과 카탈로그 조회를 트랜잭션 하나로 감싼다 (postinit.c L847, L1236)
 [스트리밍 복제]         시작 패킷의 replication=true 가 am_walsender 를 켜고,
                         같은 루프의 'Q' 가 exec_replication_command 로 간다 (postgres.c L4764-L4767)
 [heavyweight lock]      InitPostgres 가 데이터베이스에 RowExclusiveLock 을 잡는다 (postinit.c L1058)
```

다음 흐름은 [쿼리 실행 파이프라인](../query-pipeline/README.md)이다.

## db-engine 에서는

같은 세 가지 문제(연결 상한, 연결별 상태, 인증)를 db-engine 은 프로세스도 스레드도 연결에 묶지 않고, 세션 객체와 고정 크기 스레드 풀로 풀었다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 실행 단위
   PostgreSQL  연결 1개 = OS 프로세스 1개. postmaster 가 accept 마다 fork 한다
               끝난 backend 는 proc_exit 로 죽는다. 재사용하지 않는다
   db-engine   ConnectionPool(capacity) 이 Executors.newFixedThreadPool(capacity) 를 가진다
               세션과 스레드가 따로 논다. 일은 submit(sessionId) 으로 넘긴다

 상한
   PostgreSQL  postmaster 의 PMChild 슬롯 (2배 여유) -> backend 의 PGPROC freeProcs
               -> 인증 뒤 예약 슬롯 검사. 마지막 자리 몇 개는 superuser 몫
   db-engine   openSession 의 require(sessions.size < capacity) 한 번
               검사와 put 이 원자적이지 않다 (impl 문서가 race 로 적어 둠)

 연결별 상태
   PostgreSQL  Port (소켓, user_name, database_name, guc_options) 와 PGPROC
   db-engine   Session(id, user, currentTxId, ...) 과 ProtocolHandler 의 sessionId 멤버

 인증
   PostgreSQL  ClientAuthentication -> pg_hba.conf 규칙으로 방법을 고른다
               trust, scram-sha-256, md5, password, peer, ident, ldap, cert ...
   db-engine   handleStartup -> AuthManager.authenticate
               사용자 맵 조회 + SHA-256 비교. 인증 전 Query 는 "not authenticated"

 종료
   PostgreSQL  'X' 또는 EOF 면 proc_exit(0). 정리는 on_proc_exit / on_shmem_exit 콜백 몫
   db-engine   handleTerminate -> pool.closeSession. 메시지 없이 끊기는 경우는 과제로 남김
```

db-engine 은 `ProtocolHandler` 가 `Startup` / `Query` / `Terminate` 세 메시지만 받는 작은 상태 기계이고, 인증 여부를 `sessionId` 가 null 인지로 가른다. PostgreSQL 은 인증이 끝나기 전에는 메시지 루프에 들어가지조차 않는다. 인증은 [09] 에서 시작 패킷 직후 한 번 끝나고, 루프는 그 뒤에야 돈다. 챕터: [13-01-connection-pool](../../../../../project/db-engine/13-01-connection-pool/), [14-01-protocol-handler](../../../../../project/db-engine/14-01-protocol-handler/), [15-01-auth](../../../../../project/db-engine/15-01-auth/).

## 단계

1. [ServerLoop](01_ServerLoop/README.md)가 리슨 소켓을 기다리다 연결이 오면 `accept` 하고 [02] 를 부른다.
2. [BackendStartup](02_BackendStartup/README.md)이 서버 상태를 보고 슬롯을 잡은 뒤 자식을 띄운다.
3. [postmaster_child_launch](03_postmaster_child_launch/README.md)가 `fork` 하고, 자식 쪽에서 postmaster 의 흔적을 지운 뒤 `BackendMain` 으로 들어간다.
4. [BackendMain](04_BackendMain/README.md)이 시작 패킷 처리, `PGPROC` 확보, 메시지 루프 진입을 순서대로 부른다.
5. [BackendInitialize](05_BackendInitialize/README.md)가 `Port` 를 만들고 시간 제한 안에서 시작 패킷을 받는다.
6. [ProcessStartupPacket](06_ProcessStartupPacket/README.md)이 SSL/GSS 협상과 취소 요청을 가르고 user, database, 옵션을 꺼낸다.
7. [PostgresMain](07_PostgresMain/README.md)이 세션을 초기화하고 메시지 루프를 돈다.
8. [InitPostgres](08_InitPostgres/README.md)가 `ProcArray` 에 올라가고, 인증하고, 데이터베이스에 붙는다.
9. [PerformAuthentication](09_PerformAuthentication/README.md)이 인증 시간 제한을 걸고 `ClientAuthentication` 을 부른다.

## 결과가 쓰이는 곳

```text
 Port (MyProcPort)
      --> user_name, database_name 이 InitPostgres 의 인자가 된다 (backend_startup.c L124)
      --> guc_options 가 process_startup_options 에서 세션 GUC 가 된다 (postinit.c L1197)
      --> 소켓이 이후 모든 pq_* 송수신의 대상이다

 PGPROC (MyProc)
      --> InitProcessPhase2 로 ProcArray 에 오른다. 스냅샷, 락, 신호가 이 자리로 이 backend 를 찾는다
      --> MyProc->databaseId 가 이 backend 가 붙은 데이터베이스를 알린다 (postinit.c L1130)

 MyDatabaseId, 세션 사용자
      --> 이후 모든 카탈로그 조회와 권한 검사의 기준이다

 취소 키 (MyCancelKey)
      --> BackendKeyData 로 클라이언트에 간다. 클라이언트는 새 연결의 CancelRequest 로 되돌려 보낸다

 PostgresMain 의 메시지 루프
      --> 연결이 끝날 때까지 이 backend 의 모든 일이 이 루프 한 바퀴 단위로 일어난다
```

## 다루지 않는 것

postmaster 의 기동과 상태 기계(`PostmasterMain`, `PostmasterStateMachine`), 자식 종료 처리(`process_pm_child_exit` 와 슬롯 반납), `EXEC_BACKEND`(Windows) 의 `internal_forkexec` 와 `SubPostmasterMain`, TLS 와 GSSAPI 핸드셰이크 내부(`secure_open_server`, `secure_open_gssapi`), 인증 방법별 내부(SCRAM 교환, LDAP, PAM, RADIUS, OAuth), `pg_hba.conf` 파싱(`load_hba`, `hba_getauthmethod`), 취소 요청 처리(`ProcessCancelRequestPacket`), 확장 질의 프로토콜의 각 메시지(`exec_parse_message`, `exec_bind_message`, `exec_execute_message`), 오류 뒤 복구 경로의 `AbortCurrentTransaction` 내부는 이 흐름의 곁가지라 요약만 했다.

## 하위 메서드

- [01 ServerLoop](01_ServerLoop/README.md)
- [02 BackendStartup](02_BackendStartup/README.md)
- [03 postmaster_child_launch](03_postmaster_child_launch/README.md)
- [04 BackendMain](04_BackendMain/README.md)
- [05 BackendInitialize](05_BackendInitialize/README.md)
- [06 ProcessStartupPacket](06_ProcessStartupPacket/README.md)
- [07 PostgresMain](07_PostgresMain/README.md)
- [08 InitPostgres](08_InitPostgres/README.md)
- [09 PerformAuthentication](09_PerformAuthentication/README.md)
