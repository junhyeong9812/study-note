# reliability/23-deployment-strategies — 배포 전략: 롤링·블루그린·카나리·피처 플래그·롤백 — 정리 (힌트)

## 해결하는 문제

서비스를 고치려면 새 버전을 운영에 올려야 한다. 그런데 운영 중인 시스템을 바꾸는 순간이 사고가 가장 많이 나는 순간이다.\
Google SRE 책 1장은 "장애의 약 70%가 운영 중인 시스템의 변경에서 나온다"고 적는다. 그래서 같은 장이 권하는 세 가지가 **점진 배포 · 빠르고 정확한 문제 탐지 · 안전한 롤백**이다.

```text
 한 번에 전부 바꾸기                          나눠서 바꾸고, 보고, 되돌릴 수 있게
 v1 v1 v1 v1  ──(배포)──> v2 v2 v2 v2          v1 v1 v1 v1 → v2 v1 v1 v1 → (지표 확인) → v2 v2 v1 v1 → …
 버그가 있으면 사용자 100%가 맞는다            버그가 있으면 맞는 사용자가 일부이고, 그 사이에 멈춘다
```

- *배포(deployment)*: 새 코드를 서버에 올려 실행하는 일.
- *릴리스(release)*: 사용자가 새 기능을 실제로 보게 하는 일. 피처 플래그를 쓰면 배포와 릴리스를 떼어 낼 수 있다(→ [24-feature-flag-lifecycle](../24-feature-flag-lifecycle/2-summary.md)).
- *롤백(rollback)*: 직전 버전으로 되돌리는 일.

쉬운 예: 식당이 메뉴판과 주방 레시피를 바꾼다.
- 전국 지점을 하룻밤에 바꾸면, 레시피가 틀렸을 때 전국 손님이 같은 날 불만을 낸다.
- 한 지점에서 먼저 바꿔 보고(카나리), 문제가 없으면 지점을 늘린다(롤링).
- 그런데 "주문은 새 메뉴판으로 받고 조리는 옛 레시피 주방에서" 하는 순간이 생기면, 바꾸는 도중에만 엉뚱한 요리가 나간다. 이것이 **신·구 버전 공존** 문제다.

똑같은 구조다.\
실무 예: Kubernetes Deployment의 롤링 업데이트, 로드 밸런서 가중치로 하는 카나리, DNS·라우터 전환으로 하는 블루그린.\
기초(네 전략 표·Expand-Contract·롤백 수단별 복구 시간)는 원본 [systems/server-design/08-deployment-ops.md](../../systems/server-design/08-deployment-ops.md) §1~§3에 있다. 이 노트는 공존 구간에서 실제로 무엇이 깨지는지를 실험으로 보고, 롤백이 안 되는 변경과 판정 방법을 채운다.

## 동작·원리

### 1. 네 가지 전략 — 시간축 그림

```text
 인스턴스 4대, 시간은 → 방향

 재생성(Recreate)   v1 v1 v1 v1 | (전부 내림 — 서비스 공백) | v2 v2 v2 v2
 롤링(Rolling)      v1 v1 v1 v1 → v2 v1 v1 v1 → v2 v2 v1 v1 → v2 v2 v2 v1 → v2 v2 v2 v2
                                 └──────────── 신·구 공존 구간 ────────────┘
 블루그린           [파랑 v1 ×4 ← 트래픽]   [초록 v2 ×4 대기]
                     라우터 한 번 전환 ─────────> [초록 v2 ← 트래픽]   [파랑 v1 대기 = 롤백 자리]
 카나리             v1 ×N 이 95%, v2 소수가 5% ─(지표 비교)─> 10% → 50% → 100%  (나쁘면 0%로)
```

