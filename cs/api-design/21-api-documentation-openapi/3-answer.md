# api-design/21-api-documentation-openapi — 정답

## 정답

### 1. 손으로 쓴 문서가 어긋나는 이유

- 코드와 문서가 **두 출처**다. 코드를 고칠 때 문서를 함께 고치는지 검사하는 장치가 없으면, 직렬화 설정·enum 추가 같은 작은 변경이 문서에 반영되지 않는다.
- 핵심 장치: 문서를 기계가 읽는 명세(OpenAPI)로 두고, **구현의 실제 응답을 그 명세로 자동 검사**한다(CI). 명세가 단일 출처가 된다.

### 2. 뼈대와 두 버전

```text
  openapi: 3.1.0
  info.version: 1.2.0
  paths
   └ /orders/{orderId}
      └ get (operationId: getOrder)
         ├ parameters
         └ responses → '200' → content → application/json → schema($ref) · example
  components
   └ schemas → Order
```

- `openapi`: 문서가 따르는 **OpenAPI 명세 형식**의 버전(3.1.0).
- `info.version`: 이 **OpenAPI 문서**의 버전. 3.1.1 문구상 명세 형식 버전과도, 설명되는 API의 버전과도 별개다.

### 3. 명세 우선 vs 코드 우선

- 명세 우선: OpenAPI 문서를 먼저 쓰고 클라이언트와 합의 → 서버 골격·SDK·목 서버 생성 → 구현을 명세로 검사.
- 코드 우선: 코드 애노테이션에서 문서를 생성. 문서는 항상 구현과 같지만 "합의한 것"이 아니라 "지금 구현된 것"이다.
- 코드 우선에서도 할 일: 생성된 명세를 저장소에 커밋하고 **PR마다 diff를 리뷰**해 파괴적 변경(필드 삭제·이름 변경·타입 변경·enum 축소)을 잡는다.

### 4. 드리프트 검증 결과

- 실험 출력(swagger-parser 12.1.0 + ajv 8.20.0)

```text
구현 응답              FAIL
    / must have required property 'createdAt'
    / must NOT have additional properties created_at
    /id must be string
    /status must be equal to one of the allowed values ["PENDING","PAID"]
```

- 오류 4개: 필수 `createdAt` 누락, 명세에 없는 `created_at`, `id` 타입, 명세에 없는 enum 값. (필드 이름 변경 하나가 오류 두 개로 나타난다.)
- "200이면 통과" 테스트는 **0개**를 잡는다. 응답은 `200 application/json`이었다.

### 5. Schema Object와 JSON Schema

- 3.1: Schema Object는 **JSON Schema Draft 2020-12의 상위 집합**이다. `jsonSchemaDialect`로 기본 방언을 정한다.
- 3.0.3: JSON Schema Wright Draft 00의 **확장된 부분 집합**이었다(`null` 타입 대신 `nullable` 등).
- 의미: 3.1 명세의 스키마는 2020-12를 지원하는 일반 검증기(실험의 `ajv/dist/2020`)로 검사할 수 있다. 다만 `discriminator` 같은 OpenAPI 전용 키워드는 일반 검증기가 모르므로 엄격 모드를 끄거나(실험의 `strict: false`) 키워드를 등록한다. 3.0 명세는 OpenAPI 전용 변환이나 3.0을 이해하는 도구가 필요하다.

### 6. 예제와 스키마 불일치

- 형식상 오류는 아니다. 3.1.1: 예제가 스키마와 함께 주어지면 스키마에 **맞아야 한다(SHOULD)** — 권고다. 파서가 예제를 반드시 검사하지는 않는다.
- 실무: CI에서 모든 예제를 스키마로 검증한다(실험의 `명세의 example PASS` 단계). 예제를 통합 테스트 입력으로도 쓰면 낡은 예제가 테스트를 깨뜨려 드러난다.
- 참고: Schema Object 안의 `example`은 3.1에서 폐기 예정이고 JSON Schema `examples`를 권한다.

### 7. `additionalProperties: false`의 양면

- 서버 쪽 드리프트 검사: 명세에 없는 필드가 응답에 나가면 실패한다 → 명세부터 고치게 강제한다(실험의 `created_at`).
- 클라이언트 쪽 검증: 서버가 필드를 **추가**하기만 해도 클라이언트가 실패한다.
- 충돌: 필드 추가는 보통 하위 호환 변경으로 다룬다(클라이언트가 모르는 필드를 무시한다는 전제). 클라이언트가 닫힌 스키마로 엄격 검증하면 그 전제가 깨진다. 그래서 닫힌 스키마는 서버 측 검사에만 쓰고, 클라이언트는 모르는 필드를 무시하게 두는 편이 맞다.

### 8. "생성 시각이 비어 있다"

- 의심: 구현의 응답 필드 이름이 명세와 달라졌다(예: 직렬화 네이밍 전략 변경으로 `createdAt` → `created_at`). 서버는 정상 200을 보내므로 로그에 오류가 없고, SDK는 명세 이름의 필드를 못 찾아 null로 둔다.
- 확인: 실제 응답을 명세 스키마로 검증한다 → `must have required property 'createdAt'` + `must NOT have additional properties created_at`.
- CI: 주요 엔드포인트의 실제 응답을 명세 스키마로 검증하는 계약 테스트. 이름을 바꿔야 하면 새 필드 추가 + 옛 필드를 폐기 기간 동안 병행.

### 9. 깨진 `$ref`

- 원인: 명세를 손으로 고치다 참조 대상 이름을 잘못 적었다(`Order` → `Ordr`). JSON Pointer 경로 탐색이 실패한다.
- 머지 전 검출: PR 단계에서 명세 파서 검증(`SwaggerParser.validate` 등)·린트를 돌리고 실패하면 머지를 막는다. `operationId` 중복(MUST 위반) 같은 규칙은 린트 규칙으로 함께 건다(어느 도구가 무엇을 검사하는지는 도구 문서로 확인한다).
