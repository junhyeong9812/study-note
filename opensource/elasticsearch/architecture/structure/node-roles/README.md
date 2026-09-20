# 노드 역할

클러스터를 이루는 노드들이 **왜 서로 다른 일을 하는가**. 역할은 설정으로 정해지고, 그 설정이 그 노드가 샤드를 가질 수 있는지, 마스터가 될 수 있는지를 가른다.

기준 커밋: elasticsearch `main` [`60bb239edb`](https://github.com/elastic/elasticsearch/tree/60bb239edb99f0e002eb620e4e82a6f2b15a49b0) (2026-09-19). 모든 줄 번호는 이 커밋 기준이다.

## 전체 그림

```text
 node.roles 설정  -->  DiscoveryNode 가 역할 집합을 들고 있다
                       클러스터 상태에 그대로 실려 다른 노드에도 보인다

 내장 역할 14종 (DiscoveryNodeRole L145-271)

 데이터를 담을 수 있는 역할 (canContainData = true)
   data            d   L145   범용
   data_content    s   L156   내용
   data_hot        h   L167   최근 데이터
   data_warm       w   L178
   data_cold       c   L189
   data_frozen     f   L200
   index           I   L255
   search          S   L266

 데이터를 담지 않는 역할
   master               m   L216   클러스터 상태를 바꿀 자격
   voting_only          v   L221   투표만 하고 마스터는 안 됨
   ingest               i   L211   색인 전 전처리
   remote_cluster_client r  L240   원격 클러스터 연결
   ml                   l   L245
   transform            t   L250
```

```text
 역할 하나가 들고 있는 값은 넷이다 (L30-64)

   roleName              "data", "master" 같은 이름
   roleNameAbbreviation  cat API 에서 쓰는 한 글자
   canContainData        이 노드가 샤드를 가질 수 있는가
   isKnownRole           모르는 역할 이름을 역직렬화할 때만 false 다

 동작으로는 재정의 가능한 훅이 둘 있다

   isEnabledByDefault(Settings)  L72-74  역할을 안 적었을 때 켜지는가
   validateRoles(List)           L82-84  역할 조합이 유효한가
                                         voting_only 가 L228-233 에서 쓴다

 여기까지가 역할 객체의 전부다
 그 역할을 가진 노드에게 무엇을 맡길지는 역할 객체 밖에 흩어져 있다
 (샤드 할당기, 코디네이터 등)
```

```text
 "마스터-슬레이브"가 아니다

 흔히 쓰는 말과 달리 ES 는 노드를 주종으로 나누지 않는다

 master 역할   "마스터로 선출될 자격이 있다"는 뜻이다
               그중 실제로 선출된 하나가 클러스터 상태를 바꾼다
               나머지는 평범한 노드로 계속 일한다

 data 역할     샤드를 가질 수 있다는 뜻이고
               마스터 여부와 무관하다

 한 노드가 두 역할을 함께 가질 수 있다
 작은 클러스터에서는 모든 노드가 master + data 를 겸하는 것이 보통이다
```

```text
 프라이머리와 레플리카는 역할이 아니다

 노드 역할     그 노드가 무엇을 할 수 있는가      (설정)
 샤드 역할     이 샤드 복제본이 주인가 사본인가   (클러스터 상태의 라우팅)

 같은 노드가 어떤 샤드의 프라이머리이면서
 다른 샤드의 레플리카일 수 있다

 그래서 [디스크 배치](../disk-layout/README.md)의 경로에는
 프라이머리인지 레플리카인지가 나타나지 않는다
```

## 실제 코드

역할 하나가 무엇을 들고 있는지.

`server` / `org.elasticsearch.cluster.node` / `DiscoveryNodeRole.java` L30-L64 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/node/DiscoveryNodeRole.java#L30-L64))

```java
// DiscoveryNodeRole.java L30-L64 (javadoc 생략)
    private final String roleName;

    public final String roleName() {
        return roleName;
    }

    private final String roleNameAbbreviation;

    public final String roleNameAbbreviation() {
        return roleNameAbbreviation;
    }

    private final boolean canContainData;

    public final boolean canContainData() {
        return canContainData;
    }

    private final boolean isKnownRole;
```

데이터 역할의 예. `canContainData` 자리에 `true` 가 들어간다.

`server` / `org.elasticsearch.cluster.node` / `DiscoveryNodeRole.java` L142-L151 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/node/DiscoveryNodeRole.java#L142-L151))

```java
// DiscoveryNodeRole.java L142-L151
    /**
     * Represents the role for a data node.
     */
    public static final DiscoveryNodeRole DATA_ROLE = new DiscoveryNodeRole("data", "d", true) {

        @Override
        public boolean isEnabledByDefault(Settings settings) {
            return DiscoveryNode.isStateless(settings) == false;
        }
    };
```

설정에서 역할을 읽어 판정하는 곳이다.

`server` / `org.elasticsearch.cluster.node` / `DiscoveryNode.java` L65-L101 ([GitHub](https://github.com/elastic/elasticsearch/blob/60bb239edb99f0e002eb620e4e82a6f2b15a49b0/server/src/main/java/org/elasticsearch/cluster/node/DiscoveryNode.java#L65-L101))

```java
// DiscoveryNode.java L65-L101 (javadoc 생략)
    public static boolean hasRole(final Settings settings, final DiscoveryNodeRole role) {
        // this method can be called before the o.e.n.NodeRoleSettings.NODE_ROLES_SETTING is initialized
        if (settings.hasValue("node.roles")) {
            return settings.getAsList("node.roles").contains(role.roleName());
        } else {
            return role.isEnabledByDefault(settings);
        }
    }

    public static boolean isMasterNode(final Settings settings) {
        return hasRole(settings, DiscoveryNodeRole.MASTER_ROLE);
    }

    public static boolean hasDataRole(final Settings settings) {
        return hasRole(settings, DiscoveryNodeRole.DATA_ROLE);
    }

    public static boolean canContainData(final Settings settings) {
        return getRolesFromSettings(settings).stream().anyMatch(DiscoveryNodeRole::canContainData);
    }
```

## 어디에서 쓰이는가

```text
 [샤드 모델] 샤드를 어느 노드에 둘지 고를 때 canContainData 를 본다
 [클러스터 상태] master 역할 노드들만 상태 변경에 투표한다
 [디스크 배치] 데이터 역할이 하나도 없는 노드에는 indices/ 아래가 비어 있다
 [REST 진입] 어느 노드로 요청을 보내도 된다. 코디네이터 역할을 한다
```

샤드가 노드에 배치되는 규칙은 [샤드 모델](../shard-model/README.md), 디스크에 놓이는 모양은 [디스크 배치](../disk-layout/README.md)에 있다.

## 결과가 쓰이는 곳

```text
 canContainData
      --> 이 노드에 샤드를 할당할 수 있는지의 첫 관문이다
      --> 역할 집합을 훑어 하나라도 true 면 참이다
          설정 기반 판정은 L99-101, 노드 객체 쪽은 L422-423
      --> 할당은 이것으로 걸러진 노드만 본다
          DiscoveryNodes L878 -> RoutingNodes L134-135

 역할이 클러스터 상태에 실린다는 점
      --> 마스터가 샤드를 배치할 때 각 노드의 역할을 보고 정한다
      --> 노드가 스스로 판단하는 것이 아니다

 한 글자 약어
      --> cat API 응답에서 노드 역할을 표시할 때 쓴다
      --> 대문자 I, S 는 소문자 i, s 와 다른 역할이다 (index/search vs ingest/data_content)

 역할을 지정하지 않은 노드
      --> 각 역할의 isEnabledByDefault 가 기본값을 정한다 (L72-74)
      --> data 역할은 스테이트리스 모드가 아니면 기본으로 켜진다 (L148-150)
```

## 다루지 않는 것

`voting_only` 의 선출 참여 규칙, 데이터 티어(hot/warm/cold/frozen)의 자동 이동 정책(ILM), `index`/`search` 역할이 쓰이는 스테이트리스 구성, 코디네이터 전용 노드 구성, `ml`/`transform` 역할의 작업 배분은 같은 뼈대의 곁가지라 요약만 했다. 실제 마스터 선출 과정도 별도 주제다. 역할 목록은 `DiscoveryNodeRole` 자신의 public static 필드를 리플렉션으로 모아 고정되므로(L298-319) 플러그인이 역할을 추가하는 경로는 없다.