- *롤링 업데이트*: 인스턴스를 몇 대씩 차례로 새 버전으로 바꾼다. 추가 자원이 적다. 대신 공존 구간이 길다.
- *블루그린(blue/green)*: 같은 크기의 환경 두 벌을 두고 라우터를 한 번에 넘긴다. 롤백은 라우터를 되돌리는 것이다(Fowler 2010 "BlueGreenDeployment"). 자원이 두 배 든다(SRE Workbook 16장).
- *카나리(canary)*: 일부 트래픽만 새 버전에 보내고, 나머지(control)와 지표를 비교해 진행 여부를 정한다. Workbook 16장의 정의는 "변경을 일부에, 시간 제한을 두고 배포해 평가하는 것"이다.
- *재생성(Recreate)*: 다 내리고 다 올린다. 공존은 없지만 공백이 있다.

### 2. Kubernetes Deployment에서의 롤링 (문서 기준)

| 항목 | 기본값·동작 (Kubernetes Deployment 문서, 2026-10-01 열람) |
|---|---|
| `.spec.strategy.type` | `RollingUpdate`가 기본, 다른 값은 `Recreate` |
| `maxUnavailable` | 25%(내림). 갱신 중 원하는 수의 75% 이상이 떠 있다 |
| `maxSurge` | 25%(올림). 갱신 중 원하는 수 + ⌈25%⌉개까지 뜬다. 올림이라 복제본이 적으면 125%를 넘는다(예: 3개 → 최대 4개 = 133%) |
| `progressDeadlineSeconds` | 600. 넘으면 상태에 `ProgressDeadlineExceeded`를 **적기만** 한다. 자동 롤백은 하지 않는다 |
| `revisionHistoryLimit` | 10. 0으로 두면 `kubectl rollout undo`로 되돌릴 수 없다 |

- 문서는 "Kubernetes takes no action on a stalled Deployment other than to report a status condition"이라고 적는다. 멈춘 배포를 되돌리는 것은 그 위의 도구(파이프라인·Argo Rollouts 같은 것)나 사람의 일이다.
- 롤링은 **새 파드가 가용(available)한지**만 본다. 가용 = 준비(readiness) 상태를 `minReadySeconds`(기본 0초) 동안 유지한 것이다(같은 문서). 새 버전이 오류를 내도 준비 검사를 통과하면 계속 진행한다. 그래서 오류율 판정은 별도로 붙여야 한다.

### 3. 공존 구간에서 무엇이 깨지나 — 두 요청 흐름

Workbook 16장이 짚는 경우다. "한 클라이언트의 연속된 두 요청 중 첫 요청은 카나리가, 둘째 요청은 control이 받을 수 있다. 카나리의 응답이 둘째 요청의 내용을 바꾼다."

```text
 사용자  ── ① GET /form ──> LB ──> v2 인스턴스: 토큰 "v2|17" 발급 (새 형식)
        ── ② POST /submit?token=v2|17 ──> LB ──> v1 인스턴스: "v2|"를 모름 → 400
                                       (②가 v2에 가면 성공)
```

- 새 버전 비율이 p일 때 두 요청이 서로 다른 버전에 갈 확률은 2·p·(1−p)다(로드 밸런서가 요청마다 독립적으로 고른다고 가정).
  - p = 5% → 9.5%, p = 25% → 37.5%, p = 50% → 50%.
- 같은 모양으로 깨지는 것: 캐시에 쓴 새 형식 값, 큐에 넣은 새 스키마 메시지, 세션·쿠키 형식, DB의 새 컬럼 의미.
- 해결은 버전을 두 번에 나누는 것이다.
  1. **확장 배포**: 새 형식을 *읽을 줄만* 알고, 쓰기는 여전히 옛 형식으로 한다.
  2. 그 배포가 100%가 된 뒤 **전환 배포**: 새 형식으로 쓰기 시작한다. 이제 돌고 있는 인스턴스는 전부 새 형식을 읽을 줄 안다.
  - DB 스키마에서는 이것이 expand/contract다 — [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) 「동작·원리」 4절.

### 4. 실험: 롤링·블루그린·카나리, 그리고 확장 배포

