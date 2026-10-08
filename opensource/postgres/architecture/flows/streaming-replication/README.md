# 스트리밍 복제

상위: [PostgreSQL 아키텍처 지도](../../README.md)

standby 가 primary 에 붙어 **WAL 바이트를 그대로 받아 자기 `pg_wal` 에 쓰고, 그 위치를 되돌려 보고하기까지**의 흐름이다. 프로세스가 넷 나온다. standby 쪽은 WAL 을 적용하는 startup, 받아 쓰는 walreceiver 이고, primary 쪽은 보내는 walsender, 그리고 동기 복제라면 커밋 응답을 미루고 기다리는 backend 다. walsender 는 특별한 프로세스가 아니다. 시작 패킷에 `replication=true` 를 단 보통 연결이 같은 `PostgresMain` 루프를 돌다가, `'Q'` 메시지를 SQL 대신 복제 명령으로 처리할 뿐이다. 보내는 범위는 primary 가 **fsync 까지 끝낸 위치**로 묶인다. standby 는 write, flush, apply 세 위치를 보고하고, primary 의 동기 복제는 `synchronous_commit` 단계에 따라 그중 하나(동기 standby 가 여럿이면 FIRST 는 그중 최솟값, ANY 는 n 번째로 큰 값)가 커밋 LSN 이상이 될 때까지 커밋 응답을 붙잡는다.

