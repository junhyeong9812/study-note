# cs/issue/search-engine/cluster-ops-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **flood_stage → read-only 블록, 해제는 수동.**\
디스크 사용률이 flood_stage 워터마크를 넘으면 엔진은 그 노드에 샤드를 가진 인덱스에 `read_only_allow_delete` 블록을 자동으로 건다.\
쓰기는 거부되고 삭제만 허용된다 — 디스크를 더 채우지 못하게 하는 보호 장치다.\
그러나 공간이 회복돼도 블록이 저절로 풀리지 않는 경우가 있어, 인덱스 설정으로 블록을 **명시적으로 해제**해야 했다.\
보호는 "위험 감지 즉시" 자동으로 걸어야 안전하지만, 해제는 "원인이 정말 해소됐나"를 사람이 확인해야 하므로 비대칭이다.\
단일 노드·전용 디스크라는 전제에서는 워터마크(low/high/flood)를 높게 재설정해 조기 발동을 막기도 한다(전제가 깨지면 위험한 선택).
   > **디스크 워터마크** — 노드 디스크 사용률 임계값. low/high는 샤드 배치를 제한하고, flood_stage는 인덱스를 읽기 전용으로 만든다.

2. **단일 노드의 replica는 영구 미할당.**\
replica는 primary와 **같은 노드에 배치될 수 없다**(같은 노드면 노드 장애 시 둘 다 잃으므로 복제의 의미가 없다).\
노드가 하나뿐이면 replica 샤드를 놓을 곳이 영원히 없어 클러스터가 green이 되지 않는다 — 해법은 `number_of_replicas: 0`이다.\
인덱스를 split한 뒤에도 replica=1이 따라오면 같은 이유로 영구 yellow가 된다.\
반면 디스크가 100% 차서 샤드 복구 자체가 `No space left on device`로 실패하면 **primary**가 할당되지 못해 RED가 되고, 그 인덱스를 쓰는 서비스가 unhealthy가 된다 — 이건 설정이 아니라 데이터 경로(디스크)를 되돌려야 풀린다.
   > **yellow / RED** — yellow는 primary는 모두 할당됐고 replica 일부가 미할당, RED는 primary 일부가 미할당(그 샤드의 데이터를 못 읽음).

3. **세그먼트 과다도, 과도 병합도 느리다.**\
refresh마다 작은 세그먼트가 생기고 백그라운드 병합이 이를 합친다.\
병합이 못 따라가 세그먼트가 150여 개(수십 MB~수 GB로 불균형)가 되자, 검색이 세그먼트를 하나씩 순회하는 비용과 병합 작업의 자원 경합이 커져 다중조건 검색이 9초를 넘었다(두 비용 경로는 기록상 가설로 제시된 메커니즘 — 관측은 세그먼트 수·지연뿐).\
그런데 테스트 복제본에서 force merge로 단일 120GB 세그먼트를 만들자 **역효과**가 났다 — force merge는 병합 정책의 `max_merged_segment`(세그먼트 크기 상한)를 따르지 않는다.\
교정은 세그먼트 크기 상한을 정책 기본값(5GB)으로 재지정해 재색인하고, 남은 병목인 정렬을 기본 검색 경로에서 분리한 것이다(정렬은 명시 요청·점수가 의미 있을 때만, 대량 결과는 정렬 차단) → 5~6초가 1.5초로.
   > **세그먼트** — Lucene 인덱스를 구성하는 불변 조각. 검색은 모든 세그먼트를 훑고, 병합은 여러 세그먼트를 하나로 다시 쓴다.

4. **alias와 인덱스는 같은 이름공간.**\
alias 이름으로 이미 실제 인덱스가 존재하면 `invalid_alias_name_exception: an index or data stream exists with the same name as the alias`로 alias 생성이 거부된다.\
이 에러를 `try/except`로 잡아 경고만 남기고 계속하면 마이그레이션은 "성공"으로 끝나지만, 그 이름은 여전히 **옛 실제 인덱스**를 가리킨다 — 새 인덱스로의 전환이 일어나지 않은 채 조용히 넘어간다.\
기록에는 경고 처리까지만 있고 근본 정리(충돌 인덱스 정리)는 남지 않았다 — 이 방식은 임시방편임을 알아야 한다.

5. **라이선스 게이팅과 앱 레벨 RRF.**\
엔진 내장 `rrf` retriever 같은 고급 기능은 라이선스 등급에 묶일 수 있어, basic 등급에서는 하이브리드(벡터 kNN + BM25) 융합을 엔진에 맡길 수 없다는 우려가 있었다(실제 거부 에러는 기록되지 않았다).\
대안은 두 검색을 각각 실행하고 앱에서 문서별로 `1 / (k + rank)`를 누적하는 것이다.\
RRF는 **점수가 아니라 순위**만 쓰므로, 스케일이 전혀 다른 두 점수(코사인 유사도 vs BM25)를 정규화할 필요가 없다.
   > **RRF (Reciprocal Rank Fusion)** — 여러 순위 목록에서 각 문서의 `1/(k+순위)`를 합산해 합친 순위를 만드는 방법. k(보통 60)는 상위 순위의 영향을 완화한다.

