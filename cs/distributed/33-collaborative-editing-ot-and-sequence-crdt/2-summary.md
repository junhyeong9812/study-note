# distributed/33-collaborative-editing-ot-and-sequence-crdt — 실시간 공동 편집: OT vs 시퀀스 CRDT — 정리 (힌트)

## 해결하는 문제

여러 사람이 같은 문서를 동시에 고친다. 각자 화면에서는 입력이 즉시 보여야 하고(지연 없이), 결국 모두 같은 문서를 봐야 한다.

```text
  공통 문서 "abcd"
  사용자 1: 2번 위치에 X 삽입 → "abXcd"     (내 화면에 즉시)
  사용자 2: 2번 위치에 Y 삽입 → "abYcd"     (내 화면에 즉시)
  서로의 연산을 그대로 적용하면:
     사용자 1: "abXcd" + ins(2,Y) → "abYXcd"
     사용자 2: "abYcd" + ins(2,X) → "abXYcd"      ← 다른 문서. 발산
```

- 위치(정수 인덱스)는 상대 연산이 끼어들면 뜻이 바뀐다. 그래서 두 가지 길이 생겼다.
  - *OT(Operational Transformation)*: 받은 연산의 위치를 이미 적용한 연산에 맞춰 **변환**한다.
  - *시퀀스 CRDT*: 정수 위치 대신 글자마다 **바뀌지 않는 고유 id**를 붙이고, id 사이의 순서 규칙으로 정렬한다.
- 수렴만으로는 부족하다. 사용자 의도가 보존되고 읽을 수 있어야 한다(끼워짐 문제, 장애 2).

쉬운 예: 두 사람이 같은 회의록 종이를 복사해 각자 쓰고 나중에 합친다.
- "3번째 줄에 넣었다"는 메모는 다른 사람이 위에 줄을 넣으면 틀린 위치가 된다(OT가 고치는 것).
- "'안건' 다음 줄에 넣었다"고 쓰면 위에 무엇이 들어와도 위치가 안 변한다(CRDT의 생각).

똑같은 구조다.\
OT는 "몇 번째"를 계속 고쳐 주고, CRDT는 처음부터 "무엇 다음"으로 적는다.

실무 예:
- Google Docs·Google Wave: 중앙 서버 기반 OT(Wave 백서: Jupiter 시스템 방식).
- Figma: 중앙 서버 + CRDT에서 영감을 받은 속성별 LWW. 같은 텍스트 값을 동시에 고치면 글자 단위로 합치지 않고 한쪽 값만 남는다(블로그 2019-10-16 기준).
- Yjs·Automerge 같은 라이브러리: 오프라인·P2P에서도 병합되는 시퀀스 CRDT.

## 동작·원리

### 1. OT — 위치를 변환한다

```text
  변환 T(a, b): "b가 먼저 적용된 문서에서 a가 같은 의도를 내려면?"

  ins(p1) vs ins(p2):  p1 < p2 → 그대로        p1 > p2 → p1 + 1
                       p1 = p2 → 동률! 사이트 우선순위로 한쪽만 +1
  ins vs del(p2):      p1 ≤ p2 → 그대로        p1 > p2 → p1 − 1
  del vs del:          같은 글자면 → 아무것도 안 함(no-op)

  사이트 1: "abXcd" ──T(ins(2,Y), ins(2,X))=ins(3,Y)──> "abXYcd"
  사이트 2: "abYcd" ──T(ins(2,X), ins(2,Y))=ins(2,X)──> "abXYcd"     ← 수렴
```

- 수렴에 필요한 성질(Wikipedia "Operational transformation"이 정리한 이름)
  - *TP1(CP1)*: `a ∘ T(b, a) ≡ b ∘ T(a, b)`. 두 연산을 어느 순서로 적용해도 같은 문서. 두 연산이 다른 순서로 실행될 수 있는 시스템이면 필요하다.
  - *TP2(CP2)*: 세 연산에서, 변환 경로가 달라도 같은 연산이 나와야 한다. 같은 연산을 서로 다른 문맥에서 변환할 수 있는 시스템이면 필요하다.
