# data-engineering/09-data-contracts-and-schema-registry — 정답

## 정답

### 1. 레지스트리와 계약의 관계

- 레지스트리의 등록 시 호환성 검사는 **스키마** 칸만 본다. 새 스키마 문서와 옛 스키마 문서를 비교해 호환성 모드에 맞는지 본다.
  - Confluent의 Data Contracts 기능(Enterprise·Cloud Advanced)을 쓰면 스키마에 품질 규칙(`ruleSet`)을 붙여 값도 검사할 수 있다. 다만 실행 주체는 클라이언트 SerDes다.
- 못 하는 것
  - 의미: `amount`가 부가세 포함에서 제외로 바뀌어도 이름·타입이 같으면 통과한다.
  - 품질: NULL 비율, 중복, 허용값 범위는 바이트가 아니라 값의 문제다(10번).
  - SLA·소유자: "매일 09:00까지 도착", "문의는 주문팀"은 스키마에 없다.
- 그래서 계약은 레지스트리 + 품질 검사 + 문서화된 의미·SLA·소유자의 묶음이다.

### 2. 세 모드와 배포 순서 (Confluent 문서 기준)

| 모드 | 보장 | 먼저 올릴 쪽 |
|---|---|---|
| BACKWARD | 새 스키마(X)의 소비자가 X·X-1로 쓴 데이터를 읽는다 | 소비자 |
| FORWARD | X로 쓴 데이터를 X·X-1의 소비자가 읽는다 | 생산자(옛 데이터가 소비자에게 더 안 가게 한 뒤 소비자) |
| FULL | 둘 다 | 순서 무관 |

- `_TRANSITIVE`가 붙으면 X-1뿐 아니라 등록된 모든 옛 버전과 검사한다.
- Confluent 기본값은 비transitive `BACKWARD`다.

### 3. 변경 세 가지의 판정

```text
Add required field       ✘   ✔   ✘      ← (a) currency 추가
Remove required field    ✔   ✘   ✘      ← (b) amount 삭제
Widen a scalar type      ✔   ✘   ✘      ← (c) long → double
```

- (a) 새 reader에는 `currency`가 있는데 옛 데이터에는 없고 기본값도 없다 → BW 실패. 옛 reader는 새 데이터의 `currency`를 무시하면 된다 → FW 통과.
- (b) 새 reader는 `amount`를 모르니 무시 → BW 통과. 옛 reader는 `amount`가 필요한데 새 데이터에 없다 → FW 실패.
- (c) 새 reader(double)가 옛 데이터(long)를 승격해 읽는다 → BW 통과. 옛 reader(long)는 double을 못 읽는다 → FW 실패.
- 모형 결과는 Confluent 문서의 Avro 규칙표 같은 행과 일치했다. Protobuf는 같은 표에서 열이 다르다(예: 스칼라 넓히기·좁히기가 세 모드 모두 ✔).

### 4. 이름 바꾸기는 FULL을 통과한다

- 통과한다. 해석 규칙에서 이름 바꾸기는 "선택 필드 삭제 + 선택 필드 추가"이고, 둘 다 FULL 허용 변경이다.

```text
둘 다 기본값 null    FULL     -> []  (통과)
v2로 쓴 레코드        = {region_code=KR-11, order_id=1001}
v1 소비자가 읽은 결과 = {order_id=1001, region=null}   <- region 조용히 null
```

- 옛 소비자는 `region`을 writer에서 찾지 못해 기본값 null을 쓴다. 에러 없이 값이 사라진다.
- 새 이름에 기본값이 없으면 BACKWARD에서 막힌다(실험 B 첫 줄). 막히는 쪽이 오히려 안전하다.

### 5. 비transitive BACKWARD의 구멍

```text
v3 등록 BACKWARD            -> []
v3 등록 BACKWARD_TRANSITIVE -> [BW vs v1: reader 필드 'region'가 writer에 없고 기본값도 없음]
v3 소비자가 v1 레코드를 재생 -> 실패: missing required field region
```

