# api-design/21-api-documentation-openapi — API 문서: 명세 우선·OpenAPI·예제와 드리프트 검출 — 정리 (힌트)

## 해결하는 문제

API 문서가 위키에 손으로 쓰여 있으면, 코드는 바뀌는데 문서는 그대로 남는다.

```text
  위키 문서                      실제 서버 v1.2.1 응답
  id        : string            "id": 1001                 ← 숫자로 바뀜
  status    : PENDING | PAID    "status": "CANCELLED"      ← 새 값
  createdAt : date-time         "created_at": "..."        ← 이름이 바뀜
  → 문서대로 만든 클라이언트: 파싱 실패, enum 매핑 실패, 필드 누락으로 null
```

- 해법: 문서를 **기계가 읽는 명세**로 쓰고, 그 명세로 구현을 검사한다.
  - *OpenAPI*: HTTP API의 경로·메서드·파라미터·요청/응답 본문·인증을 YAML/JSON으로 기술하는 명세 형식(OpenAPI Initiative). 3.1.0이 2021-02-15, 3.1.1이 2024-10-24, 3.1.2와 3.2.0이 2025-09-19, 3.2.1이 2026-09-10에 발행됐다(spec.openapis.org 각 판의 발행일 메타데이터). 이 노트는 3.1 판을 기준으로 쓴다.
  - *명세 우선(design-first, spec-first)*: 코드보다 OpenAPI 문서를 먼저 쓰고 합의한 뒤, 그 문서로 서버 골격·클라이언트·목 서버·검증을 만든다.
  - *코드 우선(code-first)*: 코드의 애노테이션에서 OpenAPI 문서를 생성한다.
- 쉬운 예: 건축 설계도. 도면(명세)을 먼저 합의하고, 시공(구현) 뒤 도면과 실측을 대조(검사)한다. 도면 없이 짓고 나중에 사진으로 도면을 그리면, 그 도면은 "지은 그대로"일 뿐 "합의한 것"이 아니다.
- 똑같은 구조다. 실무 예: 외부 파트너용 결제 API. 파트너는 OpenAPI 문서로 SDK를 생성한다. 서버가 필드 이름을 하나만 바꿔도 파트너 SDK가 그 필드를 null로 읽는다.

## 동작·원리

### 1. OpenAPI 문서의 뼈대

```text
  openapi: 3.1.0                ← 명세 형식 버전
  info.version: 1.2.0           ← 이 OpenAPI 문서의 버전 — 형식 버전·API 버전과 별개
  paths
   └ /orders/{orderId}
      └ get  (operationId: getOrder)
         ├ parameters: orderId (path, required)
         └ responses
            └ '200' → content → application/json
                        ├ schema: $ref → components/schemas/Order
                        └ example: {...}
  components
   └ schemas
      └ Order  (JSON Schema 2020-12: type·required·properties·enum·format ...)
```

- *Schema Object*: OpenAPI 3.1부터 **JSON Schema Draft 2020-12의 상위 집합**이다. 3.0.3의 Schema Object는 JSON Schema Wright Draft 00의 "확장된 부분 집합"이었다(`null` 타입 대신 `nullable`). 그래서 3.1이면 2020-12를 지원하는 일반 JSON Schema 검증기로 응답을 검사할 수 있다.
  - 단 `discriminator`·`xml`·`externalDocs` 같은 OpenAPI 전용 키워드는 일반 검증기가 모른다. ajv 8.20.0 엄격 모드(기본)는 `strict mode: unknown keyword: "discriminator"`로 컴파일을 거부했다(사실 점검 실험) — 아래 실험이 `strict: false`를 준 이유다.
  - `jsonSchemaDialect` 필드로 기본 `$schema`를 바꿀 수 있다.