- 역사: Ellis–Gibbs(SIGMOD 1989)가 GROVE 편집기에서 처음 제안했다. 상태 벡터로 선후(precedence)를 판정하고 우선순위로 동률을 깼다. 몇 년 뒤 정확성 문제가 발견되어 여러 수정안이 나왔다(Ressel 1996, Sun–Ellis 1998 등).
- **중앙 서버로 단순화**(Google Wave 백서)
  - 클라이언트는 서버가 이전 연산을 확인(ack)해 줄 때까지 다음 연산을 보내지 않고 모아 둔다.
  - 그러면 클라이언트는 서버의 변환 경로를 추론할 수 있고, 서버는 들어온 연산을 자기 기록에 맞춰 변환·적용·방송하면 된다.
  - 출발점은 Jupiter(Nichols 외 1995)의 클라이언트-서버 OT다. 확인(ack) 대기는 Wave가 Jupiter 위에 더한 변형이다(백서: "Wave OT modifies the basic theory of OT by requiring the client to wait for acknowledgement").
  - Wikipedia OT 비교표는 Jupiter(중앙 변환 서버)와 Wave(중앙 변환 서버 + stop'n'wait 전파)를 "제어 알고리즘이 TP2를 맡고, 변환 함수는 TP1만 만족하면 되는" 방식으로 분류한다. 변환 함수 설계가 훨씬 쉬워진다.
- Figma 블로그의 평가: OT는 "긴 텍스트를 적은 메모리로 편집"하기 좋지만 구현이 어렵고 상태 조합이 폭발한다.

### 2. 시퀀스 CRDT — 글자마다 고유 id

```text
  RGA류(직전 글자를 기준으로)                    분수 위치류(Logoot·LSEQ 계열)
  글자 = (id=(램포트, 사이트), 왼쪽 기준 id)        글자 = (두 이웃 사이의 위치 값, 사이트)
                                                  정렬 = 위치 값 순
  root ─ H ─ i ─┬─ " Alice"   (A의 글자들)
                ├─ " Bob"     (B의 글자들)       동시 삽입 시 각자 고른 위치 값이 뒤섞이면
                └─ "!"                          글자 단위로 끼워짐(interleaving)
  같은 기준의 형제는 id 큰 쪽이 앞 → 트리를 깊이 우선으로 읽음
```

- id는 (램포트 카운터, 사이트 id) 쌍이 흔하다(05번). 지운 글자는 다른 글자의 기준일 수 있어 바로 버리지 못하고 **툼스톤**으로 남는다.
- Yjs(내부 문서 INTERNALS.md)
  - YATA 알고리즘(2016)을 고친 리스트 CRDT다. 글자마다 `ID(clientID, clock)`(램포트 타임스탬프)와 왼쪽·오른쪽 이웃 id(`origin`, `originRight`)를 저장한다.
  - 같은 클라이언트가 연달아 친 글자는 `Item` 하나로 합친다(run). 삽입은 연산 기반, 삭제는 "지워짐 표시 + 지운 id 집합"인 상태 기반으로 다룬다.
  - GC를 켜면(기본) 지운 글자의 **내용**은 버리지만, 순서를 위해 구조체(툼스톤)는 남긴다. README: "순서를 유일하게 유지하면서 지운 구조체를 GC할 수는 없다."
  - 동기화: 상태 벡터(클라이언트별 clock)를 보내고 상대가 모르는 갱신만 받는다(y-protocols sync step 1·2).
- 끼워짐(Kleppmann 외 PaPoC 2019)
  - Logoot·LSEQ는 동시에 같은 자리에 친 두 단어가 글자 단위로 뒤섞일 수 있다. 두 사용자가 같은 구간 안에 각자 위치 값을 흩뿌려 고르므로, 위치 값 순으로 합치면 임의로 섞이기 때문이다. 논문은 공개 구현에서 이 현상을 실제로 관찰했다.
  - RGA는 그 강한 형태는 없지만, 글자를 거꾸로 입력하는 등 순차가 아닌 삽입에서 "약한 끼워짐"이 남는다고 논문이 보였다.

### 실험 1: OT 변환 함수 — 동률 처리 하나가 수렴을 가른다