- 구성: nginx(로드 밸런서) + Node 인스턴스 4대. nginx 업스트림 설정을 바꾸고 `nginx -s reload`로 전환한다.
- 사용자 8명이 ①→② 흐름을 계속 반복한다. 0.5초마다 성공(ok)·토큰 거절(badToken)·네트워크 오류(netErr)를 센다.
- 버전 세 가지
  - `v1`: `v1:<n>`을 쓰고 v1만 읽는다.
  - `v2`: `v2|<n>`을 쓰고 v2만 읽는다(비호환 변경을 한 번에).
  - `v2read`: v1 형식을 쓰고 v1·v2를 둘 다 읽는다(확장 배포).

```js
// server.js 핵심 — 인스턴스 = (쓰기 형식, 읽을 수 있는 형식)
const KINDS = {
  v1:     { write: n => `v1:${n}`, reads: t => t.startsWith('v1:') },
  v2:     { write: n => `v2|${n}`, reads: t => t.startsWith('v2|') },
  v2read: { write: n => `v1:${n}`, reads: t => t.startsWith('v1:') || t.startsWith('v2|') },
};
// /form → k.write(++seq),  /submit?token=… → k.reads(token) ? 200 : 400
```

(실험, nginx 1.31.1(nginx:alpine) + Node 22.23.2, 각 컨테이너 `--cpus=1`, 동시 사용자 8명, 2026-10-01 — 처리량은 실행마다 다르다)

롤링(비호환 v2) — `##` 줄은 업스트림 교체 시각이고, 나머지 줄은 그 시각까지 0.5초 동안의 수다.

```text
## 06:09:27.063 업스트림 = 9001 8002 8003 8004
## 06:09:29.200 업스트림 = 9001 9002 8003 8004
## 06:09:31.369 업스트림 = 9001 9002 9003 8004
## 06:09:33.562 업스트림 = 9001 9002 9003 9004
06:09:26.653 ok=104 badToken=0 5xx=0 netErr=0
06:09:27.153 ok=152 badToken=0 5xx=0 netErr=0
06:09:27.654 ok=65 badToken=33 5xx=0 netErr=6
06:09:28.160 ok=109 badToken=60 5xx=0 netErr=0
06:09:29.662 ok=99 badToken=84 5xx=0 netErr=4
06:09:31.240 ok=201 badToken=135 5xx=0 netErr=0
06:09:33.745 ok=134 badToken=93 5xx=0 netErr=7
06:09:34.246 ok=213 badToken=0 5xx=0 netErr=0
06:09:34.747 ok=369 badToken=0 5xx=0 netErr=0
TOTAL {"ok":4437,"badToken":1048,"http5xx":0,"netErr":24}
```

(출력은 길어서 일부 줄만 옮겼다. 전체는 scratchpad `e23/out-rolling.txt`)

네 실행의 합계

```text
rolling        TOTAL {"ok":4437,"badToken":1048,"http5xx":0,"netErr":24}
bluegreen      TOTAL {"ok":4993,"badToken":5,"http5xx":0,"netErr":4}
rolling-compat TOTAL {"ok":4332,"badToken":0,"http5xx":0,"netErr":18}
canary         TOTAL {"ok":4940,"badToken":176,"http5xx":0,"netErr":13}
```

- 재실행(같은 코드·같은 제한, nginx 1.31.6·Node 22.23.2, 2026-10-01): rolling badToken 1,404 · bluegreen 5 · rolling-compat 0 · canary 237(카나리 구간 237/2,594 = 9.1%). 처리량과 건수는 실행마다 다르지만 순서와 비율은 같았다.