기준 태그: `REL_18_6` [`724edf9bde`](https://github.com/postgres/postgres/tree/724edf9bde9d356724ad384a2e196edc3c9f80f7). 모든 줄 번호는 이 태그 기준이고, 경로는 따로 적지 않으면 `src/backend/` 아래다.

## 전체 그림

번호는 시간 순서다. standby 의 startup 이 스트리밍을 요청하는 데서 시작해, primary 의 walsender 가 커밋 대기자를 깨우는 데서 끝난다.

```text
 standby                                         primary
 ------------------------------------------      ---------------------------------------------
 startup 프로세스 (redo)
   WaitForWALToBecomeAvailable
     xlogrecovery.c L3906
 [01] RequestXLogStreaming
        walreceiverfuncs.c L246
        WalRcv 에 시작 위치, PMSIGNAL
        -> postmaster 가 walreceiver fork

 walreceiver 프로세스
 [02] WalReceiverMain        walreceiver.c L159
   L281 walrcv_connect  ---- 시작 패킷 ---------> postmaster -> fork -> backend
          replication=true                         ProcessStartupPacket  am_walsender = true
                                                   PostgresMain 'Q' 루프   postgres.c L4764
   L327 IDENTIFY_SYSTEM ------------------------> [03] exec_replication_command  walsender.c L2012
   L462 START_REPLICATION X/X TIMELINE n -------> [03] -> [04] StartReplication   L809
                                                   L943 CopyBothResponse
                         <--------------------    L962 sentPtr = startpoint
                                                   L974 [05] WalSndLoop(XLogSendPhysical)  L2828
   L488 for (;;)                                     for (;;)
                                                       L2859 ProcessRepliesIfAny
                                                       L2877 [06] XLogSendPhysical         L3140
                                                               SendRqstPtr = GetFlushRecPtr L3244
                                                               최대 128KB, 페이지 경계
   L522 walrcv_receive  <-- 'w' dataStart walEnd --        L3422 'w' 를 출력 버퍼에
   L541 [07] XLogWalRcvProcessMsg     L896                 L2882 pq_flush_if_writable
          [08] XLogWalRcvWrite        L967                 L2963 WalSndWait (잠)
               pwrite -> Write 위치
   L560 [10] XLogWalRcvSendReply  -- 'r' write ---->
   L567 [09] XLogWalRcvFlush          L1062
               fsync -> Flush 위치
               WalRcv->flushedUpto
               WakeupRecovery -------+
               [10] SendReply  -- 'r' flush ---->      L2859 ProcessRepliesIfAny
                                     |                   [11] ProcessStandbyReplyMessage  L2445
 startup                              v                     MyWalSnd->write/flush/apply
   flushedUpto 아래를 읽어 redo                             [12] SyncRepReleaseWaiters  syncrep.c L474
   lastReplayedEndRecPtr 를 올린다                               대기 큐에서 꺼내 SetLatch
   (remote_apply 커밋이면 WalRcvForceReply)                         |
   [02] L606 -> [10] -- 'r' apply ------------>                     v
                                                 backend  SyncRepWaitForLSN  syncrep.c L148
                                                          에서 깨어나 COMMIT 응답

 파일을 적지 않은 줄은 standby 쪽이 replication/walreceiver.c, primary 쪽이 replication/walsender.c 다
```

```text
 primary 에서 WAL 위치의 순서 (왼쪽이 작다)

   standby flush  <=  standby write  <=  sentPtr  <=  flush (fsync)  <=  insert 끝
   [09] 가 올림       [08] 가 올림       [06]         XLogFlush          XLogInsert

 각 부등호의 근거
   flush <= write    [09] 는 Flush < Write 일 때만 Flush = Write 로 올린다 (walreceiver.c L1066-L1072)
   write <= sentPtr  standby 는 받은 바이트만 쓰고, walsender 는 메시지를 넣은 뒤 sentPtr = endptr (walsender.c L3424)
   sentPtr <= flush  SendRqstPtr = GetFlushRecPtr (walsender.c L3244), endptr 는 SendRqstPtr 에서 잘린다 (L3329-L3331),
                     시작점이 flush 를 넘으면 START_REPLICATION 이 거절한다 (walsender.c L953)
 예외: 스트리밍을 (다시) 시작한 직후 walreceiver 는 Write = Flush = replay 끝으로 놓고 (walreceiver.c L475)
 첫 보고를 강제로 보낸다 (L484). 받기는 세그먼트 머리부터 다시 하므로 그 잠깐 동안은
 보고된 write, flush 가 sentPtr 보다 클 수 있고, 첫 조각들을 받은 뒤에는 write < flush 일 수 있다 ([08] 참고)

 standby 의 apply 는 startup 이 적용한 끝이다. 스트리밍으로 읽는 동안 startup 은
 flushedUpto 아래만 읽는다 (xlogrecovery.c L3933-L3940)

 sentPtr 가 primary flush 를 넘지 않는 이유 (walsender.c L3234-L3243 주석):
   WALRead 는 쓰인 곳 너머를 못 읽고,
   primary 가 죽었다 살아나면 사라질 WAL 을 standby 가 적용해서는 안 된다
```

동기 복제는 이 흐름의 마지막 두 단계가 커밋 흐름과 만나는 자리다. 커밋하는 backend 는 자기 디스크에 flush 한 다음 큐에 들어가 자고, walsender 가 standby 의 보고를 받을 때마다 큐를 앞에서부터 비운다.

```text
 synchronous_commit 단계별로 primary 커밋이 기다리는 것

 value         local     queue     풀리는 때 (standby 보고 중 무엇이 커밋 LSN 이상이 될 때)
 off           no wait   -         기다리지 않는다. 로컬 flush 도 WAL writer 에 맡긴다
 local         fsync     -         로컬 fsync 만
 remote_write  fsync     WRITE     write  : standby 가 pwrite 한 위치   [08]
 on (default)  fsync     FLUSH     flush  : standby 가 fsync 한 위치    [09]
 remote_apply  fsync     APPLY     apply  : standby 가 redo 한 위치     startup

 큐 선택 assign_synchronous_commit syncrep.c L1124, 대기 SyncRepWaitForLSN syncrep.c L148,
 해제 [12] SyncRepReleaseWaiters syncrep.c L474.
 synchronous_standby_names 가 비어 있으면 on 이어도 기다리지 않는다 (syncrep.c L178-L181)
```

## 어디에서 쓰이는가

```text
 [연결과 backend 기동]  walreceiver 의 연결도 같은 ServerLoop -> BackendStartup -> PostgresMain 을 지난다
                        시작 패킷의 replication=true 가 am_walsender 를 켠다 (tcop/backend_startup.c L790)
                        'Q' 가 exec_replication_command 로 간다 (tcop/postgres.c L4764-L4767)
 [커밋]                 RecordTransactionCommit 이 XLogFlush 뒤 SyncRepWaitForLSN 을 부른다
                        (access/transam/xact.c L1502, L1557)
 [행 쓰기와 WAL 기록]   XLogFlush 가 fsync 뒤 walsender 를 깨운다 (access/transam/xlog.c L2913)
 [WAL redo]             standby 의 startup 이 WaitForWALToBecomeAvailable 에서 [01] 을 부르고,
                        walreceiver 가 flush 한 곳까지 읽어 적용한다 (access/transam/xlogrecovery.c L3906, L3939)
 [체크포인트]           슬롯의 restart_lsn 이 지울 수 있는 WAL 의 하한이 된다 ([11])
                        KeepLogSeg 가 슬롯 최소 LSN 을 읽는다 (access/transam/xlog.c L8008)
```

## db-engine 에서는

같은 문제(primary 의 WAL 을 다른 노드로 옮겨 같은 레코드 열을 만들기)를 db-engine 은 함수 호출 두 번으로 풀었다. 위치 보고, 동기 대기, 연속 스트리밍은 없다.

```text
 같은 문제, 두 구현 (위 PostgreSQL / 아래 db-engine)

 보내는 쪽
   PostgreSQL  walsender 프로세스. sentPtr 부터 primary 가 fsync 한 끝까지
               128KB 씩 바이트 그대로, 연결이 살아 있는 동안 계속
   db-engine   WalSender(primary).stream()
               primary.replay 로 로그 전체를 List<LogRecord> 로 모은다. 언제나 처음부터

 받는 쪽
   PostgreSQL  walreceiver 프로세스. 같은 LSN 자리에 pwrite, 바퀴마다 fsync
   db-engine   WalReceiver(replica).apply(records)
               레코드마다 append, 끝에 sync 한 번

 시작 위치
   PostgreSQL  START_REPLICATION X/X. standby 의 startup 이 정한다 (세그먼트 머리로 내림)
   db-engine   없다. 이미 받은 레코드도 다시 append 된다 (impl 과제 1)

 되돌아오는 보고
   PostgreSQL  'r' 메시지에 write, flush, apply. pg_stat_replication 과 동기 복제의 근거
   db-engine   없다 (impl 과제 2 가 "replica가 자기 상태를 보고하는 방향의 통신"을 요구)

 커밋과의 관계
   PostgreSQL  synchronous_commit 에 따라 backend 가 SyncRepWaitForLSN 에서 기다린다
   db-engine   범위 밖. impl 이 비동기, 동기, 준동기를 표로만 비교

 적용
   PostgreSQL  standby 의 startup 이 계속 redo 하고, 읽기 전용으로 질의를 받는다
   db-engine   replica 의 로그 파일을 나중에 replay 하면 같은 레코드 열이 나온다
```

db-engine 의 `WalSender.stream()` 은 시작점이 없어 매번 처음부터 보내고, impl 문서가 그 중복을 과제 1 로 남겼다. PostgreSQL 에서는 그 시작점이 `START_REPLICATION` 의 LSN 이고, 보고된 flush 위치가 슬롯의 `restart_lsn` 이 되어 다음 연결의 출발점과 WAL 보존의 하한을 함께 정한다. 챕터: [18-01-replication](../../../../../project/db-engine/18-01-replication/).

## 단계

1. [RequestXLogStreaming](01_RequestXLogStreaming/README.md)이 standby 의 startup 에서 시작 위치를 공유 메모리에 적고 postmaster 에 walreceiver 를 띄우게 한다.
2. [WalReceiverMain](02_WalReceiverMain/README.md)이 primary 에 복제 연결을 열고 `START_REPLICATION` 을 보낸 뒤 받기 루프를 돈다.
3. [exec_replication_command](03_exec_replication_command/README.md)가 primary 의 walsender 에서 복제 명령을 파싱해 가른다.
4. [StartReplication](04_StartReplication/README.md)이 타임라인과 시작 위치를 정하고 COPY BOTH 모드로 들어간다.
5. [WalSndLoop](05_WalSndLoop/README.md)가 답장 읽기, 보내기, 잠들기를 되풀이한다.
6. [XLogSendPhysical](06_XLogSendPhysical/README.md)이 flush 된 곳까지 최대 128KB 를 `'w'` 메시지로 만든다.
7. [XLogWalRcvProcessMsg](07_XLogWalRcvProcessMsg/README.md)가 standby 에서 `'w'` 와 `'k'` 를 가른다.
8. [XLogWalRcvWrite](08_XLogWalRcvWrite/README.md)가 WAL 바이트를 같은 LSN 자리에 쓴다.
9. [XLogWalRcvFlush](09_XLogWalRcvFlush/README.md)가 fsync 하고 startup 을 깨운다.
10. [XLogWalRcvSendReply](10_XLogWalRcvSendReply/README.md)가 write, flush, apply 를 primary 로 보고한다.
11. [ProcessStandbyReplyMessage](11_ProcessStandbyReplyMessage/README.md)가 보고를 walsender 의 공유 메모리 칸과 슬롯에 적는다.
12. [SyncRepReleaseWaiters](12_SyncRepReleaseWaiters/README.md)가 동기 standby 들의 위치로 커밋 대기자를 깨운다.

## 결과가 쓰이는 곳

```text
 standby 의 pg_wal 세그먼트와 WalRcv->flushedUpto
      --> [WAL redo] startup 이 XLOG_FROM_STREAM 으로 읽어 적용한다

 MyWalSnd->write, flush, apply, *_lag, state
      --> pg_stat_replication (pg_stat_get_wal_senders, walsender.c L3945)

 WalRcv 의 latestWalEnd, writtenUpto, flushedUpto
      --> pg_stat_wal_receiver (pg_stat_get_wal_receiver, walreceiver.c L1470)

 WalSndCtl->lsn[mode] 와 깨워진 backend
      --> [커밋] 이 COMMIT 응답을 보낸다

 slot->data.restart_lsn
      --> [체크포인트] KeepLogSeg 가 지울 수 있는 WAL 의 하한으로 쓴다 (xlog.c L8008)
```

## 다루지 않는 것

논리 복제(`StartLogicalReplication`, `XLogSendLogical`, 논리 디코딩), `BASE_BACKUP` 과 `pg_basebackup`, 복제 슬롯의 생성과 삭제, hot standby feedback 과 그 xmin, cascade 복제의 세부, 타임라인 전환과 승격(`promote`), 지연 측정 링 버퍼(`LagTracker*`), walsender 종료 순서(`WalSndDone`, `WalSndInitStopping`), libpq 복제 프로토콜 구현(`libpqwalreceiver`)은 이 흐름의 곁가지라 요약만 했다. 연결이 backend 가 되는 길은 [연결과 backend 기동](../connection-startup/README.md), 커밋 쪽 순서는 [커밋](../commit/README.md), standby 의 적용은 [WAL redo](../wal-redo/README.md)에 있다.

## 하위 메서드

- [01 RequestXLogStreaming](01_RequestXLogStreaming/README.md)
- [02 WalReceiverMain](02_WalReceiverMain/README.md)
- [03 exec_replication_command](03_exec_replication_command/README.md)
- [04 StartReplication](04_StartReplication/README.md)
- [05 WalSndLoop](05_WalSndLoop/README.md)
- [06 XLogSendPhysical](06_XLogSendPhysical/README.md)
- [07 XLogWalRcvProcessMsg](07_XLogWalRcvProcessMsg/README.md)
- [08 XLogWalRcvWrite](08_XLogWalRcvWrite/README.md)
- [09 XLogWalRcvFlush](09_XLogWalRcvFlush/README.md)
- [10 XLogWalRcvSendReply](10_XLogWalRcvSendReply/README.md)
- [11 ProcessStandbyReplyMessage](11_ProcessStandbyReplyMessage/README.md)
- [12 SyncRepReleaseWaiters](12_SyncRepReleaseWaiters/README.md)