- 코드: `ot.js`. 문자 단위 insert/delete와 변환 함수를 구현했다. `tieBreak=false`는 같은 위치 삽입에서 아무도 밀지 않는 **버그 판**이다.

```js
if (a.type === 'ins' && b.type === 'ins') {
  if (a.pos < b.pos) return a;
  if (a.pos > b.pos) return { ...a, pos: a.pos + 1 };
  if (!tieBreak) return a;                                   // 버그: 동률을 아무도 밀지 않는다
  return a.site < b.site ? a : { ...a, pos: a.pos + 1 };     // 사이트 번호가 작은 쪽을 앞에
}
```

(실험, Node 18.19.1, 2026-10-01)

```text
[동시 삽입 pos=2] tieBreak=true  site1="abXYcd"  site2="abXYcd"  수렴
[동시 삽입 pos=2] tieBreak=false  site1="abYXcd"  site2="abXYcd"  발산
[변환 없음] base="abcd" site1: ins X@0 → del@3 = "Xabd" (site2는 'd'를 지우려 했다)
[무작위 10000쌍] tieBreak=true  같은 위치 동시 삽입 354쌍, 발산 0건
[무작위 10000쌍] tieBreak=false  같은 위치 동시 삽입 354쌍, 발산 354건  예: o1={"type":"ins","pos":2,"ch":"X","site":1} o2={"type":"ins","pos":2,"ch":"Y","site":2} → "abYXcdef" vs "abXYcdef"
```

- 관찰: 무작위 1만 쌍 중 같은 위치 동시 삽입 354쌍이 **전부** 발산했다. 나머지 경우는 맞았다. 점검 때 코드를 다시 짜서(다른 난수 생성기) 돌리면 349쌍이 나왔고, 역시 같은 위치 동시 삽입만 전부 발산했다. 쌍 수는 난수에 따라 다르다(기대값 약 1/4 × 1/7 × 1만 ≈ 357). 변환 함수 버그는 드문 경우에만 드러나고, 드러나면 사용자마다 다른 문서가 남는다.
- 이 실험은 두 사이트·한 쌍의 연산(TP1)만 본다. 세 사이트 이상의 TP2 문제는 실험하지 않았다.

### 실험 2: Yjs 13.6.33 — 수렴, 오프라인 병합, 툼스톤, 커서

- 코드: `yjs_exp.js`. 두 `Y.Doc`를 상태 벡터로 동기화한다.

```js
function sync(a, b) {               // 상태 벡터를 교환해 서로 모르는 갱신만 보낸다
  const ua = Y.encodeStateAsUpdate(a, Y.encodeStateVector(b));
  const ub = Y.encodeStateAsUpdate(b, Y.encodeStateVector(a));
  Y.applyUpdate(b, ua); Y.applyUpdate(a, ub);
}
```

(실험, Node 18.19.1 · yjs 13.6.33, 2026-10-01)

```text
[1 동시 삽입] 병합 전 A="abXcd" B="abYcd" → 병합 후 A="abXYcd" B="abXYcd"
[2 오프라인 병합] A="Hi Alice Bob!" B="Hi Alice Bob!"
[3 크기] 입력=seq    gc=true  1만 글자 상태 10011 B → 전부 삭제 후 글자 0개, 상태 16 B
[3 크기] 입력=seq    gc=false 1만 글자 상태 10011 B → 전부 삭제 후 글자 0개, 상태 10016 B
[3 크기] 입력=random gc=true  1만 글자 상태 88581 B → 전부 삭제 후 글자 0개, 상태 78586 B
[3 크기] 입력=random gc=false 1만 글자 상태 88581 B → 전부 삭제 후 글자 0개, 상태 88586 B
[4 커서] 문서="xxac" 정수 위치 1 → "x|xac"  상대 위치 → 3 "xxa|c"
```

