# web-api/26 — 응답 본문과 스트리밍: `json()`/`text()`/`blob()` 은 한 번만·`body` 와 `ReadableStream` — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」를 페이지가 직접 묻는 판 — 청크를 받을 때마다 「이때 서버는 몇 개 보냈나 · 끝까지 다 썼나」를 서버에게 물어 한 줄로 나란히 적는 「청크 대조」다.** 서버는 헤더를 곧바로 보내고, 청크와 끝 표시는 **페이지가 `/go` 를 줄 때마다 하나씩** 보낸다 — 시간이 아니라 신호로 묶었으므로 「받았을 때 서버가 아직 다 안 보냈다」가 흔들리지 않는다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 Body 믹스인(「body 가 null 이 아니고 그 stream 이 **disturbed 또는 locked** 이면 **unusable**」 · 「consume body — **unusable 이면 TypeError 로 거부된 프라미스**」) · 「clone a body — 그 stream 을 **tee** 해서 하나는 자기가, 하나는 복사본이 갖는다」 · [WHATWG Streams](https://streams.spec.whatwg.org/) 의 `tee()`(「두 소비자가 **다른 속도로** 읽을 수 있게」 · 「**두 가지가 모두 안 읽힐 때에만** 원본에 배압 신호」) · 「lock 을 풀면 **안 읽은 청크는 큐에 남아 새 reader 로 읽을 수 있다**」. 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 청크 서버는 로컬 서버 A 의 `/chunks` 다(`Transfer-Encoding: chunked`). 하네스는 [24번 주제](../24-document-lifecycle-events/2-summary.md)의 (1)에 있다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — [25번 주제](../25-fetch-request-response/2-summary.md)(`fetch` 는 **응답 헤더가 오면** 이행한다 · 한 번 쓴 `Request` 는 다시 못 쓴다). `for await` 문법은 [JS 40번 주제](../../languages/js/syntax/40-async-iteration-and-for-await/2-summary.md)가 정본이다 — 그 편은 비동기 이터레이터의 `return()`·거부를 쟀고, 이 편은 `ReadableStream` 을 **reader 로** 읽는다(`for await` 로 스트림을 도는 것은 던지지 않았다).\
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
| **안 흔들린다** | 두 번 읽기의 예외 전문 · `bodyUsed`/`locked` · 청크 대조 여섯 줄 · `text()` 정착 여섯 줄 · 쪼개진 한글 세 방법 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들렸다가 고쳤다** | 청크 대조의 **첫 줄과 마지막 줄** | 처음 판은 **첫 청크를 헤더와 함께 곧바로** 보내 「fetch 정착 때 보낸 수」가 0 과 1 사이에서 갈릴 수 있었고, 끝 표시 뒤 「다 썼나」도 서버가 표시를 세우기 전에 물을 수 있었다. **청크와 끝 표시를 전부 `/go` 뒤로** 미루고, 서버가 **쓰기 전에** 센 수를 답하게 고쳤다 |
| **흔들린다** | Chrome 판 번호 | 판이 오르면 바뀐다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `bodyUsed` · `body.locked` · `blob.size` |
| 창 ③ 같은 것을 두 번 읽기 | ★★ **쓴다 — 주제 그 자체** | 같은 본문을 `json()` 두 번 · `clone()` 뒤 두 쪽 |
| **창 ④ 서버 요청 로그 — 청크 대조** | ★★★ **본체** | 청크를 받은 **그때** 서버는 몇 개 보냈나 · 끝까지 썼나 |
| ★ **바이트 조각 길이** | ★ **쓴다** | 한 번의 `read()` 가 몇 바이트인가 — 글자 중간에서 잘렸나 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★ **`clone()` 뒤 안 읽은 쪽이 먹는 메모리** | 쌓인다는 것은 **명세 문장과 「나중에 읽어도 다 있었다」** 로만 봤다((5)). **바이트 수는 재지 않았다** |
| **「스트리밍이 빠르다」** | **재지 않았다.** 이 편이 본 것은 「**끝을 기다리지 않고** 받는다」라는 순서다 |
| **중간 장비가 청크를 모으는 것**(프록시·압축) | 루프백만 썼다 |
| **아주 큰 청크가 여러 `read()` 로 쪼개지는 것** | 청크를 5바이트로 작게 보냈다 |

