# spi

상위: [클러스터 상태 갱신](../README.md)

이 흐름의 계약은 둘이다 — 실행기가 지켜야 하는 것(`ClusterStateTaskExecutor`)과 태스크가 기대할 수 있는 것(`ClusterStateTaskListener`). 그리고 후자에 **구멍이 여섯** 있다. 인용은 주석 원문이고, 그 아래 설명은 원문이 이유를 말하지 않을 때 내가 붙인 것이다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 줄 번호는 별도 표기가 없으면 `MasterService.java` 기준이다.

## 실행기가 지켜야 하는 것

```text
 마스터 서비스가 검사하는 것이 셋이다

 1. 버전을 건드리지 말 것            L1246-1253
      versionNumbersPreserved 가 검사한다
      어기면 IllegalStateException - 다만 같은 try 의 catch 가 흡수해
      모든 태스크를 실패시키고 상태를 그대로 돌려준다
      면제: 마스터 선출 (L677-679)

 2. 태스크를 하나도 남기지 말 것      L1208 -> L1212-1223
      ExecutionResult.incomplete() 인 것이 있으면 assert 실패
      success() 넷 또는 onFailure() 중 하나를 반드시 불러야 한다

 3. 응답 헤더를 흘리지 말 것          L1273-1282
      finally 의 assert 가 잡는다
      메시지가 대안까지 적어 준다 -
      TaskContext#captureResponseHeaders 로 태스크 문맥에 옮기거나
      BatchExecutionContext#dropHeadersContext 로 억누르라고

 2번과 3번은 assert 라 -ea 일 때만 돈다
 1번은 실제 코드다
```

```text
 그리고 하나 더 - 마스터를 제거하지 말 것 (L1203-1207)

   throw new AssertionError("update task submitted to MasterService cannot remove master")

 assert 문이 아니라 무조건 던진다
 Error 라서 아래의 catch(Exception) 들이 못 잡는다
```

## 태스크가 받는 것과 못 받는 것

태스크 하나가 도달할 수 있는 종착점이다. 통지가 **없는** 갈래를 굵게 표시했다.

| 종착점 | 어디에서 | 태스크가 받는 것 |
|---|---|---|
| 큐 진입 전 거부 | `submitTask` L1887 | `NotMasterException` |
| 대기 중 타임아웃 | `TaskTimeoutHandler` L1800 | `ProcessClusterEventTimeoutException` |
| 배치 거부(서비스 정지) | `Entry.onRejection` L1935 | `NotMasterException("node closed")` |
| 로컬이 마스터 아님 | L353-354 | `NotMasterException("no longer master")` — **그 자리에서** 알린다 |
| 실행기가 태스크를 실패 표시 | 발행 후 L1111-1113 | 실행기가 준 예외 |
| 실행기가 예외를 던짐 | L1272 를 거쳐 상태 불변 갈래로 | 실행기 예외 |
| 상태 안 바뀜 (정상) | L376 | 성공 소비자 호출 |
| 발행 성공 | L505 | 성공 소비자 호출 |
| 발행 실패 (커밋 실패 / 마스터 아님) | L556 | 그 예외 |
| **서비스가 멈춘 채 배치 진입** | **L341-345** | **없음** |
| **마스터 제거 시도 (AssertionError)** | **L1206** | **없음** |
| **배치 리스너 밖에서 난 예외** | **L1493-1498** | **없음** |
| **완료 포크가 거부됨** | **L565-577** | **없음** (TODO 주석 L577) |
| **그 밖의 발행 실패** | **L578-586** | **없음** |
| **발행 호출이 동기로 던짐** | **L407-411** | **없음** |

```text
 통지가 없는 여섯 갈래의 공통점

 전부 "마스터 서비스 자신이 무너지는 중" 이거나
 "일어나면 안 되는 일" 이다

 L341-345   이미 배치를 꺼낸 뒤 서비스가 멈췄다
            태스크는 taskHolder 에서 빠져 나왔고 타임아웃도 취소됐다
 L1206      실행기가 계약을 깼다
 L1493-1498 마스터 서비스 자기 코드가 터졌다 (assert false 가 붙어 있다)
 L565-577   알릴 스레드가 사라졌다. TODO 가 그것을 인정한다
 L578-586   assert publicationMayFail() - 운영에서는 오면 안 되는 자리다
 L407-411   같은 assert 가 붙어 있다

 즉 정상 운영에서는 L565-577 만 실제로 일어날 수 있는 갈래다
 (주석은 L577 하나뿐이다. 나머지는 assert 의 위치를 보고 내가 판단한 것이다)
```

