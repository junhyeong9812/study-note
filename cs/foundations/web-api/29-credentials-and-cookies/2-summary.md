# web-api/29 — 자격 증명과 `credentials`: 쿠키가 실리는 조건·와일드카드 금지 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ④ 「서버 요청 로그」 — 칸마다 「서버가 쿠키를 받았나」와 「페이지가 응답을 읽었나」를 나란히 놓는 「쿠키 실림 격자」다.** 받는 쪽 2(같은 사이트의 다른 출처 · 사이트 밖) × `credentials` 3 × 서버의 응답 헤더 4 = 24칸을 던지고, 마지막 줄을 스크립트가 **「서버는 쿠키를 받았는데 페이지는 못 읽은 칸 N / 24」** 로 찍는다.\
> **기준 소스** — [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 request 의 credentials mode(「`omit`·`same-origin`·`include` — **기본은 `same-origin`**」) · HTTP-network-or-cache fetch 의 includeCredentials(「**`include` 이거나, `same-origin` 이고 response tainting 이 `basic`** 이면 참」) · 「CORS check」(「credentials mode 가 `include` 가 아니고 `Access-Control-Allow-Origin` 이 `*` 면 성공 · 아니면 **요청 출처와 같아야** · `include` 면 **`Access-Control-Allow-Credentials` 가 `true` 여야**」) · CORS protocol 과 credentials 절(「**CORS-preflight request never includes credentials**」 · 허용·불허 조합 표). 열어서 확인한 것만 적었다(기준일 2026-09-26). ★ **쿠키 자체의 규칙(`SameSite`·`Secure`·서드파티 쿠키)은 HTTP 쿠키 명세(RFC 6265bis 초안)와 브라우저 정책의 몫이고 이 판에서 그 문서를 열지 않았다** — 그쪽 서술은 전부 **이 판의 관찰**로만 적는다.\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 페이지는 `http://127.0.0.1:<A>` 에서 열었고, 받는 쪽은 **같은 서버 B 를 두 이름으로** 부른다 — `http://127.0.0.1:<B>`(호스트가 같고 포트만 다름) · `http://localhost:<B>`(호스트가 다름). **바깥 인터넷으로는 한 번도 요청하지 않았다.** 하네스는 [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1)이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★★ **[28번 주제](../28-cors-simple-and-preflight/2-summary.md)** — 프리플라이트가 붙는 조건과 「거부되면 본 요청은 서버에 안 간다」. ★★ **[25번 주제](../25-fetch-request-response/2-summary.md)의 (5)가 쿠키 통을 이미 쟀다** — `fetch(…, { headers: { Cookie: "evil=1" } })` 의 `Cookie` 는 **예외 없이 지워지고 쿠키 통의 `jar=1` 이 갔다** · 응답의 `Set-Cookie` 는 `get()` 으로 `null` 인데 **쿠키 통에는 들어갔다**. 여기서는 그것을 **다시 재지 않고 인용**하고 — 쿠키는 헤더로 넣는 것이 아니라 **`credentials` 로 고르는 것** — **다른 출처로 언제 실리나**로 간다.\
> **경계** — ★ **CSRF 의 위협 모델과 방어 설계는 [`../../security/`](../../security/) 가 정본으로 걸려 있다** — 단 2026-09-26 현재 그 폴더에 **CSRF 절은 없다**(`csrf` 로 `grep` 해 0건). 여기는 (7)에서 **「쿠키가 실린 요청이 서버에서 처리됐다」까지만** 관찰로 보이고 방어 설계로 넘어가지 않는다.\
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
| **안 흔들린다** | 쿠키 통 준비 두 줄 · 격자 24칸 · 콘솔 · 서버 로그 · 차단 대조 · 프리플라이트 두 칸 | 캡처 세 판이 **한 글자도 같았다** |
| ★★ **판·설정에 매인 칸 — 흔들릴 수 있다** | **「사이트 밖」 + `include` 네 칸에 `none=1` 이 실리는 것** | 서드파티 쿠키를 막느냐는 **브라우저의 기본 설정·정책**이다 — 이 판(기본 프로필)에서는 실렸고, 그 탭에 CDP 스위치를 켜면 **네 칸이 바뀌었다**((5)). 판이 오르거나 정책이 바뀌면 이 네 칸부터 다시 찍는다 |
| ★ **판에 매인 칸** | `http` 에서 `Secure` 쿠키가 **저장되는 것**(두 이름 모두) | 쿠키 명세·Chrome 의 「안전한 곳으로 치는 주소」 목록에 매인다((1)) |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `document.cookie`(B 를 직접 열었을 때의 쿠키 통) · `then`/`catch` · `res.json()` |
| 창 ③ 같은 것을 두 번 읽기 | ★★ **쓴다** | **같은 격자를 두 탭에서** — 그대로 한 번 · 서드파티 쿠키를 막고 한 번((5)) |
| **창 ④ 서버 요청 로그 — 서버가 받은 `Cookie`** | ★★★ **본체** | 쿠키가 **실렸나** · 무엇이 실렸나 · 페이지가 못 읽은 칸에서도 실렸나 |
| ★ **「실렸나」를 페이지 대신 서버에게** | ★★ **같은 질문을 다른 창으로(제5의 상태)** | 페이지는 **나가는 요청의 `Cookie` 를 볼 수 없다**(금지 헤더 — 25편). 그래서 칸마다 서버에게 `/note` 로 물었다. ★ 바꾼 창이 못 보는 것 — **HttpOnly 여부 · 만료 · 쿠키가 「막혀서」 안 실렸는지 「없어서」 안 실렸는지**(서버는 빈 `Cookie` 만 안다 — (5)는 같은 쿠키 통으로 두 판을 견줘 가른다) |
| 콘솔(CDP Log 도메인) | ★★ **쓴다** | 거부 이유의 **세 문구**((3)) |
| 파이썬 대비 | **부적용** | 브라우저 밖 클라이언트의 쿠키는 **클라이언트가 쿠키 통을 들고 있느냐**의 문제라 이 표면과 겹치지 않는다(28편 (9)의 Go 대비로 갈음) |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★ **진짜 다른 등록 도메인(`a.example` 대 `b.example`)** | 루프백만 썼다. 「사이트 밖」은 **`127.0.0.1` 대 `localhost`** 로 흉내 냈다 — 호스트 이름이 달라 사이트가 갈린다는 것까지만 본다 |
| **https · 진짜 `Secure`** | 전부 `http` 다. `Secure` 쿠키가 **http 에서 저장·전송된 것**은 루프백 주소라서일 수 있다((1)) — 일반 http 사이트에서 어떤지는 이 판이 말하지 않는다 |
| **사용자의 서드파티 쿠키 설정 화면** | 설정 화면 대신 **CDP `Network.setCookieControls`** 로 그 탭만 막았다. 사용자가 켜는 스위치와 같은 경로인지는 모른다 |
| **서드파티 쿠키 휴리스틱 · 저장소 분할(CHIPS)** | 스위치에서 휴리스틱을 껐고 `Partitioned` 쿠키는 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ 쿠키는 「출입증」이다. 다른 건물(다른 출처)에 심부름을 보낼 때 출입증을 들려 보낼지는 내가 정하고(`credentials: 'include'`), 그 건물이 「출입증을 보고 준 답」을 나에게 보여 줄지는 그 건물이 정한다(`Access-Control-Allow-Credentials: true` + **내 이름을 콕 집은** `Allow-Origin`). 「아무에게나 보여 줘도 된다(`*`)」는 답은 출입증을 들고 간 심부름에는 안 통한다 — 그런데 심부름은 이미 출입증을 내밀었다.**

| 비유 | 실체 |
|---|---|
| 출입증을 들려 보낸다 | `credentials: "include"` |
| 같은 건물 안 심부름만 들려 보냄 | `credentials: "same-origin"`(기본) |
| 절대 안 들려 보냄 | `credentials: "omit"` |
| 「이 사람에게 보여 줘도 된다」 | `Access-Control-Allow-Origin: <정확한 출처>` |
| 「출입증을 보고 준 답도 보여 줘도 된다」 | `Access-Control-Allow-Credentials: true` |
| 「아무에게나」 | `Access-Control-Allow-Origin: *` — **`include` 에는 거부** |
| 출입증의 사용 범위 | 쿠키의 `SameSite` · `Secure` · 서드파티 쿠키 정책 |

```text
   ★ 쿠키가 실리는 것과 응답을 읽는 것은 서로 다른 문이다 (이 판)

   문 ① 실리나 — 페이지·브라우저가 정한다      문 ② 읽나 — 서버의 응답 헤더가 정한다
   credentials = include  ─┐                     ACAO = 정확한 출처 ─┐
   쿠키의 SameSite 허락   ─┼─▶ 서버가 쿠키를 받음  ACAC = true        ─┼─▶ 페이지가 읽음
   서드파티 쿠키 정책     ─┘                     (ACAO: * 는 탈락)  ─┘

   ★ 문 ①만 열리고 문 ②가 닫힌 칸 = 「서버는 쿠키를 받았는데 페이지는 못 읽은 칸」
```

## 이 주제가 답하려는 질문

1. **다른 출처 요청에 쿠키가 실리려면 양쪽이 각각 무엇을 해야 하나** — 페이지의 `credentials` · 쿠키의 속성 · 서버의 응답 헤더.
2. **`Access-Control-Allow-Origin: *` 와 `include` 는 왜 같이 못 쓰나** — 그리고 그때 서버에서는 무슨 일이 있었나.
3. **같은 사이트의 다른 출처와 사이트 밖은 어디서 갈리나** — 서드파티 쿠키 정책은 어느 칸을 바꾸나.

## 동작 방식

### (1) 쿠키 통 준비 — B 를 직접 두 이름으로 연다

**B 를 주소창으로 직접 연 것처럼**(퍼스트 파티로) 두 번 연다 — `127.0.0.1:<B>/setcookie` 와 `localhost:<B>/setcookie`. 응답은 쿠키 넷을 준다(서버 코드는 [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1) — `setcookie`):

```text
   Set-Cookie: lax=1;   Path=/; SameSite=Lax
   Set-Cookie: none=1;  Path=/; SameSite=None; Secure
   Set-Cookie: nosec=1; Path=/; SameSite=None          ← Secure 없음
   Set-Cookie: plain=1; Path=/                          ← SameSite 안 적음
```

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '1,2p'
B 를 127.0.0.1 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
B 를 localhost 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
(exit 0)
```

- ★★ **두 이름 모두 `lax`·`none`·`plain` 셋이 남았다 — `nosec` 은 없다.** `SameSite=None` 에 `Secure` 가 없으면 **저장되지 않았다**(예외도 경고도 페이지에 없다).
- ★★ **`Secure` 쿠키(`none=1`)가 `http` 에서 저장됐다** — `127.0.0.1` 과 `localhost` **둘 다.** Chrome 이 이 두 주소를 **안전한 곳으로 친다**는 관찰이다(쿠키 명세를 이 판에서 열지 않았다 — 구현 관찰로만 적는다). 그래서 이 편의 격자가 http 에서 성립한다.
- ★ **같은 서버 B 인데 두 이름은 쿠키 통이 따로**다 — 각각 따로 받았고, 아래 격자에서 실리는 것도 다르다.

### (2) ★★★ 본체 — 쿠키 실림 격자: 서버는 받았는데 페이지는 못 읽은 칸

**언제 쓰나** — 「로그인한 사용자의 정보를 다른 출처 API 에서 가져오려는데 쿠키가 안 간다 / 갔는데 못 읽는다」일 때.

**던진 것** — 받는 쪽 2 × `credentials` 3 × B 의 응답 헤더 4 = **24칸 GET.** 칸마다 ① **B 가 받은 `Cookie`**(B 에게 묻는다) ② **페이지가 `res.json()` 을 읽었나.** GET·헤더 없음이라 **프리플라이트는 안 붙는다**(28편 격자의 단순 요청 칸).

```html
<!-- wa28b-29-grid.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>29 grid</title>
<script>
// 받는 쪽 2(같은 사이트의 다른 출처 · 사이트 밖) × credentials 3 × B 의 응답 헤더 4 — GET 한 번씩
// 칸마다 ① B 가 받은 쿠키(B 에게 묻는다) ② 페이지가 응답 본문을 읽었나
const 곳 = [["같은 사이트", "B"], ["사이트 밖", "B사이트밖"]];
const 자격 = ["omit", "same-origin", "include"];
const 답 = [["허용 없음", "acao=none"], ["ACAO: *", "acao=star"], ["ACAO: 출처", "acao=origin"],
           ["ACAO: 출처 + ACAC", "acao=origin&acac=1"]];
const 너비 = t => [...t].reduce((n, ch) => n + (ch.codePointAt(0) > 0x1100 ? 2 : 1), 0);
const 한줄 = (칸들, 폭) => {
  if (칸들.length !== 폭.length) throw new Error("칸 수가 어긋났다");
  return 칸들.map((c, k) => k === 칸들.length - 1 ? c : c + " ".repeat(Math.max(폭[k] - 너비(c), 1))).join("");
};
window.__끝 = async () => {
  const 폭 = [12, 13, 19, 26, 0];
  const O = [한줄(["받는 쪽", "credentials", "B 의 응답", "B 가 받은 쿠키", "페이지"], 폭)];
  let n = 0, 실림 = 0, 읽음 = 0, 갈림 = 0;
  for (const [곳이름, 키] of 곳) for (const c of 자격) for (const [답이름, q] of 답) {
    const id = "k" + n++;
    let 페이지, 읽었나 = false;
    try {
      const res = await fetch(window["__" + 키] + "/c29?id=" + id + "&" + q, { credentials: c });
      페이지 = "읽음 " + (await res.json()).cookie; 읽었나 = true;
    } catch (e) { 페이지 = "catch " + e.name; }
    const 받음 = await (await fetch("/note?id=" + id)).json();
    const 실렸나 = 받음 !== "(쿠키 없음)" && 받음 !== "(요청 안 옴)";
    실림 += 실렸나; 읽음 += 읽었나; 갈림 += 실렸나 && !읽었나;
    O.push(한줄([곳이름, c, 답이름, 받음, 페이지], 폭));
  }
  O.push("쿠키가 서버에 간 칸 = " + 실림 + " / " + n + " · 페이지가 읽은 칸 = " + 읽음 + " / " + n +
         " · 서버는 쿠키를 받았는데 페이지는 못 읽은 칸 = " + 갈림 + " / " + n);
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '3,28p'
받는 쪽     credentials  B 의 응답          B 가 받은 쿠키            페이지
같은 사이트 omit         허용 없음          (쿠키 없음)               catch TypeError
같은 사이트 omit         ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 omit         ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 omit         ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 same-origin  허용 없음          (쿠키 없음)               catch TypeError
같은 사이트 same-origin  ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 same-origin  ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 same-origin  ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
같은 사이트 include      허용 없음          lax=1 none=1 plain=1      catch TypeError
같은 사이트 include      ACAO: *            lax=1 none=1 plain=1      catch TypeError
같은 사이트 include      ACAO: 출처         lax=1 none=1 plain=1      catch TypeError
같은 사이트 include      ACAO: 출처 + ACAC  lax=1 none=1 plain=1      읽음 lax=1 none=1 plain=1
사이트 밖   omit         허용 없음          (쿠키 없음)               catch TypeError
사이트 밖   omit         ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   omit         ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   omit         ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   same-origin  허용 없음          (쿠키 없음)               catch TypeError
사이트 밖   same-origin  ACAO: *            (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   same-origin  ACAO: 출처         (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   same-origin  ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
사이트 밖   include      허용 없음          none=1                    catch TypeError
사이트 밖   include      ACAO: *            none=1                    catch TypeError
사이트 밖   include      ACAO: 출처         none=1                    catch TypeError
사이트 밖   include      ACAO: 출처 + ACAC  none=1                    읽음 none=1
쿠키가 서버에 간 칸 = 8 / 24 · 페이지가 읽은 칸 = 14 / 24 · 서버는 쿠키를 받았는데 페이지는 못 읽은 칸 = 6 / 24
(exit 0)
```

- ★★★ **쿠키가 서버에 간 칸 8 / 24 — 전부 `include`.** `omit` 은 당연히, **기본값 `same-origin` 도 다른 출처에는 한 개도 안 실었다.** 명세의 includeCredentials — **`same-origin` 은 response tainting 이 `basic`(같은 출처)일 때만** 참이다.
- ★★★ **서버는 쿠키를 받았는데 페이지는 못 읽은 칸 6 / 24** — `include` × (허용 없음 · **`ACAO: *`** · `ACAO: 출처`만) × 받는 쪽 2. **읽힌 `include` 칸은 「`ACAO: 출처` + `ACAC`」 둘뿐**이다.
- ★★ **`include` + `ACAO: *` 는 25편과 같은 모양이다** — 요청은 **쿠키를 싣고 서버에 닿았고**(서버 로그 (4)), 페이지는 `catch TypeError`. 25편은 「허용 헤더 없음」이었고 여기는 「**허용 헤더가 있는데 `*` 라서**」다.
- ★ **`omit`·`same-origin` 에서는 `*` 도 잘 읽힌다** — `*` 가 막히는 것은 **`include` 일 때만**이다(명세의 CORS check 첫 문장).
- ★★ **같은 사이트와 사이트 밖에서 실린 쿠키가 다르다** — `127.0.0.1:<B>` 에는 **`lax=1 none=1 plain=1` 셋**, `localhost:<B>` 에는 **`none=1` 하나.** 포트만 다른 두 출처는 **같은 사이트**라 `Lax` 도 실렸고, 호스트가 다르면 **사이트 밖**이라 `SameSite=None; Secure` 만 실렸다. **`SameSite` 를 안 적은 `plain` 은 `Lax` 처럼** 굴었다(이 판의 관찰).
- 페이지가 읽은 칸 14 / 24 — 쿠키 없이 읽은 12칸 + 쿠키째 읽은 2칸.

```text
   include 여덟 칸 — 서버와 페이지 (이 판)

                    B 의 응답              서버가 받은 쿠키          페이지
   같은 사이트      허용 없음             lax none plain            catch   ★ 받았는데 못 읽음
                    ACAO: *               lax none plain            catch   ★
                    ACAO: 출처            lax none plain            catch   ★
                    ACAO: 출처 + ACAC     lax none plain            읽음
   사이트 밖        (위와 같은 넷)        none 만                   catch ×3 · 읽음 ×1

   ★ 문 ①(실리나)은 여덟 칸 모두 열렸다 — 응답 헤더는 실리는 것을 못 바꾼다
```

### (3) ★★ 콘솔 — 거부 이유는 세 문구로 갈린다

**페이지의 `catch` 는 10칸 모두 `TypeError`** 다. 이유는 콘솔에만 있다.

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '/^--- 콘솔/,/^--- 서버/{/^--- 서버/!p}'
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k0&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k4&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k8&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k9&acao=star' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=k10&acao=origin' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k12&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k16&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k20&acao=none' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k21&acao=star' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Origin' header in the response must not be the wildcard '*' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
javascript · error · Access to fetch at 'http://localhost:<B>/c29?id=k22&acao=origin' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
(exit 0)
```

- ★★ **세 문구** — ① 「No 'Access-Control-Allow-Origin' header is present …」(허용 없음 — `credentials` 무관) ② 「The value of the 'Access-Control-Allow-Origin' header in the response **must not be the wildcard '*' when the request's credentials mode is 'include'**.」 ③ 「The value of the 'Access-Control-Allow-Credentials' header in the response is **''** which must be **'true'** when the request's credentials mode is 'include'.」
- ★ 문구는 **Chrome 의 글자**다(가이드 규칙 27 — 진단 문구는 틀릴 수 있다). 이 판에서는 **세 문구가 칸의 원인과 맞았다** — 격자의 칸(응답 헤더)을 근거로 쓰고, 문구는 그것을 확인하는 데만 쓴다.

```text
   catch 열 칸의 이유 — 칸이 원인이고 문구는 확인용 (이 판)

   허용 없음 (omit·same-origin·include × 2곳)   → 문구 ①  6칸
   include + ACAO: *            (× 2곳)          → 문구 ②  2칸
   include + ACAO: 출처, ACAC 없음 (× 2곳)       → 문구 ③  2칸
```

### (4) ★★ 서버 로그 — 못 읽은 칸에서도 쿠키는 갔다

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html | sed -n '/^--- 서버/,$p'
--- 서버 로그 ---
B GET /c29?id=k0&acao=none  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k1&acao=star  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k2&acao=origin  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k3&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k4&acao=none  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k5&acao=star  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k6&acao=origin  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k7&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k8&acao=none  Origin=http://127.0.0.1:<A> · Cookie=lax=1 none=1 plain=1
B GET /c29?id=k9&acao=star  Origin=http://127.0.0.1:<A> · Cookie=lax=1 none=1 plain=1
B GET /c29?id=k10&acao=origin  Origin=http://127.0.0.1:<A> · Cookie=lax=1 none=1 plain=1
B GET /c29?id=k11&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=lax=1 none=1 plain=1
B GET /c29?id=k12&acao=none  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k13&acao=star  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k14&acao=origin  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k15&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k16&acao=none  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k17&acao=star  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k18&acao=origin  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k19&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=(쿠키 없음)
B GET /c29?id=k20&acao=none  Origin=http://127.0.0.1:<A> · Cookie=none=1
B GET /c29?id=k21&acao=star  Origin=http://127.0.0.1:<A> · Cookie=none=1
B GET /c29?id=k22&acao=origin  Origin=http://127.0.0.1:<A> · Cookie=none=1
B GET /c29?id=k23&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=none=1
(exit 0)
```

- ★★★ **`k9`(같은 사이트 · `include` · `ACAO: *`) 줄에 `Cookie=lax=1 none=1 plain=1`** — 페이지는 `catch` 였는데 **서버는 쿠키째 요청을 받았다.** 이 서버는 읽기 전용이지만, **쿠키로 사람을 알아보고 무언가를 바꾸는 엔드포인트였다면 그 일은 일어났다.**
- `Origin` 은 24줄 모두 `http://127.0.0.1:<A>` 다 — **서버가 「누가 보냈나」를 알 수 있는 자리**는 이것이다((7)).

### (5) ★★ 서드파티 쿠키를 막으면 — 바뀌는 칸

**같은 쿠키 통으로 같은 격자를 두 탭에서** 돌린다 — 그대로 한 번, 그 탭에 **CDP `Network.setCookieControls({ enableThirdPartyCookieRestriction: true, … })`** 를 켜고 한 번. 스크립트가 **갈린 줄만** 찍는다.

```text
$ python3 wa28b-net.py cookie wa28b-29-grid.html compare
그대로 사이트 밖   include      허용 없음          none=1                    catch TypeError
막음   사이트 밖   include      허용 없음          (쿠키 없음)               catch TypeError
그대로 사이트 밖   include      ACAO: *            none=1                    catch TypeError
막음   사이트 밖   include      ACAO: *            (쿠키 없음)               catch TypeError
그대로 사이트 밖   include      ACAO: 출처         none=1                    catch TypeError
막음   사이트 밖   include      ACAO: 출처         (쿠키 없음)               catch TypeError
그대로 사이트 밖   include      ACAO: 출처 + ACAC  none=1                    읽음 none=1
막음   사이트 밖   include      ACAO: 출처 + ACAC  (쿠키 없음)               읽음 (쿠키 없음)
서드파티 쿠키를 막자 바뀐 칸 = 4 / 24
(exit 0)
```

- ★★ **바뀐 칸 4 / 24 — 전부 「사이트 밖 · `include`」.** 막으면 `none=1` 도 안 실린다. **같은 사이트 칸은 하나도 안 바뀌었다** — 포트만 다른 출처는 서드파티가 아니다.
- ★★ **거꾸로 읽으면 — 이 판의 기본 프로필은 서드파티 쿠키를 막지 않았다.** 이 네 칸이 **판·설정에 매인 칸**이다(머리말 표).
- ★ **「출처 + ACAC」 칸은 막아도 `읽음`** — 쿠키가 없을 뿐 응답은 읽힌다. **CORS 가 통과해도 쿠키가 안 실릴 수 있다** — 두 문이 따로라는 (2)의 그림 그대로다.

```text
   같은 칸, 두 판 — 사이트 밖 · include · ACAO: 출처 + ACAC

   그대로   서버가 받은 쿠키 none=1        페이지 읽음 none=1
   막음     서버가 받은 쿠키 (쿠키 없음)   페이지 읽음 (쿠키 없음)     ← CORS 는 통과, 쿠키만 빠짐
```

### (6) ★ 프리플라이트가 붙는 `include` — OPTIONS 에는 쿠키가 없다

**`include` + 커스텀 헤더 `X-A`** — 프리플라이트가 붙는다(28편).

```html
<!-- wa28b-29-preflight.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>29 preflight</title>
<script>
// credentials: 'include' + 커스텀 헤더 X-A — 프리플라이트가 붙는다. OPTIONS 에는 쿠키가 실리나 · 답에 ACAC 가 없으면
const 칸 = [
  ["가. 두 답 모두 ACAO: 출처 + ACAC: true", "/c29?id=p1&acao=origin&acac=1"],
  ["나. 두 답 모두 ACAO: 출처 (ACAC 없음)", "/c29?id=p2&acao=origin"],
];
window.__끝 = async () => {
  const O = [];
  for (const [이름, 길] of 칸) {
    let 페이지;
    try { 페이지 = "읽음 " + (await (await fetch(window.__B + 길, { credentials: "include", headers: { "X-A": "1" } })).json()).cookie; }
    catch (e) { 페이지 = "catch " + e.name; }
    O.push(이름 + " → " + 페이지);
  }
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py cookie wa28b-29-preflight.html
B 를 127.0.0.1 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
B 를 localhost 로 직접 열었다 → 그 자리의 쿠키 통 = ["lax=1", "none=1", "plain=1"]
가. 두 답 모두 ACAO: 출처 + ACAC: true → 읽음 lax=1 none=1 plain=1
나. 두 답 모두 ACAO: 출처 (ACAC 없음) → catch TypeError
--- 콘솔 ---
javascript · error · Access to fetch at 'http://127.0.0.1:<B>/c29?id=p2&acao=origin' from origin 'http://127.0.0.1:<A>' has been blocked by CORS policy: Response to preflight request doesn't pass access control check: The value of the 'Access-Control-Allow-Credentials' header in the response is '' which must be 'true' when the request's credentials mode is 'include'.
network · error · Failed to load resource: net::ERR_FAILED
--- 서버 로그 ---
B OPTIONS /c29?id=p1&acao=origin&acac=1  Cookie=(쿠키 없음)
B GET /c29?id=p1&acao=origin&acac=1  Origin=http://127.0.0.1:<A> · Cookie=lax=1 none=1 plain=1
B OPTIONS /c29?id=p2&acao=origin  Cookie=(쿠키 없음)
(exit 0)
```

- ★★ **두 칸 모두 OPTIONS 의 `Cookie=(쿠키 없음)`** — 명세의 「**CORS-preflight request never includes credentials**」 그대로다. 서버는 프리플라이트 단계에서 **누가 보냈는지 쿠키로 알 수 없다.**
- ★★ **나(ACAC 없음)는 GET 이 서버에 안 왔다** — 프리플라이트 답에도 `Access-Control-Allow-Credentials: true` 가 있어야 한다. 콘솔 「Response to preflight request doesn't pass access control check: The value of the 'Access-Control-Allow-Credentials' header … must be 'true' …」. **(2)의 단순 요청 칸과 달리 쿠키가 서버에 가지도 않았다** — 28편 (4)의 「거부되면 본 요청은 안 간다」가 쿠키에도 그대로다.

```text
   include + X-A — 서버 B 가 받은 줄 (이 판)

   가. ACAC 있음   OPTIONS (쿠키 없음) ─▶ GET (lax none plain) ─▶ 페이지 읽음
   나. ACAC 없음   OPTIONS (쿠키 없음) ─✕                        페이지 catch   ← 쿠키째 안 갔다
```

### (7) 그래서 — 「읽기를 막는 것」과 「요청을 막는 것」은 다르다

**(2)·(4)가 보인 것** — 단순 요청(프리플라이트가 안 붙는 GET·POST)에 `include` 를 달면 **서버는 쿠키째 받는다.** 응답 헤더를 어떻게 주든 **실리는 것은 못 바꾼다**. 서버가 쓸 수 있는 자리는 **요청에 이미 있는 것** — `Origin` 헤더((4)) · 쿠키의 `SameSite`((2) — 사이트 밖에는 `Lax` 가 안 실렸다) · 프리플라이트를 강제하는 설계(28편 (4)).

```text
   쿠키가 실린 다른 출처 요청 — 브라우저가 해 주는 것과 안 해 주는 것 (이 판)

   브라우저가 해 줌   응답을 페이지에게 안 보여 준다 (ACAO·ACAC 가 안 맞으면)
                      SameSite=Lax 쿠키를 사이트 밖에 안 싣는다
                      프리플라이트가 거부되면 본 요청을 안 보낸다
   안 해 줌           단순 요청은 쿠키째 서버에 보낸다 — 서버의 처리를 막지 않는다
                      ★ 여기서부터가 CSRF 방어 설계다 → ../../security/ (절은 아직 없다)
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   페이지 쪽
     fetch(url, { credentials: "omit" | "same-origin"(기본) | "include" })
       omit         어디에도 안 싣는다
       same-origin  같은 출처에만 싣는다 — 다른 출처에는 안 싣는다
       include      다른 출처에도 싣는다 (쿠키의 SameSite·정책이 허락하는 것만)

   서버 쪽 — include 요청의 응답을 페이지가 읽으려면 둘 다
     Access-Control-Allow-Origin: http://정확한-출처      ← * 금지
     Access-Control-Allow-Credentials: true              ← 프리플라이트 답에도

   쿠키 쪽 (이 판의 관찰)
     SameSite=Lax (또는 안 적음)   같은 사이트에만
     SameSite=None; Secure         사이트 밖에도 — Secure 가 없으면 저장이 안 됐다
```

### 어디서 헷갈리나

- **`same-origin` 이 기본값이다** — 다른 출처 요청에는 **아무것도 안 실린다**((2)).
- **「다른 출처」와 「사이트 밖」은 다르다** — 포트만 다르면 같은 사이트라 `Lax` 도 실렸다((2)).
- **응답 헤더는 「읽기」만 바꾼다** — 「실리나」는 못 바꾼다((2)·(4)).

## 어디서 틀리나

### 1. `credentials: "include"` 만 달면 쿠키 달린 응답을 읽을 수 있다고 믿는다

**서버가 정확한 출처 + `Access-Control-Allow-Credentials: true`** 를 줘야 한다((2) — 읽힌 `include` 칸은 둘뿐).

### 2. 서버에 `Access-Control-Allow-Origin: *` 를 주면 누구나 된다고 믿는다

**`include` 에는 거부**다((2)·(3)). 그리고 그 칸에서도 **쿠키는 이미 서버에 갔다**((4)).

### 3. 「CORS 로 막혔으니 로그인 쿠키가 달린 요청은 처리 안 됐다」

**단순 요청이면 처리됐다**((4)). 되돌릴 수 없는 일을 쿠키만으로 인증하는 엔드포인트는 그 자체가 문제다((7)).

### 4. 기본값으로 다른 출처에 쿠키가 간다고 믿는다

**기본 `same-origin` 은 다른 출처에 안 싣는다**((2)).

### 5. `SameSite=None` 만 적는다

**`Secure` 가 없으면 저장조차 안 됐다**((1)) — 예외도 경고도 페이지에 없다.

### 6. 로컬에서 쿠키가 실렸으니 배포해도 실린다고 믿는다

**「사이트 밖」 칸은 서드파티 쿠키 정책에 매인다**((5)) — 이 판의 기본값에서 실렸어도 설정 하나로 네 칸이 바뀌었다. 게다가 로컬의 `127.0.0.1:포트` 끼리는 **같은 사이트**라 배포 환경의 교차 사이트를 흉내 내지 못한다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `credentials` 기본값 `same-origin` · `same-origin` 은 같은 출처에만 싣는다 | **명세**(Fetch — credentials mode · includeCredentials) · 이 판도 그랬다((2)) |
| `include` + `ACAO: *` → CORS check 실패 · `include` 면 `ACAC: true` 필요 | **명세**(Fetch — CORS check) · 이 판도 그랬다((2)·(3)) |
| ★ 읽기가 막힌 `include` 칸에서도 **쿠키가 서버에 갔다** | **명세의 순서**(CORS check 는 응답에 대해) · ★ **서버 로그가 증명**((4)) |
| 프리플라이트에는 쿠키가 없다 | **명세**(「never includes credentials」) · 이 판도 그랬다((6)) |
| `SameSite=Lax`·안 적음은 사이트 밖에 안 실림 · `None` 은 `Secure` 가 있어야 저장 | ★ **이 판의 관찰** — 쿠키 명세(RFC 6265bis 초안)는 열지 않았다 |
| `http` 의 `127.0.0.1`·`localhost` 에서 `Secure` 쿠키가 저장·전송됨 | ★ **Chrome 의 성질** — 이 판의 관찰 |
| 기본 프로필에서 서드파티 쿠키가 실림 | ★ **브라우저 설정·정책** — 판이 오르면 다시 찍는다((5)) |
| 콘솔 문구 세 가지 | ★ **Chrome 의 글자** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 같은 출처 API | 기본값(`same-origin`) | `include`(필요 없다) |
| 다른 출처 API 에 로그인 쿠키로 | `include` + 서버의 정확한 `Allow-Origin` + `Allow-Credentials: true` | `Allow-Origin: *` |
| 공개 데이터(쿠키 불필요) | `omit` + `Allow-Origin: *` | `include` |
| 사이트 밖에서도 실려야 하는 쿠키 | `SameSite=None; Secure` (정책에 막힐 수 있음을 전제) | `SameSite=None` 만 |
| 쿠키로 사람을 알아보고 상태를 바꾸는 엔드포인트 | 서버의 `Origin` 검사·토큰(→ `../../security/`) | 「CORS 가 막아 주겠지」 |

## 핵심 문장

1. **쿠키가 다른 출처로 실리는 것은 페이지(`include`)와 쿠키 속성·정책이 정하고, 응답을 읽는 것은 서버의 응답 헤더가 정한다** — 두 문이 따로다.
2. **기본값 `same-origin` 은 다른 출처에 아무것도 안 싣는다** — 쿠키가 서버에 간 칸 8 / 24 는 전부 `include`.
3. **`include` 에는 `*` 가 안 된다** — 정확한 출처 + `Allow-Credentials: true`. 그런데 그 칸에서도 **쿠키는 이미 서버에 갔다**(서버는 받았는데 페이지는 못 읽은 칸 6 / 24).
4. **포트만 다른 출처는 같은 사이트다** — `Lax` 도 실렸다. 사이트 밖에는 `SameSite=None; Secure` 만, 그것도 서드파티 쿠키 정책에 매인다(막으면 4칸이 바뀌었다).
5. **프리플라이트에는 쿠키가 없고, 거부되면 쿠키째 안 간다.**

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 29번)
- [28번 주제](../28-cors-simple-and-preflight/2-summary.md) — **CORS 의 정본**(프리플라이트 조건 · 거부되면 본 요청이 안 간다 · 하네스 (1)). 여기는 **쿠키가 붙었을 때**만
- [25번 주제](../25-fetch-request-response/2-summary.md) — `Cookie` 를 헤더로 넣으면 지워지고 쿠키 통의 값이 간다((5)). 그쪽은 **같은 출처의 금지 헤더**, 여기는 **다른 출처의 `credentials`**
- [`../../security/`](../../security/) — **CSRF 방어 설계의 정본 자리**(2026-09-26 현재 절이 없다). 여기는 **「쿠키가 실린 요청이 처리됐다」까지의 관찰**
- [30번 주제](../30-request-body-and-content-type/2-summary.md) — 본문이 정하는 `Content-Type` — 폼·`text/plain` 본문은 **단순 요청**이라 (7)의 「쿠키째 서버에」 칸이 된다

## 용어 풀이

- **자격 증명(credentials)** — Fetch 에서 쿠키·HTTP 인증·TLS 클라이언트 인증서. 이 편은 쿠키만 봤다.
- **`credentials` 옵션** — `omit` · `same-origin`(기본) · `include`. 쿠키를 싣고 받을지.
- **`Access-Control-Allow-Credentials`** — `true` 여야 `include` 요청의 응답을 페이지가 읽는다.
- **같은 사이트(same-site)** — 이 판에서 포트만 다른 두 출처는 같은 사이트로 다뤄졌다(`Lax` 가 실렸다). 호스트 이름이 다르면 사이트 밖.
- **`SameSite`** — 쿠키가 사이트 밖 요청에 실릴지. `Lax`·`Strict`·`None`.
- **서드파티 쿠키** — 사이트 밖 요청에 실리는 쿠키. 브라우저 정책으로 막힐 수 있다.
- **쿠키 실림 격자** — 받는 쪽 2 × `credentials` 3 × 응답 헤더 4 = 24칸 × (서버가 받은 쿠키 · 페이지가 읽었나). 이 편의 본체.

## 더 들어가면

- **`Partitioned`(CHIPS) 쿠키** · **`Strict`** · **HttpOnly** 는 던지지 않았다.
- **응답의 `Set-Cookie` 가 다른 출처 `include` 요청에서 저장되나**는 재지 않았다(이 편은 「실리나」만 봤다).
- **https 와 진짜 등록 도메인**은 이 판으로 못 본다(머리말 「도구가 못 보는 것」).
