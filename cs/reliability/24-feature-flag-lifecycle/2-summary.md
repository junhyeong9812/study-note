# reliability/24-feature-flag-lifecycle — 피처 플래그의 수명: 유형·평가 일관성·장애 시 기본값·제거 부채 — 정리 (힌트)

## 해결하는 문제

배포(코드를 서버에 올림)와 릴리스(사용자가 기능을 봄)가 한 덩어리면, 기능을 끄는 유일한 방법이 재배포다.\
재배포는 분 단위가 걸리고, 그 자체가 또 하나의 변경이다(→ [23-deployment-strategies](../23-deployment-strategies/2-summary.md)).

```text
 플래그 없음                                  플래그 있음
 코드 배포 = 기능 공개                         코드 배포(꺼진 채) ──> 플래그 켜기(5% → 50% → 100%)
 문제 → 재배포로 되돌림(분)                     문제 → 플래그 끄기(설정 변경, 재배포 없음)
```

- *피처 플래그(feature flag, feature toggle)*: 실행 중에 어느 코드 경로를 탈지 바꾸는 스위치. 코드에는 두 경로가 다 들어 있다.
- 대가가 있다. 플래그 하나는 코드 경로 둘이다. 플래그 n개는 켜짐·꺼짐 조합 2^n개다. 다 쓴 플래그를 지우지 않으면 죽은 코드가 운영 서버에 "켤 수 있는 상태로" 남는다.

쉬운 예: 건물의 차단기 판이다.
- 새 조명을 달 때 차단기를 내린 채 공사하고(배포), 다 되면 올린다(릴리스). 이상하면 내린다(킬 스위치).
- 그런데 다 쓴 차단기에 이름표 없이 새 조명을 연결하면, 누군가 옛 이름표대로 올렸을 때 엉뚱한 곳에 불이 들어온다.

똑같은 구조다.\
실무 예: Knight Capital(2012-08-01)은 옛 Power Peg 기능을 켜던 플래그를 새 RLP 기능용으로 **재사용**했다. 8대 중 1대에 새 코드가 배포되지 않았고, 그 1대에서 플래그가 2003년 이후 쓰지 않던 Power Peg 코드를 켰다(SEC 명령 34-70694 ¶13·¶15·¶16. Power Peg 사용 중단은 2003년, ¶14).

## 동작·원리

### 1. 플래그의 네 유형 — 수명과 동적성

Hodgson(2016, 2017 개정) "Feature Toggles (aka Feature Flags)"의 분류다. 두 축은 **얼마나 오래 사나**와 **판정이 얼마나 자주 바뀌나**다.

```text
 판정이 요청마다 바뀜 ▲
   (동적)            │  실험(Experiment)          권한(Permissioning)
                     │  시간~주                    수년(제품 기능)
                     │
                     │  운영(Ops)·킬 스위치         
                     │  대부분 짧게, 일부는 상시
   판정이 대체로 배포 │  릴리스(Release)
   마다만 바뀜(정적)  │  1~2주
                     └──────────────────────────────────────────▶ 오래 산다
```

| 유형 | 용도 | 수명(Hodgson) | 판정 |
|---|---|---|---|
| 릴리스 | 미완성 코드를 꺼진 채 배포, 준비되면 켬 | "a week or two"보다 길지 않게(제품 쪽은 더 길 수 있음) | 대체로 정적("typically very static") |
| 실험 | A/B 테스트 — 사용자를 집단에 넣고 **같은 사용자는 같은 경로로** | 통계적으로 유의할 만큼, 시간~주 | 요청마다(사용자별) |
| 운영 | 성능이 불확실한 기능을 운영자가 빨리 끄거나 줄임. 일부는 상시 "킬 스위치" | 대부분 짧음, 킬 스위치는 오래 | 빠르게 바꿔야 함 |
| 권한 | 유료·베타·내부 사용자에게만 기능 | 오래 | 요청마다 |

- *킬 스위치(kill switch)*: 부하가 높을 때 덜 중요한 기능(추천 패널 등)을 끄는 상시 운영 플래그. Hodgson은 이것을 "수동으로 다루는 서킷 브레이커"라고 부른다(→ [10-circuit-breaker](../10-circuit-breaker/2-summary.md)).
- 유형을 나누는 이유: 관리 방식이 달라서다. 릴리스 플래그는 빨리 지워야 하고, 킬 스위치는 지우면 안 되고 주기적으로 실제로 눌러 봐야 한다.