## 한눈에 — 쉽게 말하면

**★ 응답 본문은 「한 번 흐르는 수도관」이다. `json()`·`text()` 는 물통을 다 채운 뒤에 건네주고, 그러고 나면 관은 비어 있다 — 두 번 받을 수 없다. `body.getReader()` 는 관에 컵을 대고 물이 오는 대로 한 컵씩 받는다. `clone()` 은 관을 두 갈래(tee) 로 나눈다 — 한 갈래만 마시면 다른 갈래의 물은 고여서 기다린다.**

| 비유 | 실체 |
|---|---|
| 한 번 흐르는 관 | `res.body` — `ReadableStream` |
| 물통을 다 채워 건넴 | `json()` · `text()` · `blob()` · `arrayBuffer()` — **끝까지 기다린다** |
| 「이미 흘러갔다」 | `bodyUsed=true` → 두 번째는 `TypeError 「body stream already read」` |
| 컵을 대고 한 컵씩 | `getReader().read()` — 청크마다 |
| 누가 컵을 대고 있다 | `body.locked=true` → `text()` 가 `TypeError 「body stream is locked」` |
| 두 갈래 | `clone()`(안에서 `tee()`) |
| 글자가 컵 경계에서 잘림 | 한 글자(3바이트)가 두 청크에 걸침 — `TextDecoderStream` 이 이어 붙인다 |

```text
   ★ 청크 다섯 — reader 는 오는 대로, text() 는 끝에서 한 번 (이 판)

   서버        헤더 ─ 줄1 ─ 줄2 ─ 줄3 ─ 줄4 ─ 줄5 ─ 끝
                │     │     │     │     │     │     │
   reader     (정착) read  read  read  read  read  done     ← 서버가 아직 다 안 보냈을 때마다 받는다
   text()     (정착) ····· ····· ····· ····· ····· 「줄1…줄5」 ← 끝 표시가 온 뒤에야 한 번
```

## 이 주제가 답하려는 질문

1. **본문을 두 번 읽으면 왜 실패하나** — 무엇이 「이미 읽었다」를 정하나, `clone()` 은 무엇을 하나.
2. **청크 단위로 읽으면 무엇이 달라지나** — 받는 시점이 서버가 보내는 시점과 어떻게 맞물리나.
3. **글자가 청크 경계에서 잘리면** 어떻게 이어 읽나.

## 동작 방식

### (1) ★★★ 본문은 한 번만 — 두 번 읽기의 전문

**언제 쓰나** — 「로그에 한 번 찍고 다시 `json()` 했더니 터진다」일 때.