- *`$ref`*: 다른 위치의 정의를 가리키는 참조. 스키마를 한곳(`components`)에 두고 재사용한다.
- *`operationId`*: 연산의 고유 이름. 3.1.1 기준 API 안에서 **유일해야 한다**(MUST). 명세는 도구·라이브러리가 이 값으로 연산을 식별할 수 있다(MAY)고 적는다. 코드 생성기는 흔히 이 이름으로 메서드를 만든다 — 바꾸면 생성된 SDK의 메서드 이름이 바뀔 수 있다.
- *`info.version`*: OpenAPI 문서(Document)의 버전이다. 3.1.1 문구: OpenAPI 명세 버전과도, 설명되는 API의 버전과도, OpenAPI Description(여러 문서로 이뤄질 수 있는 설명 전체)의 버전과도 다르다.
- *예제*: `example`·`examples`는 스키마와 함께 주면 스키마에 **맞아야 한다(SHOULD)** — 반드시 검사되는 것은 아니다. Schema Object 안의 `example`은 3.1에서 폐기 예정(deprecated)이고 JSON Schema `examples`를 쓰라고 한다.

### 2. 명세 우선의 흐름 — 명세가 단일 출처

```text
          ┌─────────── openapi.yaml (리뷰·합의) ───────────┐
          │                                               │
     린트·검증                                        코드 생성
   ($ref 해결, 형식)                         서버 인터페이스 / 클라이언트 SDK / 목 서버
          │                                               │
          └──> CI: 실행 중인 구현의 실제 응답을 명세 스키마로 검증 ──> 불일치면 빌드 실패
```

- 핵심은 **명세 ↔ 구현 대조를 자동으로** 하는 것이다. 사람이 문서와 코드를 둘 다 고치는 흐름은 언젠가 어긋난다.
- 코드 우선도 대조는 필요하다. 생성된 문서는 구현과 일치하지만, **어제 문서와 오늘 문서의 차이**(파괴적 변경)를 누군가 봐야 한다 — 생성 결과를 저장소에 두고 diff를 리뷰한다.

### 실험: 깨진 명세와 어긋난 구현을 도구로 잡기

(실험, node 22.23.2 · @apidevtools/swagger-parser 12.1.0 · ajv 8.20.0(`ajv/dist/2020`) · ajv-formats 3.0.1, `node:22-alpine` 컨테이너, `--network none`, 2026-10-04)

명세(발췌):

```yaml
openapi: 3.1.0
info: { title: Orders API, version: 1.2.0 }
paths:
  /orders/{orderId}:
    get:
      operationId: getOrder
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Order' }
              example: { id: "ord_1", status: PAID, amount: 12000, createdAt: "2026-10-04T09:00:00Z" }
components:
  schemas:
    Order:
      type: object
      required: [id, status, amount, createdAt]
      additionalProperties: false
      properties:
        id: { type: string }
        status: { type: string, enum: [PENDING, PAID] }
        amount: { type: integer, minimum: 0 }
        createdAt: { type: string, format: date-time }
```

검사 코드(핵심):

```js
import SwaggerParser from '@apidevtools/swagger-parser';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

await SwaggerParser.validate('broken.yaml');                 // 1) 명세 자체 검사 ($ref를 Ordr로 오타)
const api = await SwaggerParser.dereference('openapi.yaml');
const media = api.paths['/orders/{orderId}'].get.responses['200'].content['application/json'];
const ajv = new Ajv2020({ allErrors: true, strict: false }); addFormats(ajv);
const validate = ajv.compile(media.schema);                  // 2) 명세의 응답 스키마 = JSON Schema 2020-12
validate(media.example);                                     //    예제가 스키마에 맞나
const r = await fetch('http://127.0.0.1:18080/orders/ord_1'); // 3) 떠 있는 구현의 실제 응답
validate(await r.json());
```

구현은 `{ id: 1001, status: 'CANCELLED', amount: 12000, created_at: '...' }`를 돌려주게 했다(명세와 어긋난 구현을 흉내).