### 2. 평가 — 규칙 트리와 결정적 해시 버킷

```text
 evaluate("new-checkout", 사용자 컨텍스트, 기본값)
   ├─ 플래그 꺼짐(kill)?                    → off 값
   ├─ 개별 지정(userId ∈ 허용 목록)?          → on
   ├─ 규칙 1: country == "KR" && plan == "beta" → on
   ├─ 규칙 2: … 
   ├─ 비율 출시: bucket(flagKey, salt, userId) < 0.20 → on
   └─ 아무 데도 안 걸림                      → off 값
 평가 중 오류(설정 못 받음, 타입 불일치)        → 코드가 넘긴 "기본값"
```

- 규칙은 위에서부터 처음 맞는 것을 쓴다(첫 일치). 순서가 의미다.
- *해시 버킷(hash bucket)*: 사용자 ID를 해시해 0~1 사이 수로 바꾸고, 그 수가 비율보다 작으면 켠다. 같은 입력이면 어느 서버에서 언제 계산해도 같은 값이 나온다.
  - LaunchDarkly Java SDK `EvaluatorBucketing.java`는 `sha1(flagKey + "." + salt + "." + userKey)`의 앞 15자리 16진수를 `0xFFFFFFFFFFFFFFF`로 나눈다(GitHub launchdarkly/java-server-sdk, 2026-10-01 열람). 아래 실험이 같은 모양이다.
- 해시에 **플래그 키**를 넣는 이유: 넣지 않고 솔트 등 나머지 입력도 같으면 플래그 A의 20%와 플래그 B의 20%가 같은 사용자들이 된다(플래그마다 솔트가 다르면 갈린다). 두 실험이 서로를 오염시킨다.
- 비율을 올릴 때 **솔트(salt)를 바꾸지 않는** 이유: 같은 솔트면 20%일 때 켜졌던 사람은 50%에서도 켜져 있다(버킷 값이 그대로이고 기준선만 올라가서). 솔트를 바꾸면 사람들이 다시 섞인다.

### 3. 플래그 서비스 장애 — 기본값이 결정한다

- OpenFeature 명세(Flag Evaluation API) Requirement 1.4.10: 클라이언트 메서드는 예외를 던지지 않고, "비정상 실행 시 평가 호출은 기본값을 돌려준다". 1.4.8: 그때 결과에 오류 코드를 담아야 한다(MUST). 1.4.9: reason은 오류를 나타내는 것이 좋다(SHOULD — 필수는 아니다).
- 그래서 평가가 비정상으로 끝날 때의 동작은 **코드에 적힌 기본값**이 정한다. 미완성 기능 플래그의 기본값이 `true`면, 평가가 기본값으로 떨어지는 장애(예: 받아 둔 설정이 없는데 플래그 서비스가 안 됨)에서 전원에게 미완성 기능이 열린다. 마지막으로 받은 규칙이 SDK에 남아 있으면 그것으로 계속 평가할 수 있다(아래 넷째 줄).
- Hodgson의 관례: 꺼짐 = 기존 동작, 켜짐 = 새 동작. 이 관례를 지키면 "모르면 꺼라"(기본값 false)가 곧 "모르면 옛 동작"이 된다.
- 플래그 평가가 원격 호출이면 플래그 서비스가 요청 경로의 의존성이 된다. 설정을 로컬에 받아 두고 로컬에서 평가하면 그 의존성이 요청 경로에서 빠진다(원본 [08-deployment-ops](../../systems/server-design/08-deployment-ops.md) §3 "기본값 + 로컬 캐시").

### 4. 실험: 평가 일관성·비율 올리기·기본값·조합 수

```java
/** LaunchDarkly Java SDK EvaluatorBucketing과 같은 모양: sha1(flagKey.salt.userKey) 앞 15자리 → [0,1] (1은 15자리가 모두 f일 때뿐) */
static double bucket(String flagKey, String salt, String userKey) throws Exception {
    byte[] d = MessageDigest.getInstance("SHA-1").digest((flagKey + "." + salt + "." + userKey).getBytes("UTF-8"));
    String hex = HexFormat.of().formatHex(d).substring(0, 15);
    return (double) Long.parseLong(hex, 16) / 0xFFFFFFFFFFFFFFFL;
}
// (1) 요청마다 rnd.nextDouble() < 0.20  vs  bucket("new-checkout","s1",user) < 0.20 — 사용자 10,000명 × 화면 10개
// (2) 20% → 50%로 올릴 때 솔트를 그대로(s1) vs 바꿈(s2)
// (3) 플래그 A·B 각 20%: 해시에 플래그 키 없음 vs 있음
// (4) 플래그 공급자가 예외 → catch에서 코드의 기본값 사용
```

