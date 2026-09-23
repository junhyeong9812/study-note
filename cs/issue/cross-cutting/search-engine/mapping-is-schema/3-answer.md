# cs/issue/search-engine/mapping-is-schema — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **역색인은 색인 시점의 분석 결과다.**\
역색인의 토큰은 문서가 들어올 때 그 시점의 분석기로 **한 번** 계산되어 저장된다.\
분석기를 바꾸면 이미 저장된 토큰과 새 분석 규칙이 섞여 같은 필드 안에서 의미가 달라지므로, 엔진은 기존 필드의 분석기 변경을 `PUT _mapping`에서 거부한다.\
multi-field 서브필드도 추가만 되고 제자리 제거는 안 되어, 쿼리에서 안 쓰게 된 서브필드가 다음 전체 마이그레이션까지 디스크를 차지한다.\
플러그인 코드를 고쳐 재배포해도 기존 문서는 다시 분석되지 않아 옛 토큰이 남는다 — 그래서 분석기 출력을 바꾸는 패치마다 배포 절차에 "재색인 필수"를 명시했다(플러그인 교체 → 재시작 → 재색인 → `_analyze`로 토큰 확인).
   > **역색인(inverted index)** — 토큰 → 그 토큰을 가진 문서 목록의 사전. 검색은 이 사전을 조회한다.

2. **새 인덱스 → 재색인 → alias 스왑.**\
새 인덱스는 신 매핑을 처음부터 적용받고, 재색인은 모든 문서를 신 분석기로 다시 토큰화하며, 누락 보강(빠진 문서 탐색 → 추가 이관)과 표본 `_source` 검증 뒤 alias를 새 인덱스로 옮겨 **읽는 쪽 코드 변경 없이** 원자적으로 전환한다.\
옛 인덱스를 1~2주 남기는 것은 **롤백 수단**이다 — alias만 되돌리면 즉시 이전 상태로 복귀한다.\
대가는 규모다: 수억 건 인덱스면 재색인에 수 시간~수일, 디스크도 일시적으로 두 벌이 필요하다.
   > **alias** — 하나 이상의 인덱스를 가리키는 별칭. 클라이언트는 alias로만 접근하고, 뒤의 실제 인덱스는 교체할 수 있다.

3. **"없으면 생성"이면 먼저 만든 쪽이 이긴다.**\
매핑 정의가 초기화 JSON과 앱 문서 클래스 두 곳에 있으면, 한쪽만 고쳐지는 순간 둘이 어긋난다(분석기 서브필드 분리를 문서 클래스에만 적용 → 운영 인덱스는 옛 매핑 → 한 인덱스의 색인이 19배 느려짐).\
부트스트랩이 "인덱스가 있으면 생성·매핑 변경을 스킵"하므로 **실제 적용 매핑은 누가 먼저 만들었나**로 결정되고, 재색인해도 옛 매핑과 옛 `_id`가 그대로 남는다.\
앱이 먼저 인덱스를 자동 생성하면 앱의 필드 어노테이션만으로 매핑이 만들어져 JSON에만 정의된 **분석기 서브필드가 누락**된다.\
교정: 운영 정본을 JSON 하나로 명문화하고, 앱 문서 클래스도 같은 JSON 파일을 매핑 소스로 참조하며, 인덱스를 지운 뒤엔 앱이 쓰기 전에 **JSON으로 먼저 재생성**한다.

4. **포맷 밖 값 하나가 bulk를 깨고, 동적 매핑은 첫 값으로 정한다.**\
엄격 타입 매핑은 파싱할 수 없는 값을 문서 단위로 거부한다 — 구분자 없는 `20240115`가 선언 포맷과 달라 `failed to parse field ... of type [date]` 400이 났고, 첫 bulk부터 전량 거부되어 처리 0건으로 작업이 실패했다.\
명시 매핑이 없는 파생 필드는 동적 매핑의 date detection이 **첫 값**을 보고 date로 정해버려, 이후 형식이 다른 값이 거부된다(워커가 예외를 삼키면 조용한 유실 위험).\
원문 보존이 목적이면 날짜를 keyword(원문 문자열)로 저장하고 `"date_detection": false`로 자동 감지를 끄는 것이 안전하다 — 직렬화 쪽도 날짜 리스트를 문자열 리스트로 바꿔 복합 객체 오색인과 경고 폭주를 없앴다.
   > **동적 매핑(dynamic mapping)** — 매핑에 없는 필드가 들어오면 첫 값의 모양을 보고 타입을 자동으로 정해 매핑에 추가하는 동작.