```text
broken.yaml: Missing $ref pointer "#/components/schemas/Ordr". Token "Ordr" does not exist.
명세의 example        PASS
GET /orders/ord_1 -> 200 application/json
구현 응답              FAIL
    / must have required property 'createdAt' 
    / must NOT have additional properties created_at
    /id must be string 
    /status must be equal to one of the allowed values ["PENDING","PAID"]
```

- 관찰
  - 명세 오타(`$ref` 대상 없음)는 파서 검증 단계에서 잡혔다.
  - 구현 응답은 HTTP 200이고 JSON도 정상이지만, 스키마 대조로 드리프트 **세 가지**(이름·타입·enum)가 검증 오류 **네 개**로 한 번에 나왔다: 필드 이름 변경(필수 누락 + 추가 속성 — 오류 둘), 타입 변경, 명세에 없는 enum 값.
  - 예제는 이 실험에서 직접 검증했을 때 PASS였다. 명세 형식만으로는 예제를 검사하지 않는다(SHOULD).
- 해석: "응답이 200이다"만 보는 테스트는 이 세 가지 드리프트를 하나도 못 잡는다. 명세 스키마를 테스트의 기대값으로 써야 드리프트가 보인다.

### 3. `additionalProperties: false`의 양면

```text
  서버가 응답에 필드 하나 추가 (하위 호환 변경으로 여기는 경우가 많다)
   ├ 서버 측 계약 테스트가 additionalProperties:false로 검증 → 명세부터 고치게 강제 (드리프트 차단)
   └ 클라이언트가 같은 스키마로 엄격 검증 → 필드 추가만으로 클라이언트가 실패 (호환성 파손)
```

- 서버 쪽 드리프트 검사에서는 "명세에 없는 필드"를 잡는 데 유용하다(실험의 `created_at`).
- 같은 스키마를 클라이언트가 응답 검증에 쓰면, 서버의 필드 추가가 파괴적 변경이 된다. 클라이언트는 모르는 필드를 무시하도록 두는 편이 하위 호환 규칙과 맞다([07](../07-versioning-and-compatibility/2-summary.md)).

## 쓰이는 자료구조·알고리즘

- **트리 + 참조 그래프**: OpenAPI 문서는 JSON 트리이고 `$ref`가 노드 사이에 간선을 더한다. `dereference`는 참조를 따라가 트리에 펼친다. 자기 참조 스키마(트리 구조 자원)가 있으면 순환이 생기므로 방문 기록이 필요하다 → [data-structure/08-graph](../../data-structure/08-graph/2-summary.md).
- **JSON Pointer**: `#/components/schemas/Order`는 루트에서 키를 따라 내려가는 경로다. 실험 오류의 `Token "Ordr" does not exist`가 그 경로 탐색 실패다.
- **스키마 검증 = 재귀 하강**: 검증기는 스키마 트리와 값 트리를 함께 내려가며 키워드(`type`·`required`·`enum`·`additionalProperties`)를 검사하고, 실패 위치를 JSON Pointer(`/id`, `/status`)로 보고한다. ajv는 스키마를 JS 함수로 컴파일해 둔다.
- **명세 diff**: 두 판의 명세 트리를 비교해 삭제된 경로·필수로 바뀐 필드·좁아진 enum을 파괴적 변경으로 분류한다.

## 적용 — 풀어나가는 법

### 1. 명세 우선으로 시작하기

1. 새 엔드포인트는 PR에 `openapi.yaml` 변경부터 올리고 클라이언트 팀과 리뷰한다. 오류 응답도 명세에 넣는다(`application/problem+json`, [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md)).
2. 모든 응답 예제를 스키마로 검증하는 단계를 CI에 둔다(명세 형식은 강제하지 않는다).
3. 명세에서 서버 인터페이스·클라이언트 SDK를 생성하거나, 최소한 구현 응답을 명세 스키마로 검사하는 계약 테스트를 둔다.
4. 명세 diff에서 파괴적 변경(경로 삭제, 필드 삭제·이름 변경, 타입 변경, 필수 추가, enum 축소)을 탐지해 리뷰를 요구한다.
5. 문서 사이트는 이 명세에서 생성한다. 손으로 쓰는 문서는 개념 설명·튜토리얼에만 둔다.

