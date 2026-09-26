# web-api/30 — 요청 본문 만들기: `FormData`·`URLSearchParams`·JSON 과 `Content-Type` 자동 설정 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」 — 서버가 받은 `Content-Type` 과 **그것으로 고른 파서의 결과**를 칸마다 서버에게 묻는 「자동 `Content-Type` 격자」다.** 본문 일곱 × `Content-Type` 을 직접 쓰나(안 씀 / 씀) = 14칸, 마지막 줄을 스크립트가 **「직접 써서 서버 파싱이 깨진 본문 N / 7」** 로 찍는다. 그 옆에 **원문(본문 바이트)** 을 서버 로그째 싣는다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 「extract a body」(**`Blob` — `type` 이 빈 바이트열이 아니면 그 값** · `BufferSource` — 타입 없음 · **`FormData` — `multipart/form-data; boundary=` + multipart/form-data 인코딩 알고리즘이 만든 boundary 문자열** · **`URLSearchParams` — `application/x-www-form-urlencoded;charset=UTF-8`** · **문자열 — `text/plain;charset=UTF-8`**) · Request 생성자(「type 이 null 이 아니고 **headers 에 `Content-Type` 이 없으면** 그때만 붙인다」) · [WHATWG HTML](https://html.spec.whatwg.org/multipage/form-control-infrastructure.html) 의 「create an entry」(**`File` 이 아닌 `Blob` 은 이름이 `"blob"` 인 새 `File` 로** · filename 을 주면 그 이름으로) · 「constructing the entry list」(**체크 안 된 체크박스는 건너뛴다**) · 「multipart/form-data encoding algorithm」(**RFC 7578** 을 따르고, **파일이 아닌 칸에는 `Content-Type` 을 붙이지 않는다** · boundary 는 알고리즘이 만든다) · [WHATWG XHR](https://xhr.spec.whatwg.org/) 의 `FormData(form)` 생성자(form 이 주어지면 **constructing the entry list** 의 결과를 쓴다). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 요청은 **같은 출처 A 의 `/echo`** 로 보냈다 — CORS 를 빼고 본문만 고립시키려고. 서버는 받은 **`Content-Type` · 원문 · 직접 짠 파서의 결과**를 적는다(파이썬 `email`·`cgi` 를 안 쓰고 **boundary 로 직접 가른다** — 파서가 대신 고쳐 주는 일을 없애려고). 하네스는 [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1)이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[HTML 21번 주제](../../languages/html/syntax/21-form-submission-model/2-summary.md)의 (1)이 폼 제출의 `method` × `enctype` 여섯 칸을 서버 로그로 쟀다** — 그쪽은 **마크업이 만드는 본문**, 여기는 **같은 본문을 스크립트로** 만든다((4)가 둘을 원문째 견준다). HTML 21편도 boundary 를 「(경계)」로 죽였다. ★ **[25번 주제](../25-fetch-request-response/2-summary.md)** — `fetch` 의 옵션 표면. ★ **[28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (2)** — `Content-Type` 값이 프리플라이트를 정한다((6)이 잇는다).\
> 이 본문은 Claude 작성이다(원고 없음). 규칙은 위 기준 소스로, 출력은 실행으로 접지했다.

**이 판의 Chrome**

```text
$ google-chrome --version
Google Chrome 151.0.7922.173 
(exit 0)
```

### 흔들리는 칸 / 안 흔들리는 칸

| | 칸 | 왜 |
|---|---|---|
| **안 흔들린다** | 격자 14칸 · 원문(boundary 를 가린 것) · 바이트 수 · 파일 칸 · 폼 대 `fetch` · 파이썬 대비 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **흔들린다 — 하네스가 가렸다** | **multipart boundary 의 뒤 16자**(Chrome — `----WebKitFormBoundary` 뒤) · **파이썬 `requests` 의 boundary 32자**(16진) | 브라우저·라이브러리가 **요청마다 새로 만든다.** 서버가 **로그에 적기 전에** `<16자>`·`<32자>` 로 바꾼다 — 그래서 재대조에서 정규화할 칸이 남지 않는다. ★ **바이트 수는 안 흔들린다** — 길이가 고정이기 때문이다 |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조 정규화 규칙은 **0개** — 흔들리는 칸은 하네스가 **출력 전에** 가렸다(위 표). **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `FormData.get()` 이 돌려주는 것의 종류·이름·`type`((3)) |
| 창 ③ 같은 것을 두 번 읽기 | ★★★ **쓴다** | **같은 `FormData` 를 두 번** — 헤더만 다르게((2)) · **같은 폼을 두 길로** — `fetch` 와 진짜 제출((4)) |
| **창 ④ 서버 요청 로그 — 받은 `Content-Type` · 원문 · 파싱** | ★★★ **본체** | 무엇이 **실렸나**(원문) · 서버가 **무엇으로 읽었나**(파싱) |
| ★ **「무엇이 실렸나」를 페이지 대신 서버에게** | ★★ **같은 질문을 다른 창으로(제5의 상태)** | 페이지는 **서버에 실제로 닿은 `Content-Type` 을 볼 수 없다.** 그래서 서버에게 `/note` 로 물었다. ★ 바꾼 창이 못 보는 것 — **HTTP 층에서 바뀌는 것**(압축·청크)은 이 서버가 풀어서 받으므로 안 보인다 |
| 파이썬 `urllib`·`requests` | ★ **대비** | 다른 클라이언트는 **무엇을 자동으로 붙이나**((5)) |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★ **서버 프레임워크의 관용** | 파서를 **직접** 짰다 — boundary 가 없으면 못 가른다. 어떤 프레임워크는 본문 첫 줄에서 boundary 를 **짐작**할지도 모른다. 그런 관용은 이 판이 말하지 않는다 |
| **업로드 진행률 · 큰 파일** | 본문은 수백 바이트다. 스트림 업로드는 28편 (3)에서 HTTP/1.1 로는 안 나갔다 |
| **`text/plain` 폼 인코딩 · 문자 인코딩이 UTF-8 이 아닌 폼** | 던지지 않았다(HTML 21편이 `text/plain` 을 쟀다) |

