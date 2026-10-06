# security/15-access-control-models — 정답

## 정답

### 1. 인증 필터가 있어도 IDOR가 생기는 이유

- 인증: "이 요청을 보낸 주체가 누구인가".
- 인가: "그 주체가 **이 객체**에 **이 동작**을 해도 되나".
- 인증 필터는 첫 질문에만 답한다. `findById(id)`로 꺼내 돌려주면 두 번째 질문은 아무도 묻지 않는다. 로그인한 alice가 bob의 주문 ID를 넣어도 통과한다.

### 2. 권한 행렬과 ACL·capability

```text
                 주문1001   주문1002   /admin/users
  alice           R W         -           -
  bob             -          R W          -
  admin           R           R          R

  ACL        = 열 단위:  주문1002 → [bob: RW, admin: R]        (객체에 붙는다)
  capability = 행 단위:  alice    → [주문1001: RW]              (주체가 들고 다닌다)
```

- OSTEP 55.3·55.4. ACL은 "이 객체에 누가 접근하나"를 보기 쉽고, capability는 "이 주체가 무엇에 접근하나"를 보기 쉽다.

### 3. RBAC의 한계와 대안

- RBAC는 사용자 → 역할 → 권한(동작, 객체)이다. NIST 모델상 객체별 권한도 줄 수 있지만, 실무 역할은 보통 대상 **종류** 단위다. "자기 담당 고객의 주문"처럼 계속 바뀌는 관계를 역할·권한 할당으로 따라가면 관리가 무너진다.
- 역할로 억지로 쪼개면 `SUPPORT_TEAM_A`… 처럼 역할이 폭증한다.
- ABAC: `subject.id == resource.assignedAgentId ∧ action == read`처럼 속성 규칙으로 쓴다(NIST SP 800-162).
- ReBAC: `customer:42#agent@user:7` 튜플과 "고객의 agent는 그 고객 주문의 viewer" 재작성 규칙으로 쓴다(Zanzibar).

### 4. 실험 예측

- v1 `/v1/orders/1002` + alice → **200**, bob의 주문 내용이 그대로 나온다(실험 출력 `owner=bob`).
- v2 `/v2/orders/1002` → **404**, `/v2/orders/9999` → **404**.
- 같은 값을 주는 이유: 남의 것은 403, 없는 것은 404로 갈리면 번호를 훑어 "존재하는 주문"을 셀 수 있다. 소유 조건을 조회에 넣으면 남의 것이 곧 "없는 것"이 된다.

### 5. ReBAC 탐색 경로

```text
  doc:readme#viewer
     ├─ 직접 튜플: group:eng#member → user:11 (아님)
     ├─ computed: doc:readme#editor → doc:readme#owner → user:10 (아님)
     └─ tuple_to_userset: parent = folder:A → folder:A#viewer → user:12  ✔
```

- 실험 출력: `doc:readme#viewer <- folder:A#viewer <- user:12`.
- 순환(그룹 A ⊂ B ⊂ A)이 있으면 같은 `객체#관계`를 다시 방문하지 않게 **방문 집합**을 둔다. 실험의 `visited` 집합이 그 역할이다. 실서비스는 깊이 상한도 둔다.

### 6. BOLA/BFLA, 수평/수직

- BOLA(API1): 접근해도 되는 `/orders/{id}`에서 ID를 남의 것으로 바꾼다 → 수평 권한 상승(같은 등급의 다른 사용자 자원).
- BFLA(API5): 일반 사용자가 `/admin/users`를 직접 호출한다 → 수직 권한 상승(더 높은 등급의 기능).
- 실험: v1 주문 API는 BOLA, v1 관리자 API는 BFLA였다.

### 7. `@PostAuthorize` 주의점

- 메서드가 **실행된 뒤** 반환값을 검사한다. 쓰기 메서드면 검사 전에 변경이 일어난다(트랜잭션이 검사까지 감싸 롤백되게 구성한 경우만 DB 변경이 되돌려지고, 외부 호출 같은 부수 효과는 남는다). Spring Security 문서도 쓰기에는 권장하지 않으니 읽기 전용에만 쓴다.
- 거부되면 `AccessDeniedException` → 403이다. 없는 객체의 404와 갈려 존재 여부가 샌다.
- 쿼리에 소유 조건(`findByIdAndOwnerId`, `WHERE id=? AND owner_id=?`)을 넣으면 남의 객체를 아예 읽지 않고, 응답도 404로 통일된다. 쓰기에도 그대로 쓴다(영향 행 수 0 → 404).

### 8. 인가 서비스 타임아웃 → 통과

- 확인: 인가 클라이언트의 `timeout`·예외 로그 시각과, 같은 시각 평소 403이던 요청의 200을 접근 로그에서 맞춰 본다.
- 고칠 곳: 인가 호출을 감싼 예외 처리. `catch (...) { return true; }`를 거부로 바꾼다.
- 어긴 원칙: Saltzer–Schroeder의 fail-safe 기본값("배제가 아니라 허가에 근거해 결정"). 가용성은 짧은 TTL 결과 캐시·타임아웃·서킷 브레이커로 다루고, 기본값은 거부로 둔다.

### 9. "new enemy"

- 원인: 회수(Bob을 폴더 ACL에서 제거) **뒤에** 생긴 내용인데, 인가 검사가 회수 **전** 스냅샷(캐시·지연 복제본)으로 돌았다(Zanzibar §2.2 예 A·B).
- 대처
  - Zanzibar: 내용 변경 때 받은 zookie를 검사 요청에 실어, 그 시각 이후 스냅샷으로 판정한다.
  - 일반 서비스: 인가 캐시 TTL을 짧게, 회수 이벤트로 캐시 무효화, 회수 직후 검사는 주 저장소에서 읽는다.

### 10. 403 vs 404

- 피할 조합: "남의 것 = 403, 없는 것 = 404". 응답 차이로 객체 존재가 새고, 순차 ID와 겹치면 전체 규모까지 드러난다.
- 고를 수 있는 규칙 두 가지
  - 권한 검사를 존재 확인보다 먼저 해서, 권한이 없으면 존재와 무관하게 403.
  - RFC 9110 §15.5.4처럼 숨기려면 둘 다 404(MAY).
- 하나를 골라 엔드포인트 전체에 같게 적용하고, 테스트로 고정한다.