```html
<!-- wa24b-26-once.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>26 once</title>
<script>
// 본문은 한 번만 — 두 번 읽기 · bodyUsed · clone 으로 두 번 · 읽은 뒤의 clone · reader 를 쥔 채 text()
const 이름 = e => e.name + " 「" + e.message + "」";
const 시도 = async (O, 글, f) => { try { O.push(글 + " → " + JSON.stringify(await f())); } catch (e) { O.push(글 + " → " + 이름(e)); } };
window.__끝 = async () => {
  const O = [];
  const r = await fetch("/status?code=200");
  O.push("가. 읽기 전 bodyUsed=" + r.bodyUsed);
  await 시도(O, "   첫 json()", () => r.json());
  O.push("   읽은 뒤 bodyUsed=" + r.bodyUsed);
  await 시도(O, "   둘째 json()", () => r.json());
  await 시도(O, "   그 뒤 text()", () => r.text());
  await 시도(O, "   그 뒤 clone()", () => r.clone());

  const s = await fetch("/status?code=200");
  const 복 = s.clone();
  await 시도(O, "나. clone 뒤 원본 json()", () => s.json());
  await 시도(O, "   clone 뒤 복사본 text()", () => 복.text());

  const t = await fetch("/status?code=200");
  const 읽개 = t.body.getReader();
  O.push("다. getReader() 뒤 body.locked=" + t.body.locked + " · bodyUsed=" + t.bodyUsed);
  await 시도(O, "   reader 를 쥔 채 text()", () => t.text());
  읽개.releaseLock();
  await 시도(O, "   releaseLock() 뒤 text()", () => t.text());

  const u = await fetch("/status?code=200");
  const b = await u.blob();
  O.push("라. blob() → size=" + b.size + " · type=" + JSON.stringify(b.type));
  await 시도(O, "   그 뒤 arrayBuffer()", () => u.arrayBuffer());
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-26-once.html
가. 읽기 전 bodyUsed=false
   첫 json() → {"status":200}
   읽은 뒤 bodyUsed=true
   둘째 json() → TypeError 「Failed to execute 'json' on 'Response': body stream already read」
   그 뒤 text() → TypeError 「Failed to execute 'text' on 'Response': body stream already read」
   그 뒤 clone() → TypeError 「Failed to execute 'clone' on 'Response': Response body is already used」
나. clone 뒤 원본 json() → {"status":200}
   clone 뒤 복사본 text() → "{\"status\": 200}"
다. getReader() 뒤 body.locked=true · bodyUsed=false
   reader 를 쥔 채 text() → TypeError 「Failed to execute 'text' on 'Response': body stream is locked」
   releaseLock() 뒤 text() → "{\"status\": 200}"
라. blob() → size=15 · type="application/json"
   그 뒤 arrayBuffer() → TypeError 「Failed to execute 'arrayBuffer' on 'Response': body stream already read」
--- 서버 로그 ---
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=200  → 200 응답을 끝까지 보냈다
A GET /status?code=200  → 200 응답을 끝까지 보냈다
(exit 0)
```

- ★★★ **두 번째 `json()` 은 `TypeError 「Failed to execute 'json' on 'Response': body stream already read」`**, 그 뒤 `text()` 도 같은 문구, **`clone()` 은 `TypeError 「… Response body is already used」`** — 다 읽은 본문은 **복사도 못 한다.**
- **`bodyUsed` 는 읽기 전 `false`, 첫 `json()` 뒤 `true`.**
- ★★ **`clone()` 을 먼저 뜨면 두 쪽 다 읽힌다** — 원본 `json()` 과 복사본 `text()` 가 같은 본문을 돌려줬다.
- ★★ **`getReader()` 만 해도 `text()` 가 막힌다** — `locked=true` 인데 `bodyUsed` 는 아직 `false` 다. 문구도 다르다: **`body stream is locked`**. `releaseLock()` 하자 `text()` 가 **전부** 읽었다 — 명세의 「lock 을 풀면 안 읽은 청크는 큐에 남는다」 그대로.
- **`blob()` 뒤 `arrayBuffer()` 도 `already read`** — 읽는 메서드끼리 한 본문을 나눠 쓰지 않는다.
- ★ Fetch 명세 — **disturbed(읽기 시작함) 또는 locked 면 unusable, 소비는 unusable 이면 `TypeError` 로 거부**. `already read` 와 `is locked` 는 그 두 갈래에 대응한다(문구는 Chrome 의 것).

```text
   본문의 세 상태 (이 판)

   처음              bodyUsed=false  locked=false   ─▶ json() · text() · clone() 전부 됨
   reader 를 쥠      bodyUsed=false  locked=true    ─▶ text() ✕ 「body stream is locked」
   한 번 읽음        bodyUsed=true                  ─▶ json() · text() ✕ 「already read」 · clone() ✕ 「already used」
   ★ 두 번 쓰려면 읽기 「전에」 clone()
```

### (2) ★★★ 본체 — 청크 대조: 받을 때 서버는 아직 다 안 보냈다