## 한눈에 — 쉽게 말하면

**★ `fetch` 의 본문은 「내용물」이고 `Content-Type` 은 「상자에 붙이는 송장」이다. `FormData`·`URLSearchParams`·문자열을 넣으면 브라우저가 내용물을 보고 송장을 알아서 붙인다 — `FormData` 의 송장에는 「칸막이 모양(boundary)」까지 적혀 있다. 송장을 내가 직접 붙이면 브라우저는 자기 송장을 안 붙인다 — 칸막이는 상자 안에 그대로 있는데 송장에서 그 모양이 빠져, 받는 쪽이 상자를 못 연다.**

| 비유 | 실체 |
|---|---|
| 내용물 | `body` — `FormData` · `URLSearchParams` · 문자열 · `Blob` · `ArrayBuffer` |
| 브라우저가 붙이는 송장 | 자동 `Content-Type` |
| 칸막이 모양 | `boundary=----WebKitFormBoundary…` — 본문 안의 구분선과 같은 글자 |
| 내가 직접 붙인 송장 | `headers: { "Content-Type": … }` — **있으면 자동 송장은 안 붙는다** |
| 송장 없는 상자 | 타입 없는 `Blob`·`ArrayBuffer` — `Content-Type` 이 **아예 없다** |

```text
   ★ 같은 FormData, 송장 둘 — 서버가 받은 것 (이 판)

   직접 안 씀   Content-Type: multipart/form-data; boundary=----WebKitFormBoundary<16자>
                본문        ------WebKitFormBoundary<16자> ... a ... 1 ...        ─▶ 칸 1개 · a=1
   직접 씀      Content-Type: multipart/form-data                                 ← boundary 가 없다
                본문        ------WebKitFormBoundary<16자> ... a ... 1 ...        ─▶ 가를 수 없다
                            ★ 본문은 한 글자도 같다 — 송장만 다르다
```

## 이 주제가 답하려는 질문

1. **본문의 종류마다 브라우저는 무슨 `Content-Type` 을 붙이나** — 그리고 내가 직접 쓰면 무엇이 달라지나.
2. **`FormData` 에 `Content-Type` 을 직접 쓰면 왜 깨지나** — 무엇이 빠지고, 본문은 어떻게 되나.
3. **폼 제출과 같은 본문을 스크립트로 만들 수 있나** — 파일 칸의 `filename`·`Content-Type` 까지.

## 동작 방식

### (1) ★★★ 본체 — 자동 `Content-Type` 격자: 직접 써서 깨진 본문

**언제 쓰나** — 「`FormData` 로 올렸더니 서버가 필드를 하나도 못 읽는다」 · 「JSON 을 보냈는데 서버가 JSON 이 아니라고 한다」일 때.

**던진 것** — 같은 출처 A 의 `/echo` 에 본문 일곱 × (`Content-Type` 안 씀 / 씀). 「씀」에는 **그 본문에 자연스러운 값**을 적었다 — `FormData` 에는 `multipart/form-data`, JSON 들에는 `application/json` 식으로. 칸마다 **서버가 받은 `Content-Type`** 과 **그것으로 고른 파서의 결과**를 서버에게 묻는다.

