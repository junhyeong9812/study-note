# 클러스터 상태

클러스터의 모든 노드가 **같은 그림을 들고 있게** 하는 장치다. 어떤 인덱스가 있고, 샤드가 어느 노드에 있고, 매핑이 무엇인지가 전부 여기 들어 있다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 ClusterState 의 필드 L170-191 (아홉 개다)

 version              L170  커밋된 상태에 한해 단조 증가한다
 stateUUID            L175  커밋되지 않아도 이 상태를 유일하게 식별한다
 routingTable         L180  어느 샤드 복제본이 어느 노드에 있는가
 nodes                L182  클러스터에 참여한 노드 목록과 역할
 compatibilityVersions L184
 minVersions          L185
 clusterFeatures      L187
 metadata             L189  인덱스 정의, 매핑, 설정
 blocks               L191  읽기/쓰기 차단 표시

 version 의 "단조 증가"에는 단서가 붙어 있다 (javadoc L166-169)
   커밋 없이 만들어져 적용되는 상태가 있다
   no-master 블록을 붙이는 경우가 그렇다
```

```text
 클래스 javadoc 이 구조를 직접 밝힌다 (L81-88)

 "모든 노드가 메모리에 들고 있고, 선출된 마스터가 갱신을 조정한다"
 "개념상 불변이다"
 "Metadata 부분은 갱신마다 디스크에 쓰여 전체 재시작에도 살아남는다"
 "나머지는 메모리에만 있고 전체 재시작 때 초기 상태로 돌아간다.
  다만 모든 노드가 들고 있으므로 마스터 선출은 넘어간다"

 즉 한 덩어리 안에 지속되는 부분과 휘발되는 부분이 함께 있다
```

```text
 발행되는 갱신은 마스터 한 곳에서만 만들어진다

 javadoc L90-93 이 경로를 적어 두었다
   TransportMasterNodeAction 이 요청을 마스터로 보낸다
   MasterService 에 태스크를 제출한다
   큐에 우선순위가 있고, 태스크에 타임아웃을 달 수 있다
   (클라이언트 요청은 대개 단다. 내부 태스크는 무한도 정상 - L94-97)

 버전 번호도 마스터만 정한다
   MasterService L653  "only the master controls the version numbers"
   ClusterState L1175-1179  version + 1

 그래서 "마스터-슬레이브"가 아니라
 "상태를 바꿀 권한이 한 노드에만 있다"가 정확한 표현이다
 데이터 읽기와 쓰기는 마스터를 거치지 않는다
   읽기  TransportSearchAction L437 이 자기 사본을 그대로 쓴다
   쓰기  TransportReplicationAction L999 가 자기 사본에서 프라이머리를 찾는다

 예외가 하나 있다
   마스터를 잃은 노드는 자기 상태에 no-master 블록을 로컬로 붙인다
   (Coordinator L1650-1659) 이때는 버전이 올라가지 않는다
```

```text
 불변이라는 점이 만드는 것

 상태를 바꾼다 = 새 ClusterState 객체를 만든다
 마스터를 거친 갱신이면 version 이 하나 올라간다

 최신 여부는 version 혼자 정하지 않는다
   supersedes  같은 마스터일 때만 version 을 비교한다 (L658-661)
   발행 수신    같은 term 일 때만 version 역행을 거부한다
                (CoordinationState L389)
 즉 (term, version) 쌍으로 본다

 [샤드 모델]의 라우팅 테이블이 이 안에 있으므로
 "어느 노드에 무엇이 있는가"도 이 버전에 묶인다
```

## 실제 코드

무엇을 담는지.

`server` / `org.elasticsearch.cluster` / `ClusterState.java` L170-L191 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/ClusterState.java#L170-L191))

```java
// ClusterState.java L170-L191 (javadoc 생략)
    private final long version;

    private final String stateUUID;

    private final GlobalRoutingTable routingTable;

    private final DiscoveryNodes nodes;

    private final Map<String, CompatibilityVersions> compatibilityVersions;
    private final CompatibilityVersions minVersions;

    private final ClusterFeatures clusterFeatures;

    private final Metadata metadata;

    private final ClusterBlocks blocks;
```

## 어디에서 쓰이는가

```text
 [노드 역할] 각 노드의 역할이 nodes 에 실려 모두에게 보인다
 [샤드 모델] 라우팅 테이블이 프라이머리/레플리카 위치를 정한다
 [디스크 배치] 인덱스 UUID 가 그대로 디렉터리 이름이 된다
 [쓰기 복제] 프라이머리가 누구인지를 이 상태가 정한다
```

노드 쪽은 [노드 역할](../node-roles/README.md), 샤드 배치는 [샤드 모델](../shard-model/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 version
      --> 노드가 자기 상태가 최신인지 판단하는 기준이다
      --> 발행된 새 상태를 받으면 올라간다

 metadata 가 디스크에 쓰인다는 점
      --> 전체 클러스터를 재시작해도 인덱스 정의가 남는다
      --> 반대로 라우팅 테이블은 재시작 후 다시 계산된다
          복원은 metadata 와 version 만 한다 (GatewayMetaState L192-195)
      --> 디스크에 쓰는 것은 마스터 후보와 데이터 노드뿐이다
          (GatewayMetaState L147-206)

 모든 노드가 사본을 든다는 점
      --> 어느 노드로 요청을 보내도 라우팅을 계산할 수 있다
      --> 그래서 어느 노드든 코디네이터가 될 수 있다
      --> "전용 코디네이터 노드"는 별도 역할이 아니라
          역할을 전부 비운 노드다 (DiscoveryNode L464-465)

 blocks
      --> 인덱스가 닫혀 있거나 읽기 전용이면 여기에 표시된다
      --> 요청이 샤드에 닿기 전에 걸러진다
```

## 다루지 않는 것

상태 발행(publication)과 2단계 커밋, `Metadata` 안의 프로젝트/템플릿/ILM 정책 구조, `ClusterBlocks` 의 차단 레벨, 마스터 선출과 정족수, `ClusterStateApplier` 와 `ClusterStateListener` 의 차이, 디프(diff) 기반 전송은 같은 뼈대의 곁가지라 요약만 했다. 상태가 실제로 바뀌고 적용되는 호출 경로는 별도 흐름 문서에서 다룬다.
