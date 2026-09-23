# cs/issue/search-engine/document-model-quirks — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 대조·추상화. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **`_id`는 메타필드다.**\
검색 hit는 `{_index, _id, _score, _source}` 구조이고, `_id`는 원본 JSON(`_source`) **바깥**의 메타데이터다.\
`hit["_source"]`만 추출해 넘기면 문서 ID가 사라지고, 하위 코드의 `data.get("_id", "")`는 빈 문자열을 받아 URL을 잘못 만든다.\
다른 경로들은 `_source` 안의 필드를 식별자로 써서 무사했기 때문에, 한 경로에서만 "이미지 누락"이라는 결과 증상으로 드러났다 — 기본값 fallback(`get(..., "")`)이 예외를 삼켰다.\
교정은 `{**hit["_source"], "_id": hit["_id"]}`로 병합해 넘기고, 버그를 재현하는 단위 테스트를 함께 두는 것이다.
   > **메타필드** — `_id`, `_index`, `_score`처럼 엔진이 문서에 붙여 관리하는 필드. 사용자가 색인한 `_source`와 별개다.

2. **`missing`은 null·부재에만.**\
정렬의 `missing` 옵션은 필드가 **없거나 null**인 문서의 위치만 정한다.\
빈 문자열 `""`은 (keyword 정렬에서) "가장 작은 유효 문자열"이라 오름차순 맨 앞에 온다 — 빈 값을 null이 아니라 `""`으로 적재했다면 `missing: _last`는 효과가 없다.\
임시 해결은 2단 정렬(1차: 스크립트로 빈 값=1·값=0, 항상 오름차순 / 2차: 실제 필드를 사용자 방향으로)이지만, 이 스크립트는 매 요청 매칭 문서 전체에서 돌아 비용이 든다.\
근본 해결은 **색인 파이프라인에서 `""` → null 변환 + 재색인**이다 — 표현을 고치는 곳은 쓰기 경로다.

3. **스크립트는 매칭 문서 전부에서 돈다.**\
Painless의 `doc['f'].value`는 그 문서에 값이 없으면 예외를 던진다.\
정렬 스크립트는 결과 집합의 **모든 문서**에서 실행되므로, 값 없는 문서가 단 하나만 섞여도 그 샤드의 검색이 실패한다 — 모든 샤드가 실패하면 `search_phase_execution_exception`으로 요청 전체가 실패하고, 일부 샤드만 실패하면 기본 설정(`allow_partial_search_results: true`)에서는 그 샤드 결과가 빠진 **부분 결과**가 `_shards.failed`와 함께 조용히 반환될 수 있다.\
결과가 클수록 값 없는 문서가 섞일 확률이 커지므로 "결과가 큰 검색어에서만" 재현되고 결과가 작은 검색어는 통과했다 — 극소수의 결함 데이터가, 그것을 포함하는 모든 요청을 깬다.\
교정은 모든 스크립트 첫 줄에 `if (doc[f].size() == 0) return 기본값;` 가드를 두는 것이다.
   > **Painless** — 검색엔진 내장 스크립트 언어. `doc[...]`는 doc_values(컬럼형 저장소)를 읽는다.

4. **`_source` 접근 vs doc_values.**\
`params._source`는 문서마다 저장된 원본 JSON을 읽어 파싱해야 하고, `doc[...]`는 컬럼형 doc_values를 직접 읽는다 — 기록은 전자가 10~100배 느리다고 서술한다(측정값이 아닌 문서 서술).\
정렬 스크립트는 매칭 문서 전체에서 돌기 때문에 수백만 건 대상이면 이 차이가 응답 지연으로 나타난다.\
가장 흔한 해결은 **정렬용 값을 색인 시점에 미리 계산한 필드**(예: 불리언 플래그)로 두고 스크립트 대신 필드 정렬 + `missing: _last`를 쓰는 것이다.

5. **nested는 숨은 문서.**\
nested 타입 필드의 각 원소는 Lucene 수준에서 **별도의 숨은 문서**로 저장된다.\
`_cat/indices`의 `docs.count`는 이 저수준 문서 수라 부모 + 자식의 합이다(최상위 문서 수가 약 10배로 보이고, 작은 표본도 수 배로 보임).\
최상위 건수는 `_count`(match_all)나 `size=0` 검색의 total로 본다.\
진행 중인 색인은 한 시점 스냅샷으로 완료를 판정할 수 없으므로, **기준 원천(원본 DB의 distinct 건수) 대비 비율**과 **시간 간격을 두고 두 번 같은 값(건수 정지)**을 함께 확인해 완료를 확정했다.

6. **같은 `_id`는 last-write-wins.**\
같은 `_id`로의 index 연산은 문서를 통째로 교체하므로(필드 병합이 아님 — 병합은 update API의 partial doc) 처리 순서상 **마지막 문서**가 이긴다. 한 bulk 요청 안에서는 순서대로 처리되지만, 병렬 bulk 요청에 나뉘면 순서가 비결정이다(external 버전을 쓰면 큰 버전이 이긴다).\
한 자연키에 연도별 레코드 여러 개와 이름 없는 stub이 있었고, `_id = 접두어:자연키` 충돌에서 stub이 마지막에 와 정상 문서가 통합 인덱스에서 사라졌다(원천별 인덱스 합 대비 상당수 결손).\
`_id` 생성 규칙을 바꾸면 새 규칙의 문서가 추가될 뿐, **옛 규칙의 `_id` 문서는 지워지지 않고** 고아로 남는다.\
교정: 결손을 "빈 값 + 중복"으로 분해하는 판정식을 먼저 고정 → 읽기 단계에서 자연키로 collapse(필드별 최신 유효값 병합, stub은 최후순위) → `_id`는 자연키(결측 시 대체 키) → 재색인 전 기존 인덱스 삭제 런북(무중단이 필요하면 새 인덱스에 색인 후 alias 전환).