```html
<!-- wa28b-30-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>30 grid</title>
<script>
// 본문 일곱 × Content-Type 을 직접 쓰나(안 씀 / 씀) — 같은 출처 A 의 /echo 에 POST 하고,
// 서버가 받은 Content-Type 과 그것으로 고른 파서의 결과를 서버에게 묻는다
const 본문 = [
  ["FormData", () => { const f = new FormData(); f.append("a", "1"); f.append("b", "한"); return f; }, "multipart/form-data"],
  ["URLSearchParams", () => new URLSearchParams({ a: "1", b: "한" }), "application/x-www-form-urlencoded"],
  ["문자열", () => "a=1", "text/plain"],
  ["Blob(type 있음)", () => new Blob(['{"a":1}'], { type: "application/json" }), "application/json"],
  ["Blob(type 없음)", () => new Blob(['{"a":1}']), "application/json"],
  ["JSON.stringify", () => JSON.stringify({ a: 1 }), "application/json"],
  ["ArrayBuffer", () => new TextEncoder().encode('{"a":1}').buffer, "application/json"],
];
const 너비 = t => [...t].reduce((n, ch) => n + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 한줄 = (칸들, 폭) => {
  if (칸들.length !== 폭.length) throw new Error("칸 수가 어긋났다");
  return 칸들.map((c, k) => k === 칸들.length - 1 ? c : c + " ".repeat(Math.max(폭[k] - 너비(c), 1))).join("");
};
window.__끝 = async () => {
  const 폭 = [17, 36, 60, 0];
  const O = [한줄(["본문", "직접 쓴 Content-Type", "서버가 받은 Content-Type", "서버 파싱"], 폭)];
  let n = 0, 바뀜 = 0, 깨짐 = 0;
  for (const [이름, 만들기, 쓸것] of 본문) {
    const 두칸 = [];
    for (const 씀 of [false, true]) {
      const id = "b" + n++;
      const init = { method: "POST", body: 만들기() };
      if (씀) init.headers = { "Content-Type": 쓸것 };
      await fetch("/echo?id=" + id, init);
      const 받음 = await (await fetch("/note?id=" + id)).json();
      두칸.push(받음);
      O.push(한줄([이름, 씀 ? 쓸것 : "(안 씀)", 받음.ct, 받음.parse], 폭));
    }
    if (두칸[0].ct !== 두칸[1].ct) 바뀜++;
    const 실패 = p => /가를 수 없다|갈라지지|파싱 실패|파서 없음/.test(p);
    if (!실패(두칸[0].parse) && 실패(두칸[1].parse)) 깨짐++;
  }
  O.push("직접 써서 서버가 받은 Content-Type 이 바뀐 본문 = " + 바뀜 + " / " + 본문.length +
         " · 직접 써서 서버 파싱이 깨진 본문 = " + 깨짐 + " / " + 본문.length);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py page wa28b-30-grid.html | sed -n '1,16p'
본문             직접 쓴 Content-Type                서버가 받은 Content-Type                                    서버 파싱
FormData         (안 씀)                             multipart/form-data; boundary=----WebKitFormBoundary<16자>  칸 2개 · a=1 · b=한
FormData         multipart/form-data                 multipart/form-data                                         boundary 가 Content-Type 에 없다 — 가를 수 없다
URLSearchParams  (안 씀)                             application/x-www-form-urlencoded;charset=UTF-8             칸 [["a", "1"], ["b", "한"]]
URLSearchParams  application/x-www-form-urlencoded   application/x-www-form-urlencoded                           칸 [["a", "1"], ["b", "한"]]
문자열           (안 씀)                             text/plain;charset=UTF-8                                    글 「a=1」
문자열           text/plain                          text/plain                                                  글 「a=1」
Blob(type 있음)  (안 씀)                             application/json                                            JSON {"a": 1}
Blob(type 있음)  application/json                    application/json                                            JSON {"a": 1}
Blob(type 없음)  (안 씀)                             (없음)                                                      (Content-Type 으로 고를 파서 없음)
Blob(type 없음)  application/json                    application/json                                            JSON {"a": 1}
JSON.stringify   (안 씀)                             text/plain;charset=UTF-8                                    글 「{"a":1}」
JSON.stringify   application/json                    application/json                                            JSON {"a": 1}
ArrayBuffer      (안 씀)                             (없음)                                                      (Content-Type 으로 고를 파서 없음)
ArrayBuffer      application/json                    application/json                                            JSON {"a": 1}
직접 써서 서버가 받은 Content-Type 이 바뀐 본문 = 6 / 7 · 직접 써서 서버 파싱이 깨진 본문 = 1 / 7
(exit 0)
```