6. **없는 설정 = 부팅 거부(fail-closed), 병렬 레버는 샤드 수.**\
해당 빌드에 없는 설정 키(`search.concurrent_segment_search.mode`)를 넣자 노드가 부팅 검증에서 거부해 크래시했다 — 모르는 설정을 무시하지 않고 **기동을 막는** fail-closed 동작이다.\
그 버전에서는 샤드 안의 세그먼트가 직렬로 처리되므로, 검색 병렬성을 올릴 수 있는 레버는 **샤드 수**뿐이었다(데이터 규모별로 샤드 수를 달리 정함).\
부수 교훈: 부하 측정은 도착률을 강제하는 방식(open-loop)이 저용량 인덱스를 과포화시켜 에러로 붕괴했으므로, 동시 사용자 수를 고정한 closed-loop와 엔진 쿼리 카운터 증분으로 쟀다.

7. **모드 전환은 미리 조회해야 보인다.**\
이 함정들은 예외가 아니라 "쓰기 거부·미할당·느려짐·기능 없음"이라는 상태로 나타난다.\
그래서 배포·마이그레이션 전에 클러스터 상태(health), 인덱스 설정의 블록 여부, replica 수 대비 노드 수, 디스크 여유, 세그먼트 분포, 라이선스 등급, 설정 키의 버전 존재 여부를 **먼저 조회**하는 편이 안전하다.\
기록된 부수 함정도 같은 계열이다: 인덱스 split은 하드링크라 빠르지만 삭제 문서 정리(expunge)는 전체 재작성이라 디스크를 크게 쓰고, 색인이 도는 중에 측정 쿼리를 섞으면 수치가 오염된다.

## 문제 구조 (추상화 코드)

### 변형 A — 디스크 워터마크 블록과 단일 노드 replica
① 문제 코드
```http
# 디스크 포화 → 엔진이 자동으로 인덱스에 read_only_allow_delete 블록
PUT /my-index { "settings": { "number_of_replicas": 1 } }   # 노드 1개 → replica 영구 미할당
```
② 고친 코드
```http
PUT _cluster/settings
{ "persistent": { "cluster.routing.allocation.disk.watermark.flood_stage": "99%", ... } }   # 단일 노드·전용 디스크 전제
PUT _all/_settings { "index.blocks.read_only_allow_delete": null }                          # 블록 명시 해제
PUT /my-index/_settings { "number_of_replicas": 0 }
```
무엇이 깨졌나: 보호 블록은 자동으로 걸렸는데 해제는 없었고, replica 배치 규칙상 놓을 노드가 없었다.\
같은 구조: 디스크 100%로 샤드 복구가 `No space left on device` 실패 → primary 미할당 RED → 데이터 경로를 여유 있는 디스크로 되돌려 해소.

### 변형 B — 세그먼트 파편화 vs 과도 병합
① 문제 코드
```http
# 세그먼트 150여 개 불균형 → 검색 지연
POST /my-index/_forcemerge?max_num_segments=1      # 단일 거대 세그먼트 → 역효과 (크기 상한 무시)
```
```python
def search(req):
    return engine.search(query=build(req), sort=default_sort(req))   # 모든 검색에 정렬
```
② 고친 코드
```http
PUT /my-index-v2 { "settings": { "index.merge.policy.max_merged_segment": "5gb" } }   # 상한 재지정 후 재색인
```
```python
def search(req):
    body = {"query": build(req)}
    if req.sort_field and score_is_meaningful(req):   # 정렬은 명시 요청일 때만
        if count(req) > SORT_LIMIT:
            raise TooManyToSort()                     # 대량 결과 정렬 차단
        body["sort"] = sort_for(req)
    return engine.search(**body)
```
무엇이 깨졌나: 세그먼트 수를 줄이는 것만 목표로 삼아 크기 상한을 우회했고, 비싼 정렬이 모든 요청 경로에 붙어 있었다.

### 변형 C — alias와 인덱스의 이름 충돌을 경고로 삼킴
① 문제 코드
```python
try:
    client.indices.put_alias(index=new_index, name=alias)   # 같은 이름의 실제 인덱스가 존재
except Exception as e:
    logger.warning(e)                                        # 전환 실패가 "경고"로 끝남
```
② 고친 코드 (방향)
```python
if client.indices.exists(index=alias) and not client.indices.exists_alias(name=alias):
    raise NameCollision(alias)          # 실제 인덱스가 이름을 점유 → 정리 후 재시도
client.indices.put_alias(index=new_index, name=alias)
```
무엇이 깨졌나: 이름공간 충돌로 전환이 안 됐는데 파이프라인은 성공으로 끝났다(기록상 근본 정리는 남지 않음 — ②는 충돌을 드러내는 방향).

### 변형 D — 기능 게이팅과 설정 검증
① 문제 코드
```python
engine.search(retriever={"rrf": {"retrievers": [knn, bm25]}})   # 라이선스 등급 게이팅 우려
```
```yaml
environment:
  - search.concurrent_segment_search.mode=auto      # 해당 버전에 없는 키 → 부팅 크래시
```
② 고친 코드
```python
fused = defaultdict(float)
for hits in (engine.knn(q), engine.bm25(q)):
    for rank, hit in enumerate(hits):
        fused[hit.id] += 1 / (60 + rank + 1)          # 순위만 사용 → 점수 정규화 불필요
```
```yaml
# 키 제거 · 병렬성은 인덱스별 샤드 수로 조정
```
무엇이 깨졌나: "엔진이 해준다"와 "이 버전·등급에서 된다"를 구분하지 않았다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