- 관찰
  - 1: 같은 위치 동시 삽입이 양쪽에서 같은 문서로 수렴했다. X와 Y 중 무엇이 앞에 오는지는 무작위로 정해지는 clientID에 달려 실행마다 다를 수 있다(점검 재실행에서는 `abYXcd`). 2의 "Alice"·"Bob" 순서도 같다.
  - 2: "Hi"와 "!" 사이에 오프라인으로 " Alice"와 " Bob"을 한 글자씩 쳤다. 병합 결과 단어가 섞이지 않았다.
  - 3: 끝에 이어 친 1만 글자는 하나의 run이라, 다 지우면 GC 후 상태가 16바이트다. 무작위 위치에 친 1만 글자는 글자마다 별도 구조체라, 다 지워 내용이 0이어도 상태가 78586바이트로 남았다(툼스톤). GC를 끄면 내용까지 남아 88586바이트.
    - 바이트 수는 clientID 길이와 무작위 삽입 위치에 따라 달라진다. 점검 때 다시 짠 코드로는 순차 GC 후 22~24 B, 무작위 GC 후 158498 B(삭제 전 168489 B)였다. "순차 입력은 거의 0으로 줄고 흩어진 입력은 GC 뒤에도 대부분 남는다"는 경향은 같다.
  - 4: 원격 사용자가 커서 앞에 "xx"를 넣었다. 정수 위치(1)는 엉뚱한 곳을 가리키고, 상대 위치(`RelativePosition`)는 원래 글자 `c` 앞을 유지했다.

### 실험 3: 끼워짐 — 분수 위치 vs RGA류

- 코드: `interleave.js`. 두 가지 단순화 구현. (A) 두 이웃 사이의 무작위 분수 위치로 글자를 놓는 Logoot류, (B) 직전 글자를 기준으로 삼는 RGA류. 둘 다 "Hi!"의 "Hi"와 "!" 사이에 오프라인으로 " Alice"(사이트 1)와 " Bob"(사이트 2)을 친 뒤 병합한다.

(실험, Node 18.19.1, 2026-10-01)

```text
[분수 위치 #1] A쪽 병합="Hi B oAlbice!"  B쪽 병합="Hi B oAlbice!"  수렴
[분수 위치 #2] A쪽 병합="Hi  ABloicbe!"  B쪽 병합="Hi  ABloicbe!"  수렴
[분수 위치 #3] A쪽 병합="Hi  AlBobice!"  B쪽 병합="Hi  AlBobice!"  수렴
[RGA류] A쪽 병합="Hi Bob Alice!"  B쪽 병합="Hi Bob Alice!"
```

- 관찰: 분수 위치 방식은 매번 **수렴했지만 읽을 수 없다**(섞인 모양은 실행마다 다르다). RGA류는 단어가 통째로 붙었다. 수렴은 CRDT의 정의이고, 끼워짐 없음은 별도 성질이다.
- 이 구현들은 원리 시연용 단순화다. 실제 Logoot·LSEQ 구현으로 돌린 결과가 아니다(그 결과는 Kleppmann 외 2019 논문이 보고).

## 쓰이는 자료구조·알고리즘

- **변환 함수(transformation function)** — OT의 핵심. 연산 쌍마다 경우 나누기.
- **연산 기록 + 서버 확인(ack)** — Wave의 중앙 OT(Jupiter의 클라이언트-서버 OT에 ack 대기를 더함). 서버 쪽 기록 하나로 단순화.
- **위치 식별자 트리** — RGA·Yjs에서 "왼쪽 기준 글자"를 부모로 하는 트리, 깊이 우선 읽기가 문서 순서다. Logoot·LSEQ는 정수 경로(path) 식별자의 트리.
- **이중 연결 리스트 + 검색 마커** — Yjs는 문서 순서로 `Item`을 이중 연결 리스트에 두고, 최근 위치 80개를 캐시해 인덱스 → 항목 찾기를 빠르게 한다(INTERNALS.md).
- **벡터 시계(상태 벡터)** — 클라이언트별로 받은 clock. 무엇이 빠졌는지 계산해 증분 동기화. [05-logical-clocks](../05-logical-clocks/2-summary.md)
- **로프(rope)** — 큰 문자열을 트리로 쪼개 중간 삽입을 싸게 하는 구조. 편집기 내부 텍스트 버퍼. [data-structure/28-rope](../../data-structure/28-rope/2-summary.md)
- **분수 인덱싱(fractional indexing)** — 목록 항목 순서를 0~1 사이 분수로 두고, 사이에 넣을 때 두 이웃의 중간값. Figma가 자식 순서에 쓴다(블로그).