(실험, JDK 21.0.12 temurin, `--cpus=2`, 사용자 10,000명, 2026-10-01 — 무작위 부분은 시드 42 고정)

```text
(1) 요청마다 무작위 20%   → 신·구 섞어 본 사용자  8932명 (89.3%), 항상 신 UI 0명
(1) 사용자 해시 버킷 20%  → 신·구 섞어 본 사용자     0명 (0.0%), 항상 신 UI 2018명
(2) 20%→50% (솔트 s1→s1): 전 2018명 켜짐, 후 5035명 켜짐, 켜졌다 꺼진 사용자 0명
(2) 20%→50% (솔트 s1→s2): 전 2018명 켜짐, 후 4987명 켜짐, 켜졌다 꺼진 사용자 1054명
(3) 플래그 A·B 각 20%를 둘 다 받은 사용자: 키 없는 해시 1959명, 플래그 키 포함 해시 407명 (독립이면 약 400명)
(4) 플래그 서버 장애, 코드의 기본값=true  → 미완성 기능 노출 10000/10000명
(4) 플래그 서버 장애, 코드의 기본값=false → 미완성 기능 노출 0/10000명
(5) 조합 수 2^n: n=1→2 n=5→32 n=10→1,024 n=20→1,048,576 n=30→1,073,741,824
```

- 관찰 1: 요청마다 무작위로 정하면 사용자 89.3%가 화면 10개 안에서 신·구를 섞어 봤다. 계산값 1 − (0.8^10 + 0.2^10) ≈ 89.3%와 맞는다. 해시 버킷은 0명이다.
- 관찰 2: 같은 솔트로 비율을 올리면 켜졌다 꺼지는 사람이 0명이다. 솔트를 바꾸면 처음 켜졌던 2,018명 중 1,054명이 꺼졌다 — 기능을 받았다가 빼앗긴다.
- 관찰 3: 키 없는 해시(`bucket("", "", u)` — 두 플래그가 같은 값을 씀)는 A를 받은 사람이 B도 다 받는다(A를 받은 1,959명 전원 — 이 실험은 두 플래그가 같은 함수를 쓰므로 구성상 전원이다). 플래그 키를 넣으면 407명으로, 독립일 때 기대값 10,000 × 0.2 × 0.2 = 400명에 가깝다.
- 관찰 4: 공급자가 실패하면 결과는 전적으로 코드의 기본값이다. 기본값 하나가 0명과 10,000명을 가른다.
- 관찰 5: 플래그 30개면 조합이 10억 개를 넘는다. 전 조합 테스트는 불가능하다. Hodgson은 다 테스트하지 말고 (a) 출시할 운영 설정 (b) 그 플래그들을 끈 대비 설정 (c) 전부 켠 설정을 테스트하라고 권한다.

### 5. 수명 주기 — 만들 때 지울 날을 정한다

```text
 생성 ─(이름·유형·담당자·만료일 등록)─> 꺼진 채 배포 ─> 비율 출시 ─> 100% ─> 코드에서 분기 제거 ─> 설정에서 플래그 삭제
                                                                 └─ 여기서 멈추면 "제거 부채"
```

- Hodgson: 플래그는 "운반 비용이 드는 재고"다. 팀들은 플래그를 만들 때 제거 작업을 백로그에 함께 넣고, 만료일을 붙이고, 만료일이 지나면 테스트를 실패시키는 "시한폭탄"을 두고, 동시에 둘 수 있는 플래그 수에 상한을 둔다.
- 순서가 중요하다. **코드의 분기를 먼저 지우고**, 그 배포가 전 서버에 퍼진 것을 확인한 뒤 설정의 플래그를 지운다. 반대로 하면 아직 분기를 가진 서버가 "플래그 없음 → 기본값"으로 동작한다.
- 플래그 이름은 **재사용하지 않는다.** Knight는 재사용한 플래그 하나가 배포가 빠진 서버에서 옛 의미로 해석됐다.