**던진 것** — 서버는 헤더를 곧바로 보내고, **청크(「줄1\n」…「줄5\n」) 다섯과 끝 표시를 `/go` 하나에 하나씩** 보낸다. 페이지는 `/go` → `read()` → **서버에게 「보낸 수 · 끝까지 다 썼나」** 를 묻는다.

```html
<!-- wa24b-26-stream.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>26 stream</title>
<script>
// 서버는 헤더를 곧바로 보내고, 청크 다섯과 끝 표시는 페이지가 /go 를 줄 때마다 하나씩 보낸다
// 페이지는 청크를 하나 받을 때마다 서버에게 「지금 몇 개 보냈나 · 끝까지 다 썼나」를 묻는다
const 서버 = async id => (await fetch(`/state?id=${id}`)).json();
window.__끝 = async () => {
  const O = [];
  const res = await fetch("/chunks?id=s1&n=5");
  O.push("fetch 가 정착(status=" + res.status + ") — 이때 서버가 보낸 청크 = " + (await 서버("s1")).sent + " / 5");
  const 읽개 = res.body.getReader();
  const 풀개 = new TextDecoder();
  for (let k = 1; ; k++) {
    await fetch("/go?id=s1");                            // 다음 것을 보내라
    const { value, done } = await 읽개.read();
    if (done) { O.push(`read() ${k}번째 → done=true`); break; }
    const 상태 = await 서버("s1");
    O.push(`read() ${k}번째 → ${value.length}바이트 ${JSON.stringify(풀개.decode(value))}` +
           ` · 이때 서버가 보낸 청크 = ${상태.sent} / 5 · 끝까지 다 썼나 = ${상태.done}`);
  }
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-26-stream.html
fetch 가 정착(status=200) — 이때 서버가 보낸 청크 = 0 / 5
read() 1번째 → 5바이트 "줄1\n" · 이때 서버가 보낸 청크 = 1 / 5 · 끝까지 다 썼나 = false
read() 2번째 → 5바이트 "줄2\n" · 이때 서버가 보낸 청크 = 2 / 5 · 끝까지 다 썼나 = false
read() 3번째 → 5바이트 "줄3\n" · 이때 서버가 보낸 청크 = 3 / 5 · 끝까지 다 썼나 = false
read() 4번째 → 5바이트 "줄4\n" · 이때 서버가 보낸 청크 = 4 / 5 · 끝까지 다 썼나 = false
read() 5번째 → 5바이트 "줄5\n" · 이때 서버가 보낸 청크 = 5 / 5 · 끝까지 다 썼나 = false
read() 6번째 → done=true
--- 서버 로그 ---
A GET /chunks?n=5  도착
A   청크 5개와 끝 표시까지 썼다
(exit 0)
```

- ★★★ **`fetch` 가 정착할 때 서버가 보낸 청크는 0 / 5** — `fetch` 는 **헤더가 오면** 이행한다. 본문은 아직 한 바이트도 없다.
- ★★★ **`read()` 다섯 번 모두 「끝까지 다 썼나 = false」** — 청크 k 를 받은 그때 서버는 **k 개만** 보냈다. 서버가 다음 것을 보내지 않으면 페이지는 **그 청크를 쥔 채 기다리지 않고 이미 받았다.**
- **여섯 번째 `read()` 가 `done=true`** — 끝 표시(`0\r\n\r\n`)가 왔다.
- ★ 이 대조는 **흔들리지 않게 만들었다** — 서버는 `/go` 없이 다음 청크를 **못 보낸다.** 만약 브라우저가 본문을 끝까지 모아서 줬다면 페이지는 첫 `read()` 에서 **영영 멈췄을** 것이다(`/go` 를 줄 사람이 없다).

```text
   ★ 페이지와 서버 — 청크 대조 (시간은 아래로)

   페이지                              서버 A
   fetch ─────────────────────────▶   도착 · 헤더 200
   (정착) 「보낸 수?」 ────────────▶   0 / 5
   /go ───────────────────────────▶   줄1 쓰기
   read() ◀── 「줄1\n」
   「보낸 수?」 ───────────────────▶   1 / 5 · 끝 아님      ★ 받은 그때 서버는 아직 다 안 보냈다
   /go … read() … (다섯 번)
   /go ───────────────────────────▶   끝 표시 쓰기
   read() ◀── done
```