- ★★★ **직접 써서 서버 파싱이 깨진 본문 1 / 7 — `FormData` 하나.** 직접 쓰면 받은 값이 **`multipart/form-data`(boundary 없음)** 이고 서버는 **가를 수 없다.**
- ★★ **직접 써서 받은 `Content-Type` 이 바뀐 본문 6 / 7** — 바뀌어도 대개는 무해하다: `;charset=UTF-8` 이 빠지거나(`URLSearchParams`·문자열), 없던 것이 생긴다(타입 없는 `Blob`·`ArrayBuffer`). **안 바뀐 것은 `type` 을 준 `Blob` 하나**다(같은 값을 적었으므로). 명세 — Request 생성자는 **`Content-Type` 이 이미 있으면 자동 값을 안 붙인다.**
- ★★ **`JSON.stringify` 만 넘기면 `text/plain;charset=UTF-8`** — 서버가 `Content-Type` 으로 파서를 고르면 JSON 이 아니라 **글**로 읽는다. JSON 은 **문자열**일 뿐이라 브라우저는 모른다((6)).
- ★ **타입 없는 `Blob` 과 `ArrayBuffer` 는 `Content-Type` 이 아예 없다**(`(없음)`) — 명세 그대로(`Blob` 은 `type` 이 비었으면 안 붙이고, `BufferSource` 는 타입이 없다).
- **`URLSearchParams` 는 `한` 을 서버가 그대로 되찾았다** — 퍼센트 인코딩(`%ED%95%9C`)이다.

```text
   본문 일곱 — 브라우저가 붙인 송장 (직접 안 썼을 때, 이 판)

   FormData          multipart/form-data; boundary=----WebKitFormBoundary<16자>
   URLSearchParams   application/x-www-form-urlencoded;charset=UTF-8
   문자열            text/plain;charset=UTF-8
   JSON.stringify    text/plain;charset=UTF-8                  ← JSON 이라고 안 붙는다
   Blob(type 있음)   application/json                          ← 그 type 그대로
   Blob(type 없음)   (없음)
   ArrayBuffer       (없음)
```

### (2) ★★★ boundary 가 빠지면 — 원문은 같고 송장만 다르다

**같은 `FormData` 를 두 번** — 헤더를 안 쓰고 한 번, `multipart/form-data` 라고 직접 쓰고 한 번. 서버가 **원문**까지 적는다(`\r\n` 을 보이게, boundary 뒤 16자는 가림).

```html
<!-- wa28b-30-twice.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>30 broken</title>
<script>
// 같은 FormData 를 두 번 — Content-Type 을 안 쓰고 한 번, multipart/form-data 라고 직접 쓰고 한 번. 서버가 받은 원문까지
const 만들기 = () => { const f = new FormData(); f.append("a", "1"); return f; };
window.__끝 = async () => {
  await fetch("/echo?id=f1&raw=1", { method: "POST", body: 만들기() });
  await fetch("/echo?id=f2&raw=1", { method: "POST", body: 만들기(), headers: { "Content-Type": "multipart/form-data" } });
  return "보냈다 — 둘";
};
</script>
```

```text
$ python3 wa28b-net.py page wa28b-30-twice.html
보냈다 — 둘
--- 서버 로그 ---
A POST /echo?id=f1&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 133바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="a"\r\n\r\n1\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 1개 · a=1
A POST /echo?id=f2&raw=1  Content-Type=multipart/form-data · 본문 133바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="a"\r\n\r\n1\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → boundary 가 Content-Type 에 없다 — 가를 수 없다
(exit 0)
```

- ★★★ **두 원문이 한 글자도 같다**(133바이트) — 브라우저는 **본문은 여전히 boundary 로 쌌다.** 달라진 것은 **`Content-Type` 에서 `; boundary=…` 가 빠진 것** 하나다.
- ★★ **서버는 본문 안의 구분선이 무엇인지 알 길이 없다** — `Content-Type` 의 boundary 로 쪼개야 하는데 그 값이 없다. **예외도 경고도 브라우저 쪽에는 없다** — 요청은 `200` 으로 잘 끝났다.
- ★ **처방은 한 줄을 지우는 것**이다 — `FormData` 에는 `Content-Type` 을 **안 쓴다.** boundary 는 **브라우저만 안다**(요청마다 새로 만든다 — 머리말 표).

```text
   FormData 한 칸의 원문 — 칸막이와 송장의 관계 (이 판)

   Content-Type: multipart/form-data; boundary=----WebKitFormBoundary<16자>
                                              └────────── 이 글자 ──────────┐
   ------WebKitFormBoundary<16자>\r\n       ← "--" + 그 글자                 │  서버는 송장에서 이 글자를 읽어
   Content-Disposition: form-data; name="a"\r\n                              │  본문을 이 줄들로 쪼갠다
   \r\n                                                                      │
   1\r\n                                                                     │
   ------WebKitFormBoundary<16자>--\r\n     ← "--" + 그 글자 + "--"  (끝) ───┘
```

### (3) ★ 파일 칸 — `filename` 과 `Content-Type` 은 어디서 오나

**문자열 · 이름 없는 `Blob` · 이름 준 `Blob` · `File`(type 있음 / 없음)** 을 한 `FormData` 에.