- 관찰 1 — 롤링: badToken이 **공존 구간에만** 나온다. 첫 교체 전과, 마지막 교체(33.562)를 걸친 집계 줄(33.745, 93건) 뒤의 줄에서는 0이다. 걸친 줄의 93건이 교체 앞뒤 어느 쪽인지는 이 집계로 가를 수 없다. 단계별 거절 비율은 약 34%·44%·38%로, 이론값 37.5%·50%·37.5%에 가깝다(0.5초 집계 구간이 단계 경계와 겹쳐 섞인다). 같은 조건 재실행에서는 약 37%·51%·40%였다(실행마다 다르다).
- 관찰 2 — 블루그린: 거절 5건. 전환 순간 ①과 ② 사이에 걸친 흐름만 깨졌다. 공존 시간이 거의 0이라서다.
- 관찰 3 — 카나리 5%(가중치 76:4): 카나리 구간 거절 174건 / 흐름 1,798건 = 9.7%. 이론값 2·0.05·0.95 = 9.5%와 맞는다. 카나리 비율보다 피해 비율이 **두 배쯤** 크다 — 흐름이 두 요청이라서다. 철회(롤백) 뒤에는 0이다.
- 관찰 4 — 확장 배포(`v2read`)로 롤링: 거절 0. 같은 롤링인데 버전 쌍이 서로를 읽을 수 있으니 공존이 문제가 되지 않는다.
- 관찰 5 — netErr: 네 시나리오 다 `nginx -s reload` 직후마다 몇 건씩 나왔다. 원인은 `UND_ERR_SOCKET`(Node fetch의 소켓 닫힘)이었다(재실행 네 시나리오의 netErr 1~16건이 모두 이 코드).
  - nginx 문서(Controlling nginx)는 reload 때 옛 워커가 "listen 소켓을 닫고 옛 클라이언트를 마저 처리한 뒤 끝난다"고 적는다.
  - 해석: 옛 워커가 끝나며 닫은 keep-alive 연결에, 클라이언트가 같은 순간 다음 요청을 실어 보내 실패한 것으로 보인다. 프록시 전환도 연결 수준의 작은 실패를 낸다. 멱등 요청은 재시도로 덮는다.

### 5. 롤백이 되는 변경과 안 되는 변경

```text
 되돌리기 쉬움                                    되돌리기 어렵거나 불가
 ─ 코드만 바뀜, 데이터 형식 그대로                  ─ 새 형식으로 이미 쓴 데이터(캐시·큐·DB)
 ─ 새 형식을 읽기만 하는 확장 배포                  ─ 컬럼·테이블 삭제, 의미를 바꾼 UPDATE
 ─ 플래그 뒤에 숨긴 기능                           ─ 외부로 나간 부수 효과(메일·결제·주문)
```

- 롤백은 **코드**를 되돌린다. 데이터와 바깥 세상은 되돌리지 않는다. 그래서 위험한 변경은 "옛 버전이 새 버전이 남긴 상태를 읽을 수 있나"로 판정한다.
- 롤백 자체도 변경이다. Knight Capital(2012-08-01) 사고에서 회사는 문제를 고치려고 정상 배포된 7대에서 새 코드를 **제거했다**. 그러자 그 7대에서도 옛 Power Peg 코드가 켜져 문제가 커졌다(SEC 명령 34-70694 ¶27).

### 6. 카나리 판정 — 무엇과 비교하나

- 비교 대상은 **같은 시각의 control**이다. 배포 전후를 비교(before/after)하면 시간대·요일 차이가 섞인다. Workbook 16장은 이것을 "시간으로 나눈 카나리"라 부르고 위험하다고 적는다.
- 지표는 사용자가 느끼는 것부터 고른다(오류율·지연). Workbook은 SLI에서 시작하고, 상위 몇 개("perhaps no more than a dozen", 많아야 십여 개)로 줄이라고 권한다.
- 에러 버짓 계산: 결함이 요청 20%를 실패시키는 버전을 전체에 내면 20% 실패다. 5% 카나리면 전체 실패는 1%다(Workbook 16장 예). 버짓 소모는 노출된 트래픽에 비례한다.
- 단, 위 실험처럼 흐름이 여러 요청이면 피해 비율은 카나리 비율보다 클 수 있다.

## 쓰이는 자료구조·알고리즘