5. **`dynamic: strict`.**\
필드가 문서에 **없는 것**은 허용하지만, 매핑에 **없는 필드를 쓰는 것**은 문서 단위로 거부한다.\
코드가 필드 구조를 바꿔(예: 한 필드를 두 언어 필드로 분리) 새 필드를 쓰기 시작했는데 인덱스가 옛 매핑이면 **전 문서가 거부**된다 — 매핑은 코드와 같은 버전이어야 한다.

6. **가드는 모든 호출부가 전파할 때만 가드다.**\
`_meta.schema_version`과 코드 상수 비교는 불일치를 기동·재색인 시점에 잡는 fail-fast 장치로, 불일치면 러너를 중단시켜 운영자가 삭제·재생성하게 강제한다(경고 → 예외로 격상).\
하지만 한 경로의 인덱스 준비 함수가 예외를 전부 삼키고 있어, 그 경로에서는 가드가 **없는 것과 같았다**.\
교정은 삼키던 예외를 재전파하고 **모든 호출부**를 일관성 점검하는 것, 그리고 매핑 사본 두 벌(앱 리소스·초기화 디렉터리)이 byte 동일한지 계약 테스트로 강제하는 것이다.

7. **정의 묶음의 버전 분리 → "정의는 있는데 구현이 없음".**\
매핑은 settings의 분석기 이름을, settings는 플러그인이 제공하는 필터 이름을, 빌드 파일은 플러그인 zip 파일명을 참조한다.\
이것들이 따로 관리되면 한쪽만 바뀌어 `analyzer [...] has not been configured`, 필터가 없는 구버전 플러그인, 파일명 불일치, 운영 서버가 구버전 빌드로 남는 상태가 생긴다.\
기본 방안(정의 단일화 + 재색인)이 **한 인덱스의 매핑 정본**을 하나로 만드는 것이라면, 이것은 **매핑·settings·플러그인·빌드를 한 묶음**으로 함께 버전 관리하는 더 넓은 층위의 해결이다(아래 방안 비교).

## 문제 구조 (추상화 코드)

### 변형 A — 제자리 변경 불가 → 새 인덱스 + 재색인 + alias 스왑
① 문제 코드
```http
PUT /items/_mapping
{ "properties": { "name": { "type": "text", "analyzer": "new_analyzer" } } }   # 기존 필드 → 거부
# 또는: 분석기 플러그인만 교체·재시작 → 기존 문서 토큰은 옛 그대로
```
② 고친 코드
```http
PUT /items_v2 { "settings": {...}, "mappings": {...신 매핑...} }
POST _reindex { "source": { "index": "items_v1" }, "dest": { "index": "items_v2" } }
# 누락 보강 + 표본 _source · _analyze 토큰 검증
POST _aliases { "actions": [
  { "remove": { "index": "items_v1", "alias": "items" } },
  { "add":    { "index": "items_v2", "alias": "items" } } ] }
# items_v1은 롤백용으로 1~2주 유지
```
무엇이 깨졌나: 저장된 토큰이 색인 시점에 굳는다는 걸 무시하고 정의만 바꾸면 반영된다고 여겼다.

### 변형 B — 정의가 둘 · "없으면 생성" 부트스트랩
① 문제 코드
```java
@Document(indexName = "items", createIndex = true)       // 앱이 먼저 만들면 분석기 서브필드 누락
class ItemDoc { @Field(type = Nested) List<Part> parts; }
// 별도: init/items.json (분석기 서브필드 포함) — 한쪽만 수정됨
```
```sh
curl -sf "$ES/items" >/dev/null || curl -XPUT "$ES/items" -d @init/items.json   # 있으면 스킵
```
② 고친 코드
```java
@Document(indexName = "items", createIndex = false)
@Mapping(mappingPath = "mappings/items.json")             // 정본 JSON 하나를 양쪽이 참조
class ItemDoc { ... }
```
```sh
# 매핑 변경 = 인덱스 DELETE → 정본 JSON으로 PUT → 재색인 (앱 쓰기보다 먼저)
```
무엇이 깨졌나: 정본이 둘이었고, 부트스트랩이 기존 인덱스의 드리프트를 조용히 방치했다.\
같은 구조: 색인 경로가 채우는 필드와 검색 어댑터가 질의하는 필드가 파이프라인마다 따로 구현돼, 한 경로가 검색 대상 필드를 채우지 않음 → 그 경로의 이름 검색 0건 → 채우는 쪽을 수정.