```html
<!-- wa28b-30-file.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>30 file</title>
<script>
// 파일 칸의 filename 과 Content-Type — 문자열 · 이름 없는 Blob · 이름 준 Blob · File 을 한 FormData 에
window.__끝 = async () => {
  const f = new FormData();
  f.append("a", "글");
  f.append("b", new Blob(["x"]));
  f.append("c", new Blob(["x"], { type: "text/csv" }), "r.csv");
  f.append("d", new File(["x"], "n.txt", { type: "text/plain" }));
  f.append("e", new File(["x"], "m.bin"));
  const 값 = k => { const v = f.get(k); return typeof v === "string" ? "string" : v.constructor.name + "(name=" + v.name + ", type=" + JSON.stringify(v.type) + ")"; };
  const O = ["FormData.get → " + ["a", "b", "c", "d", "e"].map(k => k + ":" + 값(k)).join(" · ")];
  await fetch("/echo?id=f3&raw=1", { method: "POST", body: f });
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py page wa28b-30-file.html
FormData.get → a:string · b:File(name=blob, type="") · c:File(name=r.csv, type="text/csv") · d:File(name=n.txt, type="text/plain") · e:File(name=m.bin, type="")
--- 서버 로그 ---
A POST /echo?id=f3&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 692바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="a"\r\n\r\n글\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="b"; filename="blob"\r\nContent-Type: application/octet-stream\r\n\r\nx\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="c"; filename="r.csv"\r\nContent-Type: text/csv\r\n\r\nx\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="d"; filename="n.txt"\r\nContent-Type: text/plain\r\n\r\nx\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="e"; filename="m.bin"\r\nContent-Type: application/octet-stream\r\n\r\nx\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 5개 · a=글 · b[filename=blob][application/octet-stream]=<1바이트> · c[filename=r.csv][text/csv]=x · d[filename=n.txt][text/plain]=x · e[filename=m.bin][application/octet-stream]=<1바이트>
(exit 0)
```

- ★★ **`Blob` 을 넣으면 `get()` 이 `File` 을 돌려준다** — 이름을 안 주면 **`name=blob`**, 주면 그 이름(`r.csv`). 명세의 「create an entry」 — **`File` 이 아닌 `Blob` 은 이름이 `"blob"` 인 새 `File`** 이 된다.
- ★★ **파일 칸의 `Content-Type` 은 그 `File` 의 `type`** 이고, 비었으면 **`application/octet-stream`** 이 붙었다(`b`·`e` — 이 판의 관찰). **문자열 칸(`a`)에는 `Content-Type` 줄이 없다** — 명세의 「파일이 아닌 칸에는 붙이지 않는다」.
- 서버 파서는 `text/` 가 아닌 파일 칸의 값을 바이트 수로만 적는다(`<1바이트>`).

```text
   FormData.append 한 번 → 원문의 한 칸 (이 판)

   append("a", "글")                          name="a"                       (Content-Type 줄 없음)
   append("b", new Blob(["x"]))               name="b"; filename="blob"      application/octet-stream
   append("c", Blob{type:text/csv}, "r.csv")  name="c"; filename="r.csv"     text/csv
   append("d", File("n.txt", text/plain))     name="d"; filename="n.txt"     text/plain
   append("e", File("m.bin"))                 name="e"; filename="m.bin"     application/octet-stream
```

### (4) ★★ 폼 제출과 같은 본문 — `fetch(new FormData(form))` 대 진짜 제출

**같은 폼을 두 길로** — 스크립트가 `fetch(new FormData(form))` 로 한 번, 하네스가 폼을 **진짜로 제출**(`requestSubmit()`)시켜 한 번. 폼에는 글 칸 · **체크된** 체크박스 · **체크 안 된** 체크박스 · 파일 칸(CDP `DOM.setFileInputFiles` 로 넣은 `wa28b-30-note.txt`)이 있다.

```html
<!-- wa28b-30-form.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>30 form</title>
<form method="post" enctype="multipart/form-data" action="/echo?id=form&raw=1">
  <input name="title" value="메모">
  <input type="checkbox" name="ok" value="yes" checked>
  <input type="checkbox" name="no" value="yes">
  <input type="file" name="f">
</form>
<script>
// 같은 폼을 두 길로 — 스크립트가 fetch(new FormData(form)) 로 한 번 보내고, 하네스가 폼을 제출시킨다
window.__끝 = async () => {
  await fetch("/echo?id=fetch&raw=1", { method: "POST", body: new FormData(document.forms[0]) });
  return "fetch 로 보냈다 — 이제 폼 제출";
};
</script>
```