## 쓰이는 자료구조·알고리즘

- **결정적 해시 버킷** — `hash(flagKey, salt, userId) → 0~1 사이 수`. 비율 출시·실험 집단 배정. 같은 사용자 → 같은 결과(위 실험 1). 해시 함수의 고른 분포가 비율의 정확도를 정한다(2,018명 ≈ 20%).
- **규칙 트리(첫 일치 규칙 목록)** — 조건(속성 비교)을 순서대로 평가하고 처음 맞는 결과를 쓴다. 조건은 AND/OR 트리다.
- **누적 가중치 구간** — 변형이 여러 개(A 50%·B 30%·C 20%)면 버킷 값이 [0, 0.5), [0.5, 0.8), [0.8, 1) 중 어디에 드는지로 고른다.
- **로컬 스냅숏 + 변경 구독** — 플래그 설정 전체를 메모리에 두고 변경만 받아 갱신한다. 평가는 원격 호출 없이 로컬 조회다. 받은 버전 번호를 남겨 "지금 어느 설정으로 평가했나"를 로그에 남긴다.
- **조합 폭발** — 플래그 n개 = 2^n 상태. 테스트는 대표 조합만(위 5).

## 적용 — 풀어나가는 법

### 1. 순서

1. 플래그를 만들 때 등록한다: 이름(재사용 금지), 유형(릴리스·실험·운영·권한), 담당자, 만료일, 꺼짐/켜짐의 의미(꺼짐 = 기존 동작).
2. 기본값은 "꺼짐 = 기존 동작"으로 둔다. 킬 스위치는 "켜짐 = 기능 살아 있음"이 기본인 반대 경우라 유형을 명시한다.
3. 비율 출시는 사용자(또는 테넌트) 키로 해시 버킷을 쓴다. 비율을 올릴 때 솔트를 바꾸지 않는다.
4. 평가는 로컬에서 한다. 설정 서버가 안 되면 마지막으로 받은 설정 → 그것도 없으면 코드의 기본값.
5. 100%가 되면 제거 작업을 시작한다. 분기 제거 배포 → 전 서버 버전 확인 → 설정 삭제.
6. 테스트: 운영 예정 설정 + 대비 설정(새 플래그 끔) + 전부 켬.

### 2. 평가기 (Java, 의존성 없는 최소형)

```java
record Rule(Predicate<Map<String, String>> when, boolean value) {}
record Flag(String key, String salt, boolean killed, List<Rule> rules, double rolloutPercent, boolean offValue) {}

final class FlagEvaluator {
    private volatile Map<String, Flag> snapshot = Map.of();     // 설정 서버에서 받은 마지막 스냅숏

    void update(Map<String, Flag> fresh) { snapshot = Map.copyOf(fresh); }

    /** 오류여도 예외를 던지지 않고 기본값을 돌려준다(OpenFeature 1.4.10과 같은 계약). */
    boolean isOn(String key, Map<String, String> ctx, boolean defaultValue) {
        try {
            Flag f = snapshot.get(key);
            if (f == null) return defaultValue;                  // 모르는 플래그 → 기본값 (지표로 센다)
            if (f.killed()) return f.offValue();
            for (Rule r : f.rules()) if (r.when().test(ctx)) return r.value();   // 첫 일치
            String user = ctx.get("userId");
            if (user != null && bucket(f.key(), f.salt(), user) < f.rolloutPercent() / 100.0) return true;
            return f.offValue();
        } catch (RuntimeException e) {
            return defaultValue;
        }
    }
    // bucket(...)은 「동작·원리」 4의 SHA-1 버킷
}
```

### 3. 점검 명령 (개념 예)

```bash
# 코드에 남은 플래그 참조와 등록부를 대조 — 등록부에 없거나 만료일이 지난 키
grep -rhoE 'isOn\("[a-z0-9-]+"' src/ | sort | uniq -c | sort -rn
# 배포 버전이 전 서버에 퍼졌는지 확인한 뒤에만 플래그 설정을 지운다
kubectl get pods -l app=api -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}' | sort -k2 | uniq -f1 -c
```