## 적용 — 풀어나가는 법

### 1. 무엇을 동시 편집하나로 고른다

| 상황 | 선택 | 근거 |
|---|---|---|
| 중앙 서버가 항상 있고 텍스트 위주 | 서버 기반 OT 또는 CRDT 라이브러리 | Wave 백서: 서버 확인으로 단순화 |
| 오프라인 편집·P2P·로컬 우선 | 시퀀스 CRDT(Yjs·Automerge) | Local-first 논문의 7가지 이상 중 "네트워크는 선택" |
| 도형·속성 편집, 같은 값의 글자 단위 병합 불필요 | 속성별 LWW + 서버 권위 | Figma: 같은 텍스트 값 동시 편집은 둘 중 하나만 남음 |
| 목록 재정렬 | 분수 인덱싱 | Figma |

### 2. 클라이언트 구조 (TypeScript, Yjs)

```ts
import * as Y from 'yjs';

const doc = new Y.Doc();
const text = doc.getText('body');

// 1) 로컬 편집 → 증분 갱신을 서버(또는 피어)로
doc.on('update', (update: Uint8Array, origin: unknown) => {
  if (origin !== 'remote') socket.send(update);           // 받은 것을 되돌려 보내지 않는다
});
socket.onmessage = (e: MessageEvent<ArrayBuffer>) =>
  Y.applyUpdate(doc, new Uint8Array(e.data), 'remote');

// 2) 재접속 시: 내 상태 벡터를 보내고 모자란 것만 받는다
socket.send(Y.encodeStateVector(doc));                     // 프로토콜 구분은 y-protocols의 메시지 타입을 쓴다

// 3) 커서는 정수가 아니라 상대 위치로 저장·전송
const rel = Y.createRelativePositionFromTypeIndex(text, cursorIndex);
const abs = Y.createAbsolutePositionFromRelativePosition(rel, doc);   // 원격 편집 뒤 다시 계산
```

- 프레즌스(누가 접속 중인지, 커서·선택 영역·이름·색)는 **문서와 따로** 보낸다. y-protocols의 awareness는 클라이언트마다 상태 하나를 두고, 30초 동안 갱신이 없으면 로컬에서 지운다(README). 문서 CRDT에 넣으면 커서 이동마다 영구 기록·툼스톤이 쌓인다.
- 전송로는 보통 WebSocket이다. [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md)

### 3. 오프라인 병합 순서

1. 오프라인 동안 로컬 문서에 계속 편집한다(로컬 저장소에 갱신을 쌓는다).
2. 재접속하면 상태 벡터 교환 → 서로 모르는 갱신만 주고받는다.
3. 병합 결과를 사용자에게 강조 표시한다(누가 무엇을 바꿨나). 수렴해도 의미가 충돌할 수 있다(두 사람이 같은 문장을 다르게 고침).
- Figma는 다르게 한다: 재접속하면 최신 문서를 새로 받고, 그 위에 오프라인 편집을 다시 적용한다(블로그).

### 4. 진단

- 수렴 검사: 같은 갱신 집합을 받은 클라이언트들의 문서 해시를 주기적으로 비교한다. 다르면 변환 함수·통합 로직 버그다.
- 크기 검사: 상태 크기(`Y.encodeStateAsUpdate(doc).length`)와 실제 글자 수의 비율을 지표로 낸다. 비율이 계속 오르면 툼스톤·이력 누적이다.

## 장애 시나리오와 대처

### 1. 변환 함수 버그 → 사용자마다 다른 문서 (커리큘럼 ⚠)