### (3) ★★ `text()` 는 끝을 기다린다 — 같은 서버에

```html
<!-- wa24b-26-whole.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>26 whole</title>
<script>
// 같은 서버에 text() 로 — 청크를 하나씩 풀어 주고, 서버가 보냈다고 말한 뒤마다 text() 가 정착했나 본다
const 서버 = async (id, 기다림) => (await fetch(`/state?id=${id}&wait=${기다림}`)).json();
window.__끝 = async () => {
  const O = [];
  const res = await fetch("/chunks?id=w1&n=5");
  let 정착 = false;
  const 글 = res.text().then(t => { 정착 = true; return t; });
  for (let k = 1; k <= 5; k++) {
    await fetch("/go?id=w1");
    const 상태 = await 서버("w1", `sent:${k}`);
    O.push(`서버가 청크 ${상태.sent} / 5 를 보낸 뒤 — text() 정착 = ${정착}`);
  }
  await fetch("/go?id=w1");                              // 끝 표시
  await 서버("w1", "done");
  O.push("서버가 끝 표시까지 보낸 뒤 — text() 가 돌려준 것 = " + JSON.stringify(await 글));
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-26-whole.html
서버가 청크 1 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 2 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 3 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 4 / 5 를 보낸 뒤 — text() 정착 = false
서버가 청크 5 / 5 를 보낸 뒤 — text() 정착 = false
서버가 끝 표시까지 보낸 뒤 — text() 가 돌려준 것 = "줄1\n줄2\n줄3\n줄4\n줄5\n"
--- 서버 로그 ---
A GET /chunks?n=5  도착
A   청크 5개와 끝 표시까지 썼다
(exit 0)
```

- ★★ **서버가 청크 1\~5 를 보낸 뒤마다 `text()` 는 정착하지 않았다**(다섯 번 전부 `false`). **끝 표시까지 보낸 뒤에야** 다섯 줄 전부를 한 번에 돌려줬다.
- 그래서 **진행률 표시·첫 줄부터 그리기·조기 중단**은 `text()`/`json()` 으로는 안 된다 — **reader 로** 한다((2)).
- ★ 이 블록이 말하는 것은 **순서**다. 「reader 가 더 빠르다」는 **재지 않았다**(머리말 표).

```text
   같은 서버 · 소비자 둘 — 무엇을 언제 받나 (이 판)

   서버가 보낸 것    줄1    줄2    줄3    줄4    줄5    끝
   reader           줄1    줄2    줄3    줄4    줄5    done
   text()           ·      ·      ·      ·      ·      「줄1…줄5」
                    (정착 false 다섯 번)                ← 여기서 한 번
```

### (4) ★★ 글자가 청크 경계에서 잘리면 — `TextDecoderStream`

**던진 것** — 서버가 「가나\n」 일곱 바이트를 **2 · 2 · 3 바이트**로 쪼개 보낸다(「가」·「나」는 3바이트씩이라 **글자 중간에서** 잘린다). `body.tee()` 로 둘로 나눠 **갑은 바이트째 읽으며 `/go` 를 주고, 을은 `TextDecoderStream` 에 물려 갑이 다 읽은 뒤에** 읽는다.