- **가중 라운드로빈** — 업스트림마다 weight를 주고 비율대로 나눈다. nginx 업스트림 문서: 기본 분배 방식이 "weighted round-robin"이고 weight 기본값은 1이다. 실험의 카나리 5%는 76:4다.
- **사용자 해시 버킷** — 요청이 아니라 사용자를 기준으로 비율을 고정한다. 그러면 한 사용자는 한 버전만 본다(위 2·p·(1−p) 문제를 사용자 단위에서 없앤다). 구현은 [24-feature-flag-lifecycle](../24-feature-flag-lifecycle/2-summary.md) 「쓰이는 자료구조·알고리즘」.
- **단계 상태 기계** — 배포 단계 = `카나리 5% → 25% → 50% → 100%`. 단계마다 판정(진행·정지·되돌림). Kubernetes는 `Progressing`·`ProgressDeadlineExceeded` 같은 상태 조건을 남긴다.
- **두 표본 비교** — 카나리와 control의 오류 비율 차이를 본다. 표본이 작으면 차이가 우연일 수 있다(Workbook: 크기·기간·트래픽 양이 대표성을 정한다).
- **버전 관대한 읽기(tolerant reader)** — 둘 이상의 형식을 받아들이는 파서. 확장 배포의 핵심이다.

## 적용 — 풀어나가는 법

### 1. 순서

1. 변경을 분류한다. 코드만인가, 데이터 형식·스키마·메시지가 바뀌나, 외부 부수 효과가 있나.
2. 형식이 바뀌면 배포를 둘로 쪼갠다. 읽기 확장 → 100% → 쓰기 전환. 옛 형식 읽기 제거는 그다음 배포다.
3. 전략을 고른다.
   - 상태 없는 서비스·호환 변경: 롤링 + 카나리 판정.
   - 공존이 곤란한 변경이고 자원 두 벌이 가능: 블루그린.
   - 기능 단위로 끄고 켤 필요: 피처 플래그(→ 24).
4. 판정 지표와 중단 기준을 **배포 전에** 적는다(버전 레이블별 오류율·p99).
5. 롤백 경로를 확인한다. `revisionHistoryLimit`이 0이 아닌가, 옛 버전이 새 데이터를 읽나.
6. 단계마다 기다리고 본다. 단계 시간은 작업 단위 처리 시간보다 길게 잡는다(Workbook: 비대화형 파이프라인은 작업 하나가 길다).

### 2. 확장 배포 코드 (Java)

```java
/** 확장 단계: 두 형식을 다 읽고, 쓰기는 옛 형식 그대로. 전환 단계에서 write만 바꾼다. */
final class TokenCodec {
    private final boolean writeV2;                        // 전환 배포에서 true (설정·플래그로)
    TokenCodec(boolean writeV2) { this.writeV2 = writeV2; }

    String write(long n) { return writeV2 ? "v2|" + n : "v1:" + n; }

    long read(String token) {
        if (token.startsWith("v1:")) return Long.parseLong(token.substring(3));
        if (token.startsWith("v2|")) return Long.parseLong(token.substring(3));
        throw new IllegalArgumentException("unknown token format: " + token);
    }
}
```

### 3. 진단·조작 명령

```bash
# Kubernetes: 진행 상황, 멈춤, 되돌림
kubectl rollout status deployment/api          # 끝나면 종료 코드 0
kubectl rollout pause deployment/api           # 다음 단계로 가지 않게 멈춤
kubectl rollout undo deployment/api            # 직전 리비전으로
kubectl rollout history deployment/api

# nginx 카나리: 가중치로 5%
#   upstream app { server v1-a weight=19; server v1-b weight=19; server v1-c weight=19; server v1-d weight=19; server v2-a weight=4; }
nginx -t && nginx -s reload
```

```promql
# 버전별 5xx 비율 — 카나리(version="v2")와 control(version="v1")을 같은 시각에 비교
sum by (version) (rate(http_requests_total{code=~"5.."}[5m]))
  / sum by (version) (rate(http_requests_total[5m]))
```

## 장애 시나리오와 대처