- **현상**: 두 사용자가 동시에 입력한 뒤 화면 내용이 서로 다르다. 새로고침하면 한쪽 화면이 바뀐다.
- **보이는 형태**: 클라이언트별 문서 해시 불일치. 특정 경우(같은 위치 동시 삽입, 겹치는 삭제)에서만 재현. 실험 1에서 버그 판은 같은 위치 동시 삽입 354쌍 전부 발산, 나머지는 정상.
- **원인**: 변환 함수가 TP1(필요하면 TP2)을 만족하지 않는다. 경우의 수가 많아 손으로 빠뜨리기 쉽다.
- **대처**
  - 무작위 연산 쌍·삼중을 만들어 "두 순서로 적용한 결과가 같은가"를 검사하는 성질 기반 테스트를 둔다(실험 1의 방식).
  - 서버 확인 기반 OT로 바꿔 TP2가 필요 없게 하거나, 검증된 CRDT 라이브러리를 쓴다.

### 2. 오프라인 병합에서 문단이 섞여 끼워짐 (커리큘럼 ⚠)

- **현상**: 두 사람이 오프라인에서 같은 자리에 쓴 문장이 병합 뒤 글자 단위로 뒤섞인다.
- **보이는 형태**: "Hi B oAlbice!"처럼 읽을 수 없는 텍스트(실험 3). 모든 클라이언트가 같은 엉망을 본다(수렴은 했다).
- **원인**: 위치 식별자를 무작위성을 섞어 고르는 알고리즘(Logoot·LSEQ)의 성질. RGA도 비순차 삽입에서는 약한 끼워짐이 있다(Kleppmann 외 2019).
- **대처**: 끼워짐을 막는 알고리즘·구현을 고른다. 실험 2에서 Yjs는 같은 상황에서 단어가 섞이지 않았다. 라이브러리를 고를 때 이 경우를 직접 테스트한다.

### 3. 툼스톤·이력 누적 → 문서 크기·메모리 증가 (커리큘럼 ⚠)

- **현상**: 오래 편집한 문서의 로딩이 느리고 메모리를 많이 쓴다. 보이는 글은 몇 쪽인데 저장 크기는 수 MB다.
- **보이는 형태**: 상태 크기 / 글자 수 비율 증가. 실험 2-3에서 글자 0개인데 상태 78586바이트.
- **원인**: 지운 글자의 구조체를 순서 보존을 위해 남긴다. 흩어진 편집일수록 run으로 합쳐지지 않아 커진다. Local-first 논문도 Automerge로 만든 시제품 경험에서 "CRDT는 글자 단위 편집까지 모든 이력을 저장해 쌓이고, 6개월 뒤 다시 접속할 사람이 있을 수 있어 쉽게 자를 수 없다"고 적는다.
- **대처**
  - GC를 켠다(Yjs 기본): 지운 내용은 버리고 구조체만 남긴다.
  - 모든 참여자가 특정 시점 이후 상태를 가졌다고 확인되면 그 시점으로 새 문서를 만들어 이력을 끊는다(스냅샷 압축). 그 이전 상태로 오프라인 편집하던 클라이언트는 병합할 수 없게 되므로 정책이 필요하다.

### 4. 원격 편집 뒤 커서가 엉뚱한 곳으로 튐

- **현상**: 다른 사람이 위쪽에 글을 넣으면 내 커서가 다른 단어로 이동한다.
- **보이는 형태**: 실험 2-4의 `정수 위치 1 → "x|xac"`.
- **원인**: 커서를 정수 인덱스로 저장했다.
- **대처**: 커서·선택·댓글 범위를 상대 위치(글자 id 기준)로 저장한다. Yjs `RelativePosition`.

### 5. 프레즌스를 문서에 넣어 문서가 부풂

- **현상**: 아무도 글을 안 쓰는데 문서 크기가 계속 큰다.
- **보이는 형태**: 문서 갱신 대부분이 커서 위치 변경.
- **원인**: 일시적 상태(커서·접속 여부)를 영구 CRDT 문서에 기록했다.
- **대처**: awareness 같은 별도 채널로 보낸다. 끊긴 사용자의 프레즌스는 시간 초과로 지운다(y-protocols는 30초).

## 핵심 문장