```html
<!-- wa24b-26-decode.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>26 decode</title>
<script>
// 「가나\n」 일곱 바이트를 서버가 2 · 2 · 3 바이트로 쪼개 보낸다 — 글자 중간에서 잘린다
// body 를 tee() 로 둘로 — 갑은 바이트째 읽으며 청크마다 /go 를 주고, 을은 TextDecoderStream 에 물려 나중에 읽는다
window.__끝 = async () => {
  const O = [];
  const res = await fetch("/chunks?id=d1&split=1");
  const [갑, 을] = res.body.tee();
  const 날것 = [];
  const 읽개 = 갑.getReader();
  for (;;) {
    await fetch("/go?id=d1");                            // 다음 조각을 보내라
    const { value, done } = await 읽개.read();
    if (done) break;
    날것.push(value);
  }
  O.push("가. 바이트 조각 길이 = " + JSON.stringify(날것.map(v => v.length)));
  O.push("   조각마다 new TextDecoder().decode() → " + JSON.stringify(날것.map(v => new TextDecoder().decode(v))));
  const 이어 = new TextDecoder();
  O.push("나. 한 TextDecoder 에 {stream:true} → " + JSON.stringify(날것.map(v => 이어.decode(v, { stream: true }))));
  const 글 = [];
  const 을읽개 = 을.pipeThrough(new TextDecoderStream()).getReader();   // 을은 여태 안 읽혔다
  for (;;) { const { value, done } = await 을읽개.read(); if (done) break; 글.push(value); }
  O.push("다. 을.pipeThrough(new TextDecoderStream()) → " + JSON.stringify(글));
  return O.join("\n");
};
</script>
```

```text
$ python3 wa24b-net.py page wa24b-26-decode.html
가. 바이트 조각 길이 = [2,2,3]
   조각마다 new TextDecoder().decode() → ["�","��","��\n"]
나. 한 TextDecoder 에 {stream:true} → ["","가","나\n"]
다. 을.pipeThrough(new TextDecoderStream()) → ["가","나\n"]
--- 서버 로그 ---
A GET /chunks?split=1  도착
A   청크 3개와 끝 표시까지 썼다
(exit 0)
```

- ★★★ **조각마다 `new TextDecoder().decode()` 하면 `["�","��","��\n"]`** — 잘린 바이트가 **대체 문자(�)** 가 됐다. 오류도 경고도 없다.
- ★★ **한 `TextDecoder` 에 `{ stream: true }` 로 이어 주면 `["","가","나\n"]`** — 첫 조각에서는 **아무것도 안 내고** 기다렸다가 다음 조각과 이어 붙였다.
- ★★ **`pipeThrough(new TextDecoderStream())` 은 `["가","나\n"]`** — 같은 일을 스트림으로 한다. 빈 조각은 **안 내보냈다.**
- ★ **을은 갑이 다 읽을 동안 한 번도 안 읽혔는데 조각이 다 있었다** — `tee()` 의 한 갈래가 **안 읽히는 동안 고여 있었다.** 이것이 (5)의 「쌓인다」의 행동 근거다.

```text
   「가나\n」 = EA B0 80 · EB 82 98 · 0A     서버가 2 · 2 · 3 으로 자름

   조각      EA B0 │ 80 EB │ 82 98 0A
   따로 풂    �    │  � �  │  � � \n        ✕ 경계에서 깨짐
   이어 풂    ""   │  가   │  나\n          ○ {stream:true} · TextDecoderStream
```

### (5) `clone()` 의 값 — 안 읽은 갈래는 고인다

- Fetch 명세 — **「clone a body: 그 stream 을 tee 해서 하나는 자기, 하나는 복사본」**. 그러니 `res.clone()` 은 `res.body.tee()` 와 같은 일을 한다.
- Streams 명세 — `tee()` 는 **「두 소비자가 다른 속도로 읽게」** 하는 것이고, **「두 갈래가 모두 안 읽힐 때에만」** 원본에 배압 신호가 간다. ★ 즉 **한 갈래만 읽으면 원본은 계속 흐르고, 안 읽힌 갈래의 큐에 청크가 고인다.**
- **이 판에서 본 것** — (4)의 을이 갑이 다 읽을 때까지 안 읽혔는데 **조각이 전부 남아 있었다.** 얼마나 먹는지는 **재지 않았다.**
- ★ 그래서 **큰 응답을 `clone()` 해 한쪽만 읽고 다른 쪽을 버려 두지 마라** — 버린 쪽은 `cancel()` 하거나 처음부터 뜨지 않는다.