### 1. ⚠ 배포 중에만 에러가 난다 (신·구 비호환)

- 현상: 배포를 시작하면 4xx·5xx가 오르고, 배포가 끝나면 저절로 사라진다. 롤백해도 롤백하는 동안 또 오른다.
- 보이는 형태: 위 실험의 badToken처럼 "모르는 형식", 역직렬화 예외(`UnrecognizedPropertyException` 류), 컨슈머의 스키마 오류. 버전 레이블별로 쪼개 보면, 양방향 비호환(이 실험의 v1↔v2)이면 양쪽 버전 모두, 한 방향만 비호환이면 못 읽는 쪽 버전만 오류를 낸다.
- 원인: 새 버전이 쓴 것을 옛 버전이 못 읽는다(또는 반대). 공존 구간에서 요청·메시지가 두 버전을 오간다.
- 대처: 확장 배포(읽기 먼저) → 쓰기 전환으로 쪼갠다. 메시지 스키마는 하위·상위 호환 규칙을 정한다. 급하면 블루그린으로 공존 시간을 줄인다(실험: 1,048건 → 5건).

### 2. ⚠ 롤백할 수 없는 변경

- 현상: 새 버전에 버그가 있어 되돌렸는데, 옛 버전이 오류를 낸다.
- 보이는 형태: 옛 버전 로그에 "column does not exist", 캐시·큐의 새 형식 값을 못 읽는 예외.
- 원인: 새 버전이 컬럼을 지웠거나 새 형식 데이터를 이미 썼다. 롤백은 코드만 되돌린다.
- 대처: 파괴적 스키마 변경은 마지막 배포로 미룬다(expand/contract, [database/26-schema-migration](../../database/26-schema-migration/2-summary.md)). 되돌릴 수 없는 단계 앞에서는 "앞으로 고치기(forward-fix)" 계획과 플래그 끄기 경로를 미리 둔다.

### 3. 일부 서버에만 배포가 안 됐다

- 현상: 대부분의 서버는 정상인데 한 대에서만 이상 동작이 난다.
- 보이는 형태: 버전 레이블이 하나만 다르다. Knight Capital은 8대 중 1대에 새 코드를 복사하지 않았다. 재사용한 플래그가 그 1대에서 옛 Power Peg 코드를 켰고, 약 45분 동안 약 400만 건이 체결됐고 손실은 4억 6천만 달러가 넘었다(SEC 명령 ¶15·¶16·¶17).
- 원인: 수작업 배포, 2차 확인 부재(같은 명령 ¶15·¶26: "second technician" 검토 절차 없음).
- 대처: 배포를 자동화하고, 끝난 뒤 전 서버의 실행 버전을 조회해 맞춘다. 버전 혼재를 경보로 둔다. 플래그 재사용 금지는 24에서 다룬다.

### 4. 전환 순간의 연결 끊김

- 현상: 블루그린 전환이나 프록시 설정 reload 직후 짧게 연결 오류가 튄다.
- 보이는 형태: 실험의 netErr(`UND_ERR_SOCKET`), "connection reset", "socket hang up". 한 번 튀고 사라진다.
- 원인(해석): 옛 워커·옛 인스턴스가 keep-alive 연결을 닫는 순간에 보낸 요청이 실패한다.
- 대처: 멱등 요청은 클라이언트에서 한 번 재시도한다. 옛 인스턴스는 바로 죽이지 말고 드레이닝([14-graceful-shutdown](../14-graceful-shutdown/2-summary.md)).

### 5. 카나리가 통과했는데 전체 배포에서 터진다

- 현상: 카나리 단계는 지표가 멀쩡했는데 100%에서 지연이 폭증한다.
- 보이는 형태: 카나리 기간이 짧았거나 트래픽이 적은 시간이었다. 비교가 before/after였다.
- 원인: 표본이 대표적이지 않다. 성능 결함은 부하가 높을 때만 나온다(Workbook 16장 "Time of day").
- 대처: 단계를 여러 개로 나누고 단계마다 지표를 늘린다(작은 단계는 크래시·오류, 큰 단계는 지연·자원). control과 같은 시각에 비교한다.