- 정수 위치는 동시 편집에서 뜻이 바뀐다. OT는 위치를 변환하고, 시퀀스 CRDT는 글자에 바뀌지 않는 id를 붙인다.
- OT 변환 함수는 두 순서의 결과가 같아야(TP1) 하고, 동률 하나를 빠뜨려도 사용자마다 다른 문서가 남는다.
- 중앙 서버가 연산 순서를 정하면 OT가 크게 단순해진다(Jupiter). 클라이언트가 확인까지 기다리게 하면 더 단순해진다(Wave).
- 시퀀스 CRDT는 수렴을 보장하지만 끼워짐 없음은 별도 성질이다. Logoot·LSEQ는 동시 입력을 글자 단위로 섞을 수 있다.
- 지운 글자의 구조체는 순서 때문에 남는다. 흩어진 편집과 긴 이력이 문서 크기를 키운다.
- 커서·프레즌스는 상대 위치와 별도 일시 채널로 다룬다.

## 관련 주제·근거

- 선행: [24-conflict-resolution-and-crdt](../24-conflict-resolution-and-crdt/2-summary.md) — CRDT 정의·SEC·OR-Set·툼스톤
- 선행: [data-structure/28-rope](../../data-structure/28-rope/2-summary.md) — 편집기 텍스트 버퍼(커리큘럼 표기 `data-structure/41-rope`, 영역 표의 노트 링크는 28-rope)
- 연결
  - [05-logical-clocks](../05-logical-clocks/2-summary.md) — 램포트 id, 상태 벡터
  - [13-distributed-id-generation](../13-distributed-id-generation/2-summary.md) — 클라이언트 id + 카운터로 만드는 고유 id(Figma 객체 id도 같은 방식)
  - [network/38-websocket-sse-long-lived](../../network/38-websocket-sse-long-lived/2-summary.md) — 전송로
- 논문
  - C. A. Ellis, S. J. Gibbs, "Concurrency Control in Groupware Systems", SIGMOD 1989 — GROVE, 수렴·선후 성질, 상태 벡터, 우선순위 <https://doi.org/10.1145/67544.66963>
  - M. Kleppmann, V. B. F. Gomes, D. P. Mulligan, A. R. Beresford, "Interleaving anomalies in collaborative text editors", PaPoC 2019 — Logoot·LSEQ 끼워짐, RGA 약한 끼워짐 <https://martin.kleppmann.com/papers/interleaving-papoc19.pdf>
  - M. Kleppmann, A. Wiggins, P. van Hardenberg, M. McGranaghan, "Local-first software: you own your data, in spite of the cloud", Onward! 2019 — 7가지 이상, CRDT 이력 누적 <https://www.inkandswitch.com/essay/local-first/>
- 문서·글
  - Evan Wallace, "How Figma's multiplayer technology works", Figma 블로그 2019-10-16 — OT 미채택 이유, 속성별 LWW, 서버 권위, 오프라인 재적용, 분수 인덱싱 <https://www.figma.com/blog/how-figmas-multiplayer-technology-works/>
  - Google Wave Operational Transformation 백서 — Jupiter 방식, 클라이언트가 서버 ack를 기다림 <https://svn.apache.org/repos/asf/incubator/wave/whitepapers/operational-transform/operational-transform.html>
  - Wikipedia "Operational transformation" — TP1/TP2 정의, dOPT 이후 수정 이력(2차 자료) <https://en.wikipedia.org/wiki/Operational_transformation>
  - Yjs README(Relative Positions, CRDT 알고리즘·GC)·INTERNALS.md(Item·origin·run·삭제 처리·상태 벡터) <https://github.com/yjs/yjs>
  - y-protocols README — awareness(30초 시간 초과) <https://github.com/yjs/y-protocols>
- 실험 목록
  - `ot.js` — 문자 단위 OT 변환 함수, 동률 처리 유무별 수렴(무작위 1만 쌍). Node 18.19.1.
  - `yjs_exp.js` — yjs 13.6.33: 동시 삽입 수렴, 오프라인 단어 병합, 1만 글자 삽입·삭제 후 상태 크기(순차·무작위 × GC 켬·끔), RelativePosition. Node 18.19.1.
  - `interleave.js` — 분수 위치(Logoot류 단순화) vs RGA류 단순화의 오프라인 병합. Node 18.19.1.