## ack 리스너는 따로 논다

```text
 ack 리스너가 만들어지는 조건 (L1180-1187)

   실행기가 success(..., ackListener) 로 등록했고
   그리고 그 태스크가 실패하지 않았을 때

 둘 중 하나라도 아니면 null 이고
 L489 의 filter(Objects::nonNull) 가 걸러낸다

 그래서 실패한 태스크는 ack 통지를 아예 안 받는다
```

```text
 ack 가 끝나는 길이 셋이다

 onAckSuccess   상태가 안 바뀌었으면 즉시 (L374)
                또는 모든 노드의 ack 가 모였을 때
 onAckFailure   ack 중 실패가 있었을 때
 onAckTimeout   ack 타임아웃

 발행 자체가 실패하면 ack 리스너는 통지받지 못한다
 (Coordinator 쪽을 읽지 않아 그 경로는 확인하지 못했다)
```

## 우선순위 여섯

`Priority.java` `server` / `org.elasticsearch.common` / `Priority.java` L18-L46 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/common/Priority.java#L18-L46))

| 값 | javadoc 이 말하는 쓰임 |
|---|---|
| `IMMEDIATE` | 실제로는 거의 안 쓴다. 마스터가 다른 태스크에 파묻혔을 때 푸는 용도 |
| `URGENT` | 흔히 쓰는 것 중 가장 높다. 노드 추가나 미할당 샤드 배정처럼 가용성에 영향 있는 것 |
| `HIGH` | `NORMAL` 줄을 앞질러야 할 이유가 뚜렷한 것 |
| `NORMAL` | 나머지 대부분 |
| `LOW` | 배경 작업. 몇 분 걸려도 받아들인다 |
| `LANGUID` | 실제 태스크에 안 쓴다 |

```text
 IMMEDIATE 의 javadoc 이 경고를 담고 있다 (L20-22)

   "The absolute highest priority level. Almost never used in practice. Only
    appropriate for tasks that may be needed to fix a situation in which the master
    is overwhelmed by other tasks with more sensible priorities, e.g. removing a
    node or performing a manual reroute."

 URGENT 도 마찬가지다 (L25-27)
   "It's usually a bad idea to let user-visible APIs directly trigger tasks at
    this level."
```

```text
 LANGUID 는 센티널이다 (L41-42)

   "A sentinel priority level below [#LOW]. Never used for any actual tasks, only
    for `GET _cluster/health?wait_for_tasks=languid` to express a desire to wait
    for all tasks to complete."

 이름에 대한 농담 주석도 붙어 있다 (L44-45)
   "Languid" 는 실재하는 (다만 잘 안 쓰는) 영어 단어이고
   LANGuage + Unique ID 가 아니라고 적어 두었다

 그래도 마스터 서비스는 LANGUID 용 큐를 만들고 매번 순회한다
 언제나 비어 있을 뿐이다
```

```text
 우선순위가 작동하는 시점이 정해져 있다

 takeNextBatch(L1546)가 **다음 배치를 고를 때만** 본다
 고른 배치는 끝까지 돌고, 그 사이 더 높은 것이 들어와도 못 끼어든다

 그래서 긴 배치 하나가 우선순위를 무력화할 수 있다
 StarvationWatcher 가 그것을 재는 장치다
```

## 결과가 쓰이는 곳

```text
 실행기 계약
      --> 39개 실행기가 이 규칙 아래 돈다
      --> 어기면 assert 나 IllegalStateException 으로 드러난다

 태스크 통지
      --> 제출자가 결과를 아는 유일한 길이다
      --> 여섯 갈래에서는 아무 소식도 못 받는다

 우선순위
      --> 큐를 고르는 순서를 정한다
      --> 배치 안의 순서는 정하지 않는다
```

## 다루지 않는 것

`ClusterStateTaskExecutor` 의 나머지 메서드(`clusterStatePublished`, `runOnlyOnMaster`, `describeTasks`)와 `BatchExecutionContext` 의 구성, `ClusterStateAckListener` 의 인터페이스, `TaskAckListener` 의 카운트다운과 타임아웃 예약, `StarvationWatcher` 가 기아를 판정하는 기준, `UnbatchedExecutor`(L708)와 `submitUnbatchedStateUpdateTask`(L700)의 예전 경로는 같은 뼈대의 곁가지라 요약만 했다.