```text
   clone() = tee() — 한 갈래만 읽으면

   원본 스트림 ─┬─▶ 갑(읽힘)      청크가 오는 대로 나간다
                └─▶ 을(안 읽힘)   [청크1][청크2][청크3]…   ← 큐에 고인다
   배압이 원본에 가는 때 = 「두 갈래가 모두 안 읽힐 때」 뿐 (Streams — tee)
   ★ 이 판은 「나중에 읽어도 다 있었다」만 봤다 — 바이트 수는 재지 않았다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   한 번에       res.json() · res.text() · res.blob() · res.arrayBuffer() · res.formData() · res.bytes()
   상태          res.bodyUsed · res.body.locked
   복사          res.clone()                       ← 읽기 「전에」
   흘려 읽기     const r = res.body.getReader();  const { value, done } = await r.read();  r.releaseLock();
   풀어 읽기     res.body.pipeThrough(new TextDecoderStream()).getReader()
                new TextDecoder().decode(조각, { stream: true })
   가르기        const [갑, 을] = res.body.tee();

   관용구 — 진행률
     const r = res.body.getReader(); let 받음 = 0;
     for (;;) { const { value, done } = await r.read(); if (done) break; 받음 += value.length; 그리기(받음); }
```

### 어디서 헷갈리나

```text
   본문 한 개 — 누가 가져갔나로 갈린다

   아무도 안 가져감            → 무엇이든 한 번 · clone() 가능
   reader 가 쥐고 있음          → text() ✕ is locked      (releaseLock 하면 다시 됨)
   한 번 다 가져감             → 전부 ✕ already read · clone ✕ already used
```

- **`bodyUsed` 가 `false` 여도 못 읽을 수 있다** — reader 가 쥐고 있으면(`locked`)((1)).
- **`fetch` 가 정착했다고 본문이 온 것이 아니다** — 헤더만 왔다((2)).
- **조각마다 따로 풀면 한글이 깨진다**((4)).

## 어디서 틀리나

### 1. 로그에 찍으려고 `await res.text()` 한 뒤 `res.json()` 한다

**`TypeError 「body stream already read」`**((1)). 한 번 읽어 **변수에 두고** 쓰거나, 읽기 전에 `clone()` 한다.

### 2. 다 읽은 뒤 `clone()` 한다

**`TypeError 「Response body is already used」`**((1)). `clone()` 은 **읽기 전에만** 된다.

### 3. `getReader()` 를 해 두고 `json()` 도 부른다

**`TypeError 「body stream is locked」`**((1)). 한 본문에는 **한 소비자**다.

### 4. 청크를 받을 때마다 `new TextDecoder().decode(청크)` 한다

**글자가 경계에서 잘리면 `�`** 가 된다((4)). 오류가 없어서 **한국어·이모지를 쓰는 사용자만** 깨진 화면을 본다. `{ stream: true }` 나 `TextDecoderStream` 을 쓴다.

### 5. `text()` 로 진행률을 그리려 한다

**`text()` 는 끝 표시가 온 뒤에야 한 번 정착한다**((3)). 진행률은 reader 로 센다.

### 6. `clone()` 하고 한쪽만 읽는다