```text
$ python3 wa28b-net.py form wa28b-30-form.html wa28b-30-note.txt
fetch 로 보냈다 — 이제 폼 제출
폼 제출 뒤 주소 = http://127.0.0.1:<A>/echo?id=form&raw=1
두 원문(경계 뒤 16자를 가린 것)이 한 글자도 같나 = True
--- 서버 로그 ---
A POST /echo?id=fetch&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 392바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="title"\r\n\r\n메모\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="ok"\r\n\r\nyes\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="f"; filename="wa28b-30-note.txt"\r\nContent-Type: text/plain\r\n\r\n메모 파일\n\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 3개 · title=메모 · ok=yes · f[filename=wa28b-30-note.txt][text/plain]=메모 파일
A POST /echo?id=form&raw=1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 392바이트
    원문 = ------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="title"\r\n\r\n메모\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="ok"\r\n\r\nyes\r\n------WebKitFormBoundary<16자>\r\nContent-Disposition: form-data; name="f"; filename="wa28b-30-note.txt"\r\nContent-Type: text/plain\r\n\r\n메모 파일\n\r\n------WebKitFormBoundary<16자>--\r\n
    서버 파싱 → 칸 3개 · title=메모 · ok=yes · f[filename=wa28b-30-note.txt][text/plain]=메모 파일
(exit 0)
```

- ★★★ **두 원문(boundary 뒤 16자를 가린 것)이 한 글자도 같다** — `True`, 392바이트. **`new FormData(form)` 은 폼 제출과 같은 본문**을 만든다(명세 — 둘 다 같은 「entry list」와 같은 multipart 인코딩 알고리즘을 거친다).
- ★★ **체크 안 된 `no` 는 둘 다 안 실렸다** — entry list 를 만들 때 건너뛴다. **파일 칸은 `filename="wa28b-30-note.txt"` · `text/plain`** 이고 내용 `메모 파일\n` 의 **`\n` 이 그대로**다(명세 — 줄바꿈을 `\r\n` 으로 고치는 것은 **파일이 아닌 칸의 값**뿐이다).
- ★ **다른 것은 boundary 16자뿐**이다 — 요청마다 새로 만들기 때문이다. HTML 21편이 같은 이유로 그 칸을 죽였다.

```text
   같은 폼, 두 길 (이 판)

   new FormData(form) ─▶ fetch POST ─────┐
                                          ├─▶ 서버 원문 392바이트 — boundary 16자만 다르다
   form.requestSubmit() ─▶ 문서 이동 POST ┘     (가리고 견주면 True)
                           └ 페이지가 /echo 의 응답으로 바뀐다 — fetch 는 안 바뀐다
```

### (5) 대비 — 파이썬 `urllib` 와 `requests`

**같은 서버에 파이썬 두 클라이언트로.** `urllib` 는 표준 라이브러리, `requests` 는 서드파티다(파이썬 갈래 목록은 서드파티를 다루지 않는다).

```text
$ python3 wa28b-net.py py
urlopen(urlencode 한 바이트) → status 200 · 보낸 Content-Type = application/x-www-form-urlencoded
urlopen(JSON 바이트) → status 200 · 보낸 Content-Type = application/x-www-form-urlencoded
urlopen(JSON 바이트 + Content-Type 지정) → status 200 · 보낸 Content-Type = application/json
requests.post(files= 만) → status 200 · 보낸 Content-Type = multipart/form-data; boundary=<32자>
requests.post(files= + Content-Type: multipart/form-data 지정) → status 200 · 보낸 Content-Type = multipart/form-data
--- 서버 로그 ---
A POST /echo?id=py  Content-Type=application/x-www-form-urlencoded · 본문 15바이트
    서버 파싱 → 칸 [["a", "1"], ["b", "한"]]
A POST /echo?id=py  Content-Type=application/x-www-form-urlencoded · 본문 8바이트
    서버 파싱 → 칸 [["{\"a\": 1}", ""]]
A POST /echo?id=py  Content-Type=application/json · 본문 8바이트
    서버 파싱 → JSON {"a": 1}
A POST /echo?id=py  Content-Type=multipart/form-data; boundary=<32자> · 본문 248바이트
    서버 파싱 → 칸 2개 · a=1 · f[filename=n.txt][text/plain]=x
A POST /echo?id=py  Content-Type=multipart/form-data · 본문 248바이트
    서버 파싱 → boundary 가 Content-Type 에 없다 — 가를 수 없다
(exit 0)
```

- ★★ **`urllib` 는 `data=` 가 있으면 `Content-Type` 을 안 줄 때 `application/x-www-form-urlencoded` 를 붙인다 — JSON 바이트에도.** 서버는 JSON 을 **폼으로** 읽어 `{"a": 1}` 이라는 **이름 하나**를 얻었다. 브라우저는 문자열에 `text/plain` 을, 바이트(`ArrayBuffer`)에는 **아무것도 안** 붙였다((1)) — **「자동」이 가리키는 값은 클라이언트마다 다르다.**
- ★★ **`requests` 에 `files=` 를 주면 boundary 를 붙인다 — 그런데 `Content-Type: multipart/form-data` 를 직접 주면 똑같이 깨진다**(boundary 없음 · 서버가 못 가른다). **같은 사고가 언어를 안 가린다** — 「본문을 만드는 쪽만 boundary 를 안다」는 구조가 같기 때문이다.