### 2. 코드 우선이라면

- 생성된 OpenAPI 파일을 저장소에 커밋하고 PR마다 diff를 본다. "코드가 곧 문서"여도 **변경 리뷰**는 따로 해야 한다.
- 애노테이션에 예제를 넣었다면 같은 예제를 테스트 입력으로도 쓴다 — 예제가 낡으면 테스트가 깨지게.

### 3. 소비자 관점의 계약 테스트와 함께

- OpenAPI 스키마 검증은 "응답이 명세 모양인가"를 본다. 특정 소비자가 실제로 쓰는 필드·상호작용은 소비자 주도 계약 테스트가 본다([testing/13](../../testing/13-contract-testing/2-summary.md)). 둘은 겹치지만 대신하지 않는다.

### 4. 진단

```text
  명세 자체: 파서 검증($ref 해결, 필수 필드) + 린트 규칙(operationId 중복 등)
  예제: 스키마로 전부 검증
  구현: 스테이징에서 주요 엔드포인트를 호출해 응답을 명세 스키마로 검증 → 실패 위치(/id, /status)를 리포트
  운영: 게이트웨이·서버 미들웨어에서 응답 표본을 스키마로 검증해 불일치 비율을 지표로 (전수 검증은 비용 주의)
```

## 장애 시나리오와 대처

### 1. 파트너 SDK가 필드를 null로 읽는다 — 문서-구현 불일치 (⚠)

- **현상**: 배포 뒤 파트너가 "주문 생성 시각이 비어 있다"고 신고한다. 서버 로그에는 오류가 없다.
- **보이는 형태**: HTTP 200, 응답 본문에 `created_at`이 있지만 SDK는 `createdAt`을 찾는다. 실험의 `must have required property 'createdAt'`.
- **원인**: 구현에서 직렬화 설정(네이밍 전략)을 바꿨는데 명세와 대조하는 테스트가 없었다.
- **대처**: 응답을 명세 스키마로 검증하는 계약 테스트를 CI에 둔다. 이름을 바꿔야 하면 새 필드를 추가하고 옛 필드를 폐기 기간 동안 함께 보낸다([07](../07-versioning-and-compatibility/2-summary.md)).

### 2. 명세에 없는 enum 값이 나가 클라이언트가 실패한다 (⚠)

- **현상**: 주문 취소 기능을 출시하자 일부 앱에서 주문 목록이 안 열린다.
- **보이는 형태**: 응답에 `"status": "CANCELLED"`. 엄격 역직렬화 클라이언트(Jackson enum 등)에서 역직렬화 예외. 실험의 `must be equal to one of the allowed values ["PENDING","PAID"]`.
- **원인**: 구현에 enum 값을 추가했지만 명세는 그대로였고, 클라이언트는 명세의 닫힌 enum을 믿었다.
- **대처**: enum 추가를 명세 변경 + 리뷰 대상으로 다룬다. 명세 설명에 "새 값이 추가될 수 있으니 모르는 값을 처리하라"를 명시하고, 클라이언트는 알 수 없는 값용 기본 분기를 둔다.

### 3. 문서의 예제를 복사한 코드가 동작하지 않는다 — 예제 부패

- **현상**: 개발자 포털의 예제 요청을 그대로 보내면 400이 온다.
- **원인**: 스키마는 고쳤지만 예제는 안 고쳤다. OpenAPI는 예제가 스키마에 맞아야 한다고 권할 뿐(SHOULD) 검사하지 않는다.
- **대처**: CI에서 모든 예제를 스키마로 검증한다(실험의 `명세의 example PASS` 단계). 가능하면 예제를 통합 테스트의 입력으로도 쓴다.

### 4. 명세 파일이 깨져 문서 사이트·코드 생성이 멈춘다