**안 읽은 갈래에 고인다**((5)). 큰 응답이면 그만큼 붙든다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 한 번 읽은(disturbed)·잠긴(locked) 본문은 unusable → 소비는 `TypeError` | **명세**(Fetch — Body 믹스인 · consume body) · 이 판도 그랬다((1)) |
| `clone()` 은 unusable 이면 `TypeError` · 안에서 `tee` | **명세**(Fetch — clone · clone a body) · 이 판도 그랬다((1)) |
| lock 을 풀면 안 읽은 청크가 남아 다시 읽힌다 | **명세**(Streams — releaseLock) · 이 판도 그랬다((1)) |
| `tee` 의 한 갈래만 읽으면 다른 갈래에 고인다 | **명세**(Streams — 두 갈래가 모두 안 읽힐 때만 배압) · 이 판은 **행동만** 봤다((4)) |
| `fetch` 가 헤더에서 정착 · 청크가 오는 대로 `read()` | ★ **명세의 틀**(응답 본문은 스트림) · ★ **이 판의 대조**((2)) — 청크를 **몇 개씩 묶어 주나**는 구현이다 |
| 오류 문구(`already read` · `is locked` · `already used`) | ★ **Chrome 의 글자** |
| `TextDecoderStream` 이 빈 조각을 안 내보낸 것 | ★ **이 판의 관찰** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 작은 JSON 한 번 | `await res.json()` | reader |
| 같은 본문을 두 곳에서 | 한 번 읽어 변수 · 또는 읽기 전 `clone()` | 두 번 읽기 |
| 진행률 · 첫 줄부터 그리기 · 조기 중단 | `getReader()` · `for await`(JS 40) | `text()` |
| 글자 스트림 | `pipeThrough(new TextDecoderStream())` | 청크마다 새 `TextDecoder` |
| 캐시에 넣고 화면에도 | `clone()` 뒤 **두 쪽 다** 끝까지 | 한쪽을 버려 두기 |

## 핵심 문장

1. **본문은 한 번 흐른다** — 두 번째 `json()` 은 `TypeError 「body stream already read」`, 다 읽은 뒤 `clone()` 은 `already used`.
2. **reader 를 쥐기만 해도 잠긴다** — `bodyUsed=false` 인데 `text()` 가 `is locked`.
3. **`fetch` 는 헤더에서 정착하고, reader 는 청크를 받을 때마다 받는다** — 받은 그때 서버는 아직 다 안 보냈다(다섯 번 전부).
4. **`text()`·`json()` 은 끝 표시를 기다린다.**
5. **청크 경계에서 글자가 잘린다** — 따로 풀면 `�`, 이어 풀면(`stream:true`·`TextDecoderStream`) 멀쩡하다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 26번)
- [25번 주제](../25-fetch-request-response/2-summary.md) — `fetch` 의 이행·거부와 `Request` 의 한 번 쓰기
- [27번 주제](../27-abort-and-timeout/2-summary.md) — **본문을 읽는 중에 취소하면**(`read()` 가 `AbortError`)
- [JS 40번 주제](../../languages/js/syntax/40-async-iteration-and-for-await/2-summary.md) — **`for await` 의 정본.** 그쪽은 비동기 이터레이션 규약, 여기는 `ReadableStream` 의 reader
- [`../../../ops-patterns/05-backpressure/`](../../../ops-patterns/05-backpressure/) — **배압 일반론의 정본.** 그쪽은 생산자·소비자 설계, 여기는 **`tee` 의 한 갈래가 고이는 자리** 하나

## 용어 풀이

- **`ReadableStream`** — 조각(청크)을 차례로 내주는 스트림. `res.body` 가 이것이다.
- **청크** — 한 번의 `read()` 가 주는 조각(`Uint8Array`).
- **disturbed** — 누가 읽기 시작한 스트림. `bodyUsed=true`.
- **locked** — reader 가 쥐고 있는 스트림. 다른 소비자는 못 읽는다.
- **`tee()`** — 스트림을 두 갈래로 나눈다. `clone()` 이 안에서 쓴다.
- **배압** — 소비자가 느릴 때 생산자에게 「그만 보내」를 전하는 것.
- **`TextDecoderStream`** — 바이트 스트림을 글자 스트림으로 바꾸며 **경계에서 잘린 글자를 이어 붙이는** 변환 스트림.
- **청크 대조** — 청크를 받을 때마다 서버에게 「몇 개 보냈나」를 물어 나란히 적은 것. 이 편의 본체.

## 더 들어가면

- **`res.bytes()`·`formData()`** 는 던지지 않았다.
- **`ReadableStream` 을 요청 본문으로 보내기**(`duplex: "half"`)는 던지지 않았다.
- **BYOB reader**(`getReader({ mode: "byob" })`)는 던지지 않았다.