```text
   「Content-Type 을 안 줬을 때」 — 클라이언트 셋이 붙인 것 (이 판)

                      문자열/바이트 JSON                   multipart
   브라우저 fetch     문자열 → text/plain;charset=UTF-8     boundary 자동 · 직접 쓰면 빠짐
                      ArrayBuffer → (없음)
   파이썬 urllib      application/x-www-form-urlencoded     (만들어 주지 않는다)
   파이썬 requests    (던지지 않았다)                       boundary 자동 · 직접 쓰면 빠짐
```

### (6) 연결 — `JSON.stringify` 만 넘기면 다른 출처로는 단순 요청이다

**(1)의 `JSON.stringify` 칸은 `text/plain;charset=UTF-8`** 이었다. [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (2) 격자에서 **`POST` · `text/plain` · 헤더 없음**은 **OPTIONS 가 안 붙는 칸**이다. 새로 재지 않고 두 칸을 잇는다.

```text
   같은 JSON 을 다른 출처로 — 헤더 한 줄이 가르는 것 (28편 (2) · 이 편 (1))

   body: JSON.stringify(x)                                 → text/plain;charset=UTF-8 → 단순 요청 (OPTIONS 없음)
   body: JSON.stringify(x), Content-Type: application/json → application/json          → 프리플라이트 (OPTIONS 먼저)

   ★ 서버가 Content-Type 을 안 보고 JSON 으로 파싱하면 — 프리플라이트 없는 JSON 요청을 받는다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   fetch(url, { method: "POST", body })        body 의 종류가 Content-Type 을 정한다
     FormData          multipart/form-data; boundary=…   ← headers 에 Content-Type 을 쓰지 마라
     URLSearchParams   application/x-www-form-urlencoded;charset=UTF-8
     문자열            text/plain;charset=UTF-8           ← JSON.stringify 결과도 여기
     Blob · File       그 type (비었으면 없음)
     ArrayBuffer · 형식화 배열 · DataView   없음
     ReadableStream    없음 (duplex: "half" 필요 — 28편 (3))

   FormData
     new FormData()  ·  new FormData(formElement)        ← 폼 제출과 같은 entry list
     .append(name, 문자열)  ·  .append(name, Blob, filename?)   ← Blob 은 File 이 된다(이름 없으면 "blob")
     .get · .getAll · .set · .delete · .has · 순회

   JSON 을 보낼 때의 관용구
     fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(x) })
```

### 어디서 헷갈리나

- **`FormData` 에는 `Content-Type` 을 쓰지 않는다** — 쓰면 boundary 가 빠진다((2)).
- **JSON 에는 `Content-Type` 을 쓴다** — 안 쓰면 `text/plain` 이다((1)).
- 둘이 **정반대 처방**이라 헷갈린다 — 기준은 하나다: **「브라우저가 붙일 줄 아는 값이면 맡기고, 모르는 값이면 쓴다」.**

## 어디서 틀리나

### 1. `FormData` 에 `Content-Type: multipart/form-data` 를 적는다

**boundary 가 빠져 서버가 못 가른다**((2)) — 본문은 멀쩡해서 **요청 로그만 보면 정상**이다.

### 2. `JSON.stringify` 만 넘기고 서버가 JSON 으로 받기를 기다린다

**`text/plain;charset=UTF-8`** 이다((1)). 서버가 `Content-Type` 으로 고르면 JSON 파서가 안 돈다.

### 3. `ArrayBuffer`·타입 없는 `Blob` 에도 브라우저가 무언가 붙여 줄 거라 믿는다

**아무것도 안 붙는다**((1)). 서버의 기본값에 맡겨진다.

### 4. `fetch(new FormData(form))` 과 폼 제출은 본문이 다를 거라 믿는다

**boundary 만 빼면 한 글자도 같다**((4)) — 체크 안 된 체크박스가 빠지는 것까지.

### 5. 파일 칸의 `filename` 을 서버가 정한다고 믿는다

**클라이언트가 원문에 적어 보낸다** — `Blob` 이면 `"blob"`, `File` 이면 그 `name`((3)). 서버는 **신뢰할 수 없는 입력**으로 받아야 한다.

### 6. 「다른 언어 클라이언트도 똑같이 알아서 붙인다」

**`urllib` 는 JSON 바이트에 폼 타입을 붙인다**((5)). 「자동」은 클라이언트마다 다르다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 본문 종류별 자동 `Content-Type` 다섯 | **명세**(Fetch — extract a body) · 이 판도 그랬다((1)) |
| ★ `Content-Type` 을 직접 쓰면 자동 값이 안 붙는다 → `FormData` 의 boundary 가 빠진다 | **명세**(Fetch — Request 생성자 「없을 때만 붙인다」) · ★ **서버 로그가 증명**((2)) |
| boundary 의 모양(`----WebKitFormBoundary` + 16자) | ★ **Chrome 의 글자** — 명세는 「알고리즘이 만든 boundary 문자열」까지만 말한다 |
| `Blob` → 이름 `"blob"` 인 `File` · 파일 아닌 칸에 `Content-Type` 없음 · 체크 안 된 체크박스 제외 | **명세**(HTML — create an entry · multipart 인코딩 · constructing the entry list) · 이 판도 그랬다((3)·(4)) |
| 파일 칸 `type` 이 비면 `application/octet-stream` | ★ **이 판의 관찰**(RFC 7578 은 열지 않았다) |
| `new FormData(form)` 과 폼 제출의 원문이 같다 | **명세**(같은 entry list · 같은 인코딩) · ★ **원문 대조가 증명**((4)) |
| `urllib` 의 자동 `application/x-www-form-urlencoded` · `requests` 의 boundary | ★ **각 라이브러리의 설계** — 이 판의 관찰((5)) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 파일이 섞인 폼 · 폼 그대로 | `new FormData(form)` · `Content-Type` 안 씀 | `Content-Type: multipart/form-data` |
| 짧은 키·값(파일 없음) | `URLSearchParams` | 손으로 `a=1&b=…` 이어 붙이기 |
| JSON API | `JSON.stringify` + `Content-Type: application/json` | `JSON.stringify` 만 |
| 파일 하나를 그대로 | `body: file`(`Content-Type` 은 파일의 `type`) — 31편 | 파일을 문자열로 읽어 보내기 |
| 바이트(`ArrayBuffer`) | `Content-Type` 을 직접 | 서버 기본값에 맡기기 |

## 핵심 문장

1. **본문의 종류가 `Content-Type` 을 정한다** — `FormData` 는 boundary 까지, 문자열은 `text/plain;charset=UTF-8`, 바이트는 없음.
2. **직접 쓰면 자동 값은 안 붙는다** — `FormData` 에서만 그것이 사고다(직접 써서 서버 파싱이 깨진 본문 1 / 7).
3. **boundary 가 빠져도 본문은 한 글자도 같다** — 송장만 다르다. 브라우저 쪽에는 예외도 경고도 없다.
4. **`new FormData(form)` 은 폼 제출과 같은 본문을 만든다** — boundary 만 빼고.
5. **`JSON.stringify` 만 넘기면 `text/plain`** — 다른 출처로는 프리플라이트 없는 단순 요청이다(28편).

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 30번)
- [HTML 21번 주제](../../languages/html/syntax/21-form-submission-model/2-summary.md) — **폼 제출이 만드는 본문의 정본**(`method` × `enctype`). 그쪽은 **마크업**, 여기는 **같은 본문을 스크립트로**
- [28번 주제](../28-cors-simple-and-preflight/2-summary.md) — `Content-Type` 값이 프리플라이트를 정한다((6)) · 하네스 (1)
- [25번 주제](../25-fetch-request-response/2-summary.md) — `fetch` 의 옵션과 `Request`(한 번 쓴 본문은 다시 못 쓴다)
- [31번 주제](../31-blob-file-and-object-url/2-summary.md) — 파일 입력의 `File` 을 **그대로** 올리는 쪽