### 변형 C — 엄격 타입 거부 · 동적 date detection
① 문제 코드
```json
{ "properties": { "created_at": { "type": "date", "format": "yyyy.MM.dd||yyyy-MM-dd" } } }
// 원천에 "20240115" → 문서 거부 → bulk 전량 400
// 매핑에 없는 파생 날짜 필드 → date detection이 첫 값으로 date 고정 → 이후 값 거부
```
② 고친 코드
```json
{ "date_detection": false,
  "properties": { "created_at": { "type": "keyword" } } }   // 원문 문자열 보존
```
```java
List<String> derivedDates;   // 날짜 객체 리스트 대신 원문 문자열 리스트
```
무엇이 깨졌나: 원천 데이터의 형식 분포를 확인하지 않고 강한 타입을 걸었고, 매핑 밖 필드의 타입을 엔진의 추측에 맡겼다.

### 변형 D — `dynamic: strict` + 스키마 버전 가드 + 예외 삼킴
① 문제 코드
```java
void ensureIndex() {
    try {
        checkSchemaVersion();              // 불일치면 throw 하도록 만든 가드
    } catch (Exception e) {
        log.warn("ensure index failed", e);   // 한 경로가 전부 삼킴 → 가드 무력
    }
}
```
② 고친 코드
```java
void checkSchemaVersion() {
    Map<String, JsonData> meta = client.indices().getMapping(...).meta();
    String actual = meta == null || !meta.containsKey("schema_version") ? null
                  : meta.get("schema_version").to(String.class);
    if (!SCHEMA_VERSION.equals(actual))
        throw new IllegalStateException("stale schema_version=" + actual + " — delete & re-create before reindex");
}
void ensureIndex() { checkSchemaVersion(); /* 예외는 전파 → 러너 abort */ }
// 계약 테스트: 매핑 사본 2벌 byte 동일
```
무엇이 깨졌나: 가드는 한 곳에 있었지만 전파 경로 하나가 끊겨 있었다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~D)은 "한 인덱스의 매핑 정본을 하나로 두고, 바꿀 땐 재색인 + alias 스왑"이다. 같은 원리(매핑은 생성 시점에 고정되는 스키마)에 다른 방안이 쓰인 사례:

### 방안 1 — 매핑·settings·플러그인·빌드 파일을 한 묶음으로 버전 관리
```text
문제 (서로 이름으로 참조하는 네 조각이 따로 변함)
  mappings:  "field_x": { "analyzer": "custom_ko" }      ← settings에 custom_ko 정의 없음
             → mapper_parsing_exception: analyzer [custom_ko] has not been configured
  settings:  "filter": ["new_filter"]                    ← repo의 플러그인 zip은 new_filter 없는 구버전
  build:     COPY plugin-X.zip ...                       ← 실제 파일명은 plugin-X-slim.zip
  build:     RUN install analysis-extra                  ← 쓰지 않는 플러그인을 네트워크로 설치 → 폐쇄망 빌드 실패
  운영:      untracked zip 충돌로 pull 거부 → 구버전 빌드 파일로 이미지가 만들어진 채 방치

고친 (한 묶음)
  - 참조되는 분석기 정의를 settings에 함께 둠 (다른 인덱스 정의에서 복사한 filter·tokenizer·analyzer 3종)
  - "배포 전 플러그인 zip 갱신"을 절차로 문서화
  - 코드 전수 검색으로 참조 0건인 플러그인 설치 줄 제거
  - 서버 상태 복원(pull → tracked zip 복원 → 재빌드) 후 설치된 플러그인 목록(_cat/plugins)으로 확인
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 매핑 정본 단일화 + 재색인·alias 스왑 | 분석기·플러그인은 이미 배포돼 있다 | 재색인 시간·디스크 두 벌 | 정본 밖(앱 자동 생성·부트스트랩 스킵)에서 드리프트 | 필드 구조·분석기 설정을 바꿀 때 |
| 1. 정의 묶음 통합 버전 관리 | 매핑이 커스텀 분석기·플러그인에 의존한다 | 빌드·배포 절차가 무거워짐 | 한 조각만 갱신되면 인덱스 생성 자체가 실패 | 커스텀 플러그인·폐쇄망 빌드가 있는 환경 |

**결론**: 매핑이 엔진 기본 분석기만 쓴다면 기본 방안(정본 하나 + 재색인)으로 충분하다.\
매핑이 커스텀 분석기·플러그인 바이너리에 의존하면 매핑 정본만 하나로 만들어서는 부족하다 — 매핑·settings·플러그인·빌드를 **한 단위로 버전 관리**해야 "정의는 있는데 구현이 없는" 실패를 막는다.\
두 방안은 배타적이지 않다 — 묶음 통합은 기본 방안의 전제(분석기가 실제로 배포돼 있다)를 보장하는 바깥 층이다.