7. **JSON과 갈라지는 지점.**\
식별자는 본문 밖에 있고(메타필드), "값 없음"은 null·부재와 빈 문자열이 다르며(missing), 스크립트는 값의 존재를 가정할 수 없고(doc 부재), nested 배열 원소가 따로 세어지며(숨은 문서), 같은 키로의 index 연산은 병합이 아니라 덮어쓴다(last-write-wins).\
공통점은 모두 **에러가 아니라 틀린 결과**로 나타난다는 것이다 — 그래서 문서 모델의 규칙을 알고 읽기·쓰기 경로에 명시적으로 대응해야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — `_source`만 넘겨 메타필드 `_id` 소실
① 문제 코드
```python
sources = [hit["_source"] for hit in resp["hits"]["hits"]]
# ...
url = build_asset_url(data.get("_id", ""))      # 항상 "" → 에셋 누락
```
② 고친 코드
```python
sources = [{**hit["_source"], "_id": hit["_id"]} for hit in resp["hits"]["hits"]]
```
무엇이 깨졌나: 식별자가 본문 밖에 있다는 걸 모르고 본문만 넘겼고, 기본값 fallback이 결손을 숨겼다.

### 변형 B — 빈 문자열은 `missing` 대상이 아니다
① 문제 코드
```python
sort = [{"name": {"order": order, "missing": "_last"}}]    # "" 문서는 여전히 맨 앞
```
② 고친 코드
```python
# 임시: 1차 스크립트(빈값 뒤로, 항상 ASC) + 2차 실제 필드
empty_last = """
  def v = doc['name'].size() > 0 ? doc['name'].value : '';
  return (v == null || v == '') ? 1 : 0;
"""
sort = [{"_script": {"type": "number", "script": empty_last, "order": "asc"}},
        {"name": {"order": order, "missing": "_last"}}]
# 근본: 색인 파이프라인에서 "" → None 변환 후 재색인 → 스크립트 제거
```
무엇이 깨졌나: "빈 값"을 null이 아닌 값(`""`)으로 적재해 부재 정책이 무력화됐다.

### 변형 C — 값 없는 문서에서 스크립트가 예외 → 요청 전체 실패
① 문제 코드
```painless
String s = doc['status'].value;          // 값 없는 문서 1건이면 예외
if (s == 'ACTIVE') return 1; // ...
```
② 고친 코드
```painless
if (doc['status'].size() == 0) return 99;   // 부재 가드
String s = doc['status'].value;
```
무엇이 깨졌나: 스크립트가 모든 매칭 문서에 값이 있다고 가정했다(샤드 일부만 실패하면 에러 대신 부분 결과로 숨을 수도 있다).\
같은 구조: 정렬 스크립트가 `params._source.items.size() > 0`으로 원문을 파싱 → 수백만 건 정렬에서 지연 → 색인에 이미 있던 불리언 플래그 필드로 `sort(field="has_entries", missing="_last")` 전환.

### 변형 D — nested 숨은 문서가 건수를 부풀림 · 완료 판정
① 문제 코드
```sh
curl -s "$ES/_cat/indices/my-index?h=docs.count"    # 부모 + nested 자식 합
[ "$count" -ge "$expected" ] && echo "done"          # 한 시점 스냅샷으로 완료 판정
```
② 고친 코드
```sh
top=$(curl -s "$ES/my-index/_count" | jq .count)     # 최상위 문서만
sleep 20
top2=$(curl -s "$ES/my-index/_count" | jq .count)
[ "$top" = "$top2" ] && ratio "$top" "$source_distinct"   # 건수 정지 + 원천 대비 비율
```
무엇이 깨졌나: 저수준 문서 수를 비즈니스 문서 수로 읽었고, 진행 중인 값을 완료로 읽었다.

### 변형 E — `_id` 충돌 last-write-wins와 고아 문서
① 문제 코드
```java
Function<Doc, String> idOf = doc -> prefix + ":" + doc.naturalKey();   // 한 키에 여러 레코드 + stub
bulk(stream.map(d -> index(idOf.apply(d), d)));                          // 마지막 도착이 승자
```
② 고친 코드
```java
Function<Doc, String> idOf = doc ->
    doc.naturalKey() == null || doc.naturalKey().isBlank() ? doc.fallbackKey() : doc.naturalKey();
// 읽기 단계: naturalKey keyset으로 묶어 필드별 최신 유효값 병합, stub은 최후순위
Stream<Doc> merged = collapseByNaturalKey(reader, Doc::isPlaceholder);
// 런북: 재색인 전 기존 인덱스 삭제 (옛 규칙 _id 잔존 방지)
```
무엇이 깨졌나: 같은 키로의 쓰기를 병합이라 여겼고, 키 규칙 변경이 옛 키를 지운다고 여겼다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)