```promql
# reason=ERROR로 끝난 평가의 비율(지표 이름은 예시) — 모르는 키·설정 없음 같은 평가 오류를 잡는다.
# 1.4.9는 SHOULD라 SDK가 ERROR를 붙이는지 확인하고, error_code로도 센다. 캐시로 평가하면 CACHED·STALE로 나와 여기 안 잡힌다
sum(rate(flag_evaluations_total{reason="ERROR"}[5m])) / sum(rate(flag_evaluations_total[5m]))
```

## 장애 시나리오와 대처

### 1. ⚠ 재사용한 오래된 플래그가 죽은 코드를 되살린다 (Knight Capital 2012)

- 현상: 새 기능을 켰는데 서버 한 대가 전혀 다른 동작을 한다.
- 보이는 형태(원문): 새 RLP 코드는 옛 Power Peg를 켜던 플래그를 재사용했다. 8대 중 1대에 새 코드가 복사되지 않았고, 그 서버에서 플래그가 Power Peg를 켰다. 부모 주문 212건에서 자식 주문 수백만 건이 나가 약 45분 동안 약 400만 건이 체결됐다(¶13·¶15·¶16·¶17). 시장 개장 전부터 "Power Peg disabled"를 담은 자동 메일 97통이 왔지만 경보로 설계된 것이 아니어서 주의를 끌지 못했고 개장 전 조치로 이어지지 않았다(¶19).
- 원인: 플래그 이름 재사용 + 죽은 코드를 지우지 않음 + 배포 누락 + 확인 절차 부재.
- 대처: 플래그 이름은 재사용하지 않는다. 다 쓴 플래그는 분기 코드부터 지운다. 배포 뒤 전 서버 버전을 확인한다(→ 23 장애 3).

### 2. ⚠ 플래그 서버 장애 → 기본값이 "켜짐"이라 미완성 기능 전면 노출

- 현상: 플래그 서비스가 내려간 순간(SDK에 받아 둔 설정이 없어 평가가 기본값으로 떨어진 경우), 5%에만 열려 있던 기능이 전원에게 열린다.
- 보이는 형태: 평가 결과에 error_code가 붙고 reason이 ERROR로 몰린다(1.4.9는 SHOULD라 SDK에 따라). 실험 4처럼 노출 10,000/10,000.
- 원인: 평가가 비정상으로 끝나면 SDK는 코드에 적힌 기본값을 돌려준다(OpenFeature 1.4.10). 그 기본값이 `true`였다. 마지막으로 받은 설정이 남아 있으면 그것으로 평가가 이어진다.
- 대처: 기본값 = 기존 동작(false). 로컬 스냅숏으로 평가해 서비스 장애가 평가를 멈추지 않게 한다. "기본값으로 떨어진 평가 비율"에 경보를 건다.

### 3. ⚠ 요청마다 평가가 달라 한 화면에 신·구 UI가 섞인다

- 현상: 같은 사용자가 새로고침할 때마다 다른 버튼을 본다. 장바구니는 새 UI, 결제는 옛 UI.
- 보이는 형태: 실험 1처럼 무작위 평가면 화면 10개에서 89.3%가 섞어 본다. 실험 지표가 집단 간에 오염된다.
- 원인: `random() < 0.2`처럼 요청 단위로 판정했다. 또는 서버마다 다른 솔트·해시를 썼다.
- 대처: 사용자 키 기반 결정적 해시 버킷. 해시에 플래그 키를 넣는다(실험 3). 비율을 올릴 때 솔트를 유지한다(실험 2). 한 화면을 그리는 동안 평가를 한 번만 하고 결과를 요청 컨텍스트에 실어 하위 호출에 넘긴다.

### 4. ⚠ 수백 개의 방치 플래그 → 조합 테스트 불가

- 현상: 어떤 플래그 조합이 운영에 있는지 아무도 모른다. 버그가 "특정 조합에서만" 난다.
- 보이는 형태: 코드에 `isOn(` 호출이 수백 개, 등록부와 맞지 않는 키, 만료일 지난 플래그. 조합은 2^n(실험 5).
- 원인: 만들 때 제거 계획이 없었다. 릴리스 플래그를 1~2주 넘게 뒀다.
- 대처: 등록부(유형·담당자·만료일), 만료 테스트("시한폭탄"), 플래그 수 상한, 정기 정리. 테스트는 운영 설정·대비 설정·전부 켬 세 가지로 묶는다.

### 5. 플래그를 설정에서 먼저 지워 일부 서버가 기본값으로 돈다