## 용어 풀이

- **`Content-Type`** — 본문이 무슨 형식인지 알리는 헤더. 서버가 파서를 고르는 근거.
- **boundary** — multipart 본문의 칸을 가르는 글자. 본문 안에 `--boundary` 로 나오고 `Content-Type` 에 `boundary=` 로 적힌다.
- **`multipart/form-data`** — 칸마다 머리(이름·파일 이름·타입)와 값을 boundary 로 갈라 싣는 형식. 파일을 실을 수 있다.
- **`application/x-www-form-urlencoded`** — `a=1&b=%ED%95%9C` 꼴. 파일을 못 싣는다.
- **entry list** — 폼이나 `FormData` 가 가진 (이름, 값) 목록. 폼 제출과 `new FormData(form)` 이 같은 것을 만든다.
- **자동 `Content-Type` 격자** — 본문 일곱 × 직접 쓰나 = 14칸 × (받은 `Content-Type` · 서버 파싱). 이 편의 본체.

## 더 들어가면

- **`text/plain` 폼 인코딩**과 **UTF-8 이 아닌 폼**은 HTML 21편 · 목록 밖이다.
- **`FormData` 의 `filename` 에 `"` · 줄바꿈이 들어가면** `%22`·`%0A` 로 바뀐다(명세) — 던지지 않았다.
- **업로드 진행률**은 `fetch` 로는 스트림 업로드가 필요하다(28편 (3) — HTTP/1.1 에서는 안 나갔다).