- **현상**: 문서 빌드가 실패하거나, 코드 생성기가 일부 모델을 빈 객체로 만든다.
- **보이는 형태**: `Missing $ref pointer "#/components/schemas/Ordr"` 같은 오류(실험).
- **원인**: 손으로 고친 명세의 참조 오타. 중복 `operationId`도 코드 생성을 꼬이게 한다(3.1.1에서 MUST 위반).
- **대처**: 명세 파서 검증·린트를 PR 단계에서 돌린다. 머지 전에 실패하게 한다.

## 핵심 문장

- 사람이 문서와 코드를 따로 고치면 언젠가 어긋난다. 명세를 기계가 읽는 형식(OpenAPI)으로 두고 구현을 그 명세로 자동 검사해야 드리프트가 보인다.
- OpenAPI 3.1의 Schema Object는 JSON Schema 2020-12의 상위 집합이라, 일반 JSON Schema 검증기로 실제 응답을 검사할 수 있다(실험: 200 응답에서 드리프트 3가지를 검증 오류 4개로 검출).
- 예제가 스키마에 맞는지는 명세 형식이 강제하지 않는다(SHOULD). CI에서 직접 검증한다.
- `info.version`은 문서 버전, `openapi`는 명세 형식 버전이다. `operationId`는 유일해야 하고, 코드 생성기가 흔히 SDK 메서드 이름으로 쓴다.
- 응답 스키마의 `additionalProperties: false`는 서버 드리프트 검사에는 유용하지만, 클라이언트 검증에 쓰면 필드 추가가 파괴적 변경이 된다.

## 관련 주제·근거

- 선행
  - [01-api-as-contract](../01-api-as-contract/2-summary.md) — API = 공개 계약, Hyrum의 법칙 — 영역 표: [curriculum](../curriculum.md)
- 후속·연결
  - [07-versioning-and-compatibility](../07-versioning-and-compatibility/2-summary.md) · [08-schema-and-serialization](../08-schema-and-serialization/2-summary.md) · [04-error-format-problem-details](../04-error-format-problem-details/2-summary.md) · [18-api-style-selection](../18-api-style-selection/2-summary.md)
  - testing [13-contract-testing](../../testing/13-contract-testing/2-summary.md) — 소비자 주도 계약 테스트
  - software-design [23-design-by-contract](../../software-design/23-design-by-contract/2-summary.md)
- 명세·문서
  - OpenAPI Specification 3.1.1 — Schema Object(JSON Schema 2020-12 상위 집합, `jsonSchemaDialect`), `example` SHOULD match schema, Schema Object `example` deprecated, `operationId` MUST be unique, `info.version` 정의 <https://spec.openapis.org/oas/v3.1.1.html>
  - OpenAPI Specification 3.0.3 — Schema Object = JSON Schema Wright Draft 00의 extended subset <https://spec.openapis.org/oas/v3.0.3.html>
  - OpenAPI 발행 목록(3.1.0 2021-02-15, 3.1.1 2024-10-24, 3.1.2·3.2.0 2025-09-19, 3.2.1 2026-09-10 — 각 판 HTML의 발행일 메타데이터) <https://spec.openapis.org/oas/>
  - JSON Schema Draft 2020-12 <https://json-schema.org/draft/2020-12>
  - @apidevtools/swagger-parser <https://github.com/APIDevTools/swagger-parser> · Ajv(JSON Schema 2020-12 지원) <https://ajv.js.org/>
- 실험 목록
  - 깨진 `$ref` 명세 검증, 명세 예제 검증, 명세와 어긋난 구현(HTTP 서버)의 실제 응답을 명세 스키마로 검증 — node 22.23.2, swagger-parser 12.1.0, ajv 8.20.0, ajv-formats 3.0.1, `node:22-alpine`(`--network none`). 사실 점검에서 다시 돌려 같은 출력
  - (사실 점검) ajv 엄격 모드가 OpenAPI 전용 키워드 `discriminator`를 거부하는지 — 같은 환경, `strict: true`면 컴파일 오류, `false`면 통과