- 마지막 줄은 모형이 v3를 reader 스키마로 고정한 소비자를 흉내 낸 결과다. Confluent 기본 `GenericRecord` 소비자는 writer 스키마(v1)로 읽으므로 역직렬화 자체는 될 수 있다.

- BACKWARD는 v3를 v2와만 비교한다. v2 데이터에는 `region`이 있으니 통과.
- TRANSITIVE는 v1과도 비교한다. v1 데이터에는 `region`이 없고 v3에는 기본값이 없어 실패.
- 드러나는 순간(최신 스키마를 reader로 고정한 소비자): 새 소비자를 `earliest`로 붙이거나, 재처리를 위해 오프셋을 되감을 때. 운영 소비자(최신 데이터만 읽는)는 문제를 모른다.

### 6. 이름 변경 → NULL 진단

- 확인 SQL
  - NULL 비율을 일자별로: 2026-10-01 0.0% → 2026-10-02 100.0%(실험).
  - 원천 키 집합 diff: `jsonb_object_keys(payload)`와 계약 키 목록 비교 → `missing region`, `unexpected region_code`(실험).
- 즉시 복구: 변환을 `coalesce(payload->>'region_code', payload->>'region')`로 고치고 영향받은 날짜 파티션을 다시 적재(08번 덮어쓰기라 재실행해도 2배가 되지 않게).
- 재발 방지: 계약에 `region` 필수 명시, 적재 시 키 diff·NULL 비율 검사, 필요하면 적재 테이블에 `NOT NULL` — 실험에서 조용한 NULL이 `ERROR: null value in column "region" ... violates not-null constraint`로 바뀌었다.

### 7. "기타" 급증

- 의심: enum 새 값. 허용값 밖 값을 세는 쿼리로 확인 — 실험에서 `PARTIALLY_REFUNDED 100`.
- 소비자 코드: `default -> "기타"`처럼 모르는 값을 정상 범주에 섞지 않는다. `UNKNOWN`으로 따로 두고 값별 카운터를 올려, 비율이 넘으면 알림이 가게 한다.
- 계약 쪽: enum 값 추가를 변경 공지 대상으로 둔다. Avro에서는 reader enum에 없는 기호가 reader의 enum 기본값으로 바뀐다(기본값이 없으면 오류).

### 8. 강제 지점

```text
① 생산자 CI(스키마 diff·계약 리뷰) → ② 레지스트리 등록(호환성 모드) → ③ 직렬화기(등록된 스키마로만)
→ ④ 브로커 스키마 ID 검증(Confluent 기능) → ⑤ 적재·변환(제약·계약 검사 SQL) → ⑥ 품질 검사(10번)
```

- 앞일수록 싸다. 생산자 배포 전에 막히면 잘못된 데이터가 한 건도 안 들어온다.
- 레지스트리 밖 데이터는 ⑤⑥에서 막는다. 키 diff·NULL 비율·허용값 검사, 적재 테이블 제약.
- 막을지(차단) 알리기만 할지(경고)는 10번 데이터 품질 노트의 "차단 vs 경고"로 이어진다.

### 9. 이름 변경 절차 — expand/contract

1. expand: v2에서 `region`과 `region_code`를 둘 다 채운다(새 필드는 선택 필드로 추가).
2. 소비자 이전: 계보로 찾은 소비자들이 `region_code`를 읽게 바꾼다.
3. contract: v3에서 `region`을 지운다. 선택 필드 삭제라 BACKWARD 통과.
4. 계약 버전을 메이저로 올리고 이전 기간을 공지한다.

- DB 컬럼 이름 변경의 expand/contract와 같은 구조다(database/26).
- 소비자 목록: 계보(11번)에서 그 필드를 읽는 하류 잡·데이터셋을 컬럼 수준으로 찾는다. 계약의 소유자·지원 채널은 공지 대상을 준다.