## 핵심 문장

- 배포 전략은 "한 번에 얼마나 많은 사용자를 새 코드에 노출하나"와 "얼마나 빨리 되돌리나"를 정하는 일이다.
- 롤링·카나리에는 신·구 공존 구간이 있다. 실험에서 비호환 변경을 롤링하자 거절이 공존 구간에만 1,048건 났고, 확장 배포(읽기 먼저)로는 0건이었다.
- 두 요청 흐름은 새 버전 비율 p에서 2·p·(1−p) 확률로 버전을 넘나든다. 5% 카나리의 피해는 약 9.5%다.
- 롤백은 코드만 되돌린다. 새 형식 데이터·삭제한 컬럼·외부 부수 효과는 남는다.
- Kubernetes 롤링은 준비(가용) 여부만 보고, 멈춘 배포를 자동으로 되돌리지 않는다. 판정과 롤백은 위에 붙여야 한다.

## 관련 주제·근거

- 선행
  - [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md) — 준비 해제·드레이닝 뒤 종료
  - 원본 [systems/server-design/08-deployment-ops.md](../../systems/server-design/08-deployment-ops.md) §1 무중단 배포 전략, §2 Expand-Contract, §3 롤백 가능성. 참고: 원본 §1 표의 블루그린 장점 "공존 시간 짧음"은 맞지만, 전환 순간에 걸친 흐름과 연결은 깨질 수 있다(위 실험 bluegreen: badToken 5·netErr 4).
- 후속·연결
  - [24-feature-flag-lifecycle](../24-feature-flag-lifecycle/2-summary.md) — 배포와 릴리스 분리, 해시 버킷
  - [51-cells-stamps-and-blast-radius](../51-cells-stamps-and-blast-radius/2-summary.md) — 셀 단위 배포 웨이브
  - [26-incident-response-and-postmortem](../26-incident-response-and-postmortem/2-summary.md) — 완화로서의 롤백
  - [02-slo-sli-error-budget](../02-slo-sli-error-budget/2-summary.md) — 카나리의 버짓 소모
  - [database/26-schema-migration](../../database/26-schema-migration/2-summary.md) — expand/contract·백필
- 문서·글
  - Google SRE 책 1장 Introduction "Change Management"(장애의 약 70%가 변경), 8장 Release Engineering <https://sre.google/sre-book/release-engineering/>
  - Google SRE Workbook 16장 "Canarying Releases"(정의, 5%·20% 예, before/after 위험, 두 요청 상호작용, blue/green) <https://sre.google/workbook/canarying-releases/>
  - Fowler, "BlueGreenDeployment", 2010-03-01 <https://martinfowler.com/bliki/BlueGreenDeployment.html> · "CanaryRelease"(Sato), 2014-06-25 <https://martinfowler.com/bliki/CanaryRelease.html>
  - Kubernetes 문서 "Deployments"(maxSurge·maxUnavailable 25%, progressDeadlineSeconds 600, revisionHistoryLimit 10, rollout undo) <https://kubernetes.io/docs/concepts/workloads/controllers/deployment/>
  - nginx 문서 "Controlling nginx"(reload와 옛 워커), `ngx_http_upstream_module`(weighted round-robin, weight 기본 1)
  - SEC 행정 명령 Release No. 34-70694, In the Matter of Knight Capital Americas LLC, 2013-10-16 — ¶12~¶17, ¶26, ¶27 <https://www.sec.gov/litigation/admin/2013/34-70694.pdf>
- 실험 목록
  - E23: nginx + Node 인스턴스 4대, 두 요청 흐름 8명 — 롤링(비호환)·블루그린·롤링(확장 배포)·카나리 5% 비교. 코드 scratchpad `rel/23/e23/{server.js,client.js,run23.sh}`, 일회용 컨테이너 `sn-rl-w23-{app,lb,cli}`