- 현상: 플래그 정리 직후 일부 사용자에게서 옛 동작이 다시 보인다.
- 보이는 형태: "unknown flag" 경고, reason=ERROR(FLAG_NOT_FOUND 류) 평가가 특정 파드에서만.
- 원인: 분기 제거 배포가 아직 다 퍼지지 않았는데 설정을 지웠다. 남은 서버는 기본값(옛 동작)으로 평가한다.
- 대처: 분기 제거 배포 → 전 서버 버전 확인 → 설정 삭제 순서를 지킨다. "모르는 플래그 평가" 지표를 본다.

## 핵심 문장

- 피처 플래그는 배포와 릴리스를 떼어 내어, 기능을 재배포 없이 켜고 끈다. 대신 플래그 하나마다 코드 경로가 둘씩 늘어난다.
- 유형(릴리스·실험·운영·권한)마다 수명과 관리 방식이 다르다. 릴리스 플래그는 보통 1~2주 안에 지운다(제품 쪽 출시 플래그는 더 길 수 있다).
- 비율 출시는 사용자 키의 결정적 해시로 한다. 실험에서 요청 단위 무작위는 89.3%에게 신·구를 섞어 보였고, 해시 버킷은 0명이었다.
- 평가가 실패하면 SDK는 코드의 기본값을 돌려준다. 기본값은 "꺼짐 = 기존 동작"으로 둔다.
- 플래그는 재사용하지 않고, 분기 코드를 먼저 지운 뒤 설정을 지운다. Knight Capital은 재사용한 플래그 하나가 배포가 빠진 서버에서 2003년 이후 쓰지 않던 코드를 켰다.

## 관련 주제·근거

- 선행
  - [23-deployment-strategies](../23-deployment-strategies/2-summary.md) — 배포·카나리·롤백
  - engineering-practice/04-branching-strategies — [../../engineering-practice/README.md](../../engineering-practice/README.md)(이 노트 작성 시점 미작성. 트렁크 기반 개발에서 미완성 코드를 플래그로 숨기는 것과 이어진다)
  - 원본 [systems/server-design/08-deployment-ops.md](../../systems/server-design/08-deployment-ops.md) §3 "피처 플래그 운영"(부채·기본값+로컬 캐시·킬 스위치)
- 후속·연결
  - engineering-practice/20-practice-incidents — [../../engineering-practice/README.md](../../engineering-practice/README.md)(이 노트 작성 시점 미작성) · [software-design/54-designing-for-deletion](../../software-design/54-designing-for-deletion/2-summary.md)
  - [10-circuit-breaker](../10-circuit-breaker/2-summary.md) — 킬 스위치 = 수동 서킷 브레이커
  - [12-backpressure-and-load-shedding](../12-backpressure-and-load-shedding/2-summary.md) — 부하 때 기능 끄기
  - [51-cells-stamps-and-blast-radius](../51-cells-stamps-and-blast-radius/2-summary.md) — 셀 단위로 켜기
- 문서·글·소스
  - Hodgson, "Feature Toggles (aka Feature Flags)", martinfowler.com, 2016-01~02 연재(완결 2016-02-08), 마지막 개정 2017-10-09 — 유형 4종, 수명·동적성, 일관된 집단, 운반 비용·만료일·시한폭탄·상한, 테스트할 조합 <https://martinfowler.com/articles/feature-toggles.html>
  - OpenFeature Specification, Flag Evaluation API — Requirement 1.4.8·1.4.9·1.4.10(오류 시 기본값) <https://openfeature.dev/specification/sections/flag-evaluation>
  - launchdarkly/java-server-sdk `src/main/java/com/launchdarkly/sdk/server/EvaluatorBucketing.java` — SHA-1 버킷(2026-10-01 main 열람)
  - SEC 행정 명령 Release No. 34-70694 (Knight Capital Americas LLC), 2013-10-16 — ¶12~¶19, ¶27 <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>
- 실험 목록
  - E24: 사용자 10,000명 — (1) 요청 단위 무작위 vs 해시 버킷 일관성 (2) 솔트 유지/변경 시 비율 올리기 (3) 해시에 플래그 키 유무 (4) 공급자 장애 시 기본값 (5) 2^n. JDK 21.0.12, 코드 scratchpad `rel/23/e24/FlagExp.java`, `docker run --rm --cpus=2 eclipse-temurin:21-jdk java FlagExp.java`
