# web-api/31 — `Blob`·`File`·`FileReader` 와 오브젝트 URL: 미리보기·업로드·저장 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.\
> ★★★ **이 편의 본체는 창 ③ 「같은 것을 두 번 읽기」 — 풀지 않은 오브젝트 URL 하나를 「누가 · 언제」 읽나로 바꿔 가며 `fetch` 하는 「URL 수명 표」다.** 풀기 전 · 푼 뒤 · 같은 출처의 다른 탭 · 다른 출처의 탭 · **만든 문서가 떠난 뒤 · 닫힌 뒤** · unload 리스너를 단 문서가 떠난 뒤. 그 옆에 **넘기는 길 셋**(미리보기 · 업로드 · 저장)을 서버 로그와 내려받은 파일로 싣는다.\
> **기준 소스** — [W3C File API](https://w3c.github.io/FileAPI/) 의 `interface File : Blob` · `slice()`(「**새 `Blob`** 을 돌려준다」) · FileReader 의 read operation(「state 를 `loading` 으로 · **`loadstart` 를 태스크로** 큐에 · 대략 50ms 마다 `progress` · 끝나면 `load` → `loadend`」 · `LOADING = 1`) · blob URL store(「user agent 마다 **하나**」 · 항목 = 객체 + **만든 환경**) · 「**Lifetime of blob URLs** — unloading document cleanup steps 에서 **그 문서의 환경이 만든 항목을 지운다**」 · `revokeObjectURL`(「blob 이 아니거나 항목이 없거나 **다른 저장소 분할이면 조용히 끝난다**」 · 「풀린 뒤의 역참조는 **network error**」 · 「**풀기 전에 시작한 요청은 성공해야 한다**」) · 접근 제한(「**storage key 가 같은 환경에서만** fetch 할 수 있다」) · [WHATWG Fetch](https://fetch.spec.whatwg.org/) 의 scheme fetch `blob`(「메서드가 `GET` 이 아니거나 **blob URL entry 가 null 이면 network error**」). 열어서 확인한 것만 적었다(기준일 2026-09-26).\
> **실행 검증** — 모든 출력은 **Google Chrome 151.0.7922.173** headless 에서 받은 것이다. 파일은 **73바이트 PNG(3×2 빨강)** 하나를 CDP `DOM.setFileInputFiles` 로 파일 입력에 넣었고, 저장은 CDP `Browser.setDownloadBehavior` 로 받은 폴더에 **실제로 떨어진 파일**을 원본과 바이트째 견줬다. 하네스는 [28번 주제](../28-cors-simple-and-preflight/2-summary.md)의 (1)이다.\
> **엔진은 Chrome 하나다** — **이식성을 주장하지 않는다.**\
> **선행** — ★★ **[30번 주제](../30-request-body-and-content-type/2-summary.md)** — `FormData` 의 파일 칸(`filename`·`Content-Type`)과 폼 제출의 본문. 여기서는 **파일 입력의 `File`** 을 그대로 넘긴다. ★ **HTML 갈래 31번**(파일 업로드 — `accept`/`multiple`/`capture`)은 폴더가 아직 없다 — 마크업 쪽 파일 입력은 그쪽 몫이다. ★ **[24번 주제](../24-document-lifecycle-events/2-summary.md)의 (4)** — **`unload` 리스너 하나가 문서를 bfcache 에서 뺀다.** (5)에서 그것을 재지 않고 **스위치로** 쓴다.\
> **경계** — ★ **메모리는 재지 않았다.** 「`revokeObjectURL` 을 안 하면 메모리가 샌다」는 이 편이 **주장하지 않는다** — 관찰한 것은 **「그 URL 이 아직 읽힌다」** 까지다. 힙·가비지 컬렉션의 원리는 [`../../memory-management/`](../../memory-management/README.md) 의 몫이다.\
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
| **안 흔들린다** | `File` 들여다보기 · 미리보기 둘 · 이벤트 순서 · 올리기 둘(서버 로그) · 풀기 전·뒤 · 수명 표 일곱 줄 · 내려받기 | 캡처 세 판이 **한 글자도 같았다** |
| ★ **흔들리게 만들지 않았다** | 오브젝트 URL 의 **UUID 36자** | 판마다 새로 만든다 — 그래서 URL 을 찍지 않고 **「출처 + `/` 로 시작하나」와 「뒤 글자 수」** 만 찍었다 |
| ★ **판에 매일 수 있는 칸** | 「첫 탭이 떠난 뒤」의 **`then`** | 문서가 **bfcache 에 들어갔기 때문**이다((5)) — bfcache 에 들어가느냐는 구현·조건에 매인다(24편) |
| **흔들린다** | Chrome 판 번호 · 포트 | 포트는 출력에 안 나온다 |

- 재대조에서 정규화하는 칸은 없다. **위 표에 없는 차이는 전부 고칠 것**이다.

### 이 주제가 쓰는 창 / 부적용인 창

| 창 | 이 주제에서 | 무엇을 답하나 |
|---|---|---|
| 창 ① `--dump-dom` 트리 | **부적용** | — |
| 창 ② 노드 프로브 | ★ **쓴다** | `instanceof` · `name`·`size`·`type` · `img.naturalWidth` · `FileReader.readyState` |
| **창 ③ 같은 것을 두 번 읽기 — 같은 URL 을 여러 자리에서** | ★★★ **본체** | 풀기 전·뒤 · 다른 탭 · 다른 출처 · 문서가 떠난 뒤 · 닫힌 뒤 |
| 창 ④ 서버 요청 로그 | ★★ **쓴다** | 업로드 둘의 `Content-Type`·바이트 수 · 서버가 받은 바이트가 원본과 같나 |
| ★ **내려받은 파일** | ★★ **쓴다** | 떨어진 파일의 이름·크기·원본과 같은 바이트인가 |
| ★★ **메모리** | **안 잰 것 — 부적용이 아니다** | 「남아 있다」를 **힙 크기로 묻지 않고 「URL 이 아직 읽히나」로 물었다**(제5의 상태 — 같은 질문을 다른 창으로). ★ 바꾼 창이 못 보는 것 — **URL 이 살아 있어도 그 바이트가 메모리에 있는지 디스크에 있는지** · 얼마나 차지하는지 |

### 도구가 못 보는 것

| 무엇을 | 왜 못 보나 |
|---|---|
| ★★★ **메모리 — 풀지 않은 URL 이 무엇을 얼마나 붙드나** | **재지 않았다**(가이드 규칙 4). 힙 스냅숏을 찍어도 Blob 바이트가 JS 힙 밖에 있을 수 있어 **이 판의 도구로는 말할 수 없다** |
| **`Blob.slice` 가 바이트를 복사하나** | **재지 않았다.** 관찰한 것은 **새 `Blob` 이 돌아오고 `size` 와 바이트가 맞다**는 것까지다 |
| **진짜 사용자의 파일 선택 창 · 저장 대화상자** | CDP 로 파일을 넣고, 내려받기를 「허용」으로 두었다 |
| **워커가 만든 URL** | 명세도 「워커에 비슷한 훅이 필요하다」고 적어 두었다 — 던지지 않았다 |

## 한눈에 — 쉽게 말하면

**★ 오브젝트 URL 은 「물품 보관소의 번호표」다. 파일(`Blob`)을 맡기면 번호표(`blob:…`)를 주고, 그 번호표만 있으면 같은 건물(같은 출처) 어디서든 물건을 꺼낼 수 있다. 번호표를 반납(`revokeObjectURL`)하면 그 번호로는 더 못 꺼낸다. 반납하지 않으면 — 맡긴 사람(문서)이 건물을 완전히 떠날 때까지 번호표가 살아 있다. 잠깐 자리를 비운 것(bfcache)은 떠난 것이 아니다.**

| 비유 | 실체 |
|---|---|
| 맡긴 물건 | `Blob` · `File`(`File` 은 `Blob` 의 한 종류) |
| 번호표 | `URL.createObjectURL(blob)` → `blob:<출처>/<UUID>` |
| 보관소 장부 | blob URL store — **브라우저에 하나** · 항목마다 **만든 문서** |
| 번호표 반납 | `URL.revokeObjectURL(url)` — 그 뒤로 꺼내면 `TypeError` |
| 다른 건물에서 번호표 | 다른 출처의 문서 — **못 꺼낸다** |
| 맡긴 사람이 떠남 | 만든 문서가 **파괴**될 때 장부에서 지운다 — bfcache 에 들어간 것은 파괴가 아니다 |

```text
   ★ 풀지 않은 URL 하나 — 누가 · 언제 읽나 (이 판)

   만든 문서(첫 탭, 출처 A)
     │ createObjectURL(file) ─▶ blob:http://127.0.0.1:<A>/<UUID>
     ├─ 같은 출처 A 의 다른 탭 ········· 읽힌다
     ├─ 다른 출처 B 의 탭 ·············· ✕ TypeError
     ├─ 첫 탭이 다른 문서로 떠남 ─▶ 다른 탭 ··· 읽힌다   ← bfcache — 문서가 살아 있다
     └─ 첫 탭을 닫음 ─────────▶ 다른 탭 ··· ✕ TypeError   ← 문서가 사라졌다
```

## 이 주제가 답하려는 질문

1. **파일 입력에서 받은 것을 미리보기 · 업로드 · 저장으로 각각 어떻게 넘기나** — 오브젝트 URL · `FileReader` · `FormData` · `body` · `<a download>`.
2. **`revokeObjectURL` 을 하면 무엇이 끝나고, 안 하면 무엇이 남나** — 「남는 것」을 무엇으로 관찰하나.
3. **그 URL 은 누가 · 언제까지 읽을 수 있나** — 다른 탭 · 다른 출처 · 문서가 떠난 뒤 · 닫힌 뒤.

## 동작 방식

### (1) ★★ 들여다보기 · 미리보기 둘 · 올리기 둘 · 풀기 전과 뒤 — 한 페이지

**파일 입력 하나에 73바이트 PNG 를 넣고**(CDP `DOM.setFileInputFiles`) 한 번에 돌린다. 다른 탭에서 읽을 URL(`window.__남긴URL`)은 **풀지 않고** 남기고, 저장 함수(`window.__내려받기`)도 걸어 둔다 — 하네스가 뒤에서 부른다((4)·(5)).

```html
<!-- wa28b-31-file.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>31 file</title>
<input type="file">
<script>
// 파일 입력에서 받은 것 하나를 — 들여다보고 · 미리보기 둘 · 올리기 둘 · 오브젝트 URL 을 풀기 전과 뒤
const 이름 = e => e.name + " 「" + e.message + "」";
const 그림 = src => new Promise(r => { const i = new Image(); i.onload = () => r("load · " + i.naturalWidth + "×" + i.naturalHeight);
                                        i.onerror = () => r("error 이벤트"); i.src = src; });
const 가져오기 = async url => { try { const r = await fetch(url); return "then · status " + r.status + " · " + (await r.arrayBuffer()).byteLength + "바이트"; }
                                catch (e) { return "catch · " + 이름(e); } };
window.__끝 = async () => {
  const O = [];
  const f = document.querySelector("input").files[0];
  O.push("가. File — instanceof File=" + (f instanceof File) + " · instanceof Blob=" + (f instanceof Blob) +
         " · name=" + f.name + " · size=" + f.size + " · type=" + f.type);
  const 머리 = new Uint8Array(await f.slice(0, 8).arrayBuffer());
  O.push("   f.slice(0, 8) → " + f.slice(0, 8).constructor.name + " size=" + f.slice(0, 8).size +
         " · 바이트 = " + [...머리].map(b => b.toString(16).padStart(2, "0")).join(" "));
  // 미리보기 ① 오브젝트 URL
  const url = URL.createObjectURL(f);
  O.push("나. createObjectURL → 「blob:」 + 이 문서의 출처 + 「/」 로 시작하나=" + url.startsWith("blob:" + location.origin + "/") +
         " · 그 뒤 글자 수=" + url.slice(("blob:" + location.origin + "/").length).length);
  O.push("   <img src=그 URL> → " + await 그림(url));
  // 미리보기 ② FileReader.readAsDataURL
  const 이벤트 = [];
  const 끝남 = new Promise(r => {
    const fr = new FileReader();
    for (const t of ["loadstart", "progress", "load", "loadend"]) fr.addEventListener(t, () => 이벤트.push(t));
    fr.onloadend = () => r(fr.result);
    fr.readAsDataURL(f);
    이벤트.push("(readAsDataURL 이 돌아옴 · readyState=" + fr.readyState + ")");
  });
  const 데이터 = await 끝남;
  O.push("다. readAsDataURL → " + 이벤트.join(" → ") + " · 결과 앞부분 = " + 데이터.slice(0, 22) + " · 길이 " + 데이터.length);
  O.push("   <img src=데이터 URL> → " + await 그림(데이터));
  // 올리기 ① FormData ② body 에 File 그대로
  const fd = new FormData(); fd.append("f", f);
  await fetch("/echo?id=u1", { method: "POST", body: fd });
  await fetch("/echo?id=u2&save=up.png", { method: "POST", body: f });
  O.push("라. 올리기 둘을 보냈다 — 서버 로그에서");
  // 오브젝트 URL 을 풀기 전과 뒤
  const u2 = URL.createObjectURL(f);
  O.push("마. 풀기 전 fetch(URL) → " + await 가져오기(u2));
  URL.revokeObjectURL(u2);
  O.push("   revokeObjectURL 뒤 fetch(URL) → " + await 가져오기(u2));
  O.push("   revokeObjectURL 뒤 <img src=URL> → " + await 그림(u2));
  let 두번 = "예외 없음";
  try { URL.revokeObjectURL(u2); URL.revokeObjectURL("blob:" + location.origin + "/없는-것"); URL.revokeObjectURL("아무 글자"); }
  catch (e) { 두번 = 이름(e); }
  O.push("   같은 URL 을 또 풀기 · 없는 URL 풀기 · blob 아닌 글자 풀기 → " + 두번);
  // 텍스트 Blob — FileReader(이벤트) 와 blob.text()(프라미스)
  const 글 = new Blob(["가나"]);
  const 읽음 = await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsText(글); });
  O.push("바. new Blob(['가나']) — FileReader.readAsText → " + JSON.stringify(읽음) + " · blob.text() → " + JSON.stringify(await 글.text()) +
         " · size=" + 글.size);
  window.__남긴URL = url;                         // 풀지 않은 첫 URL — 하네스가 다른 탭에서 쓴다
  window.__내려받기 = () => { const a = document.createElement("a"); a.href = url; a.download = "wa28b-31-saved.png";
                              document.body.append(a); a.click(); return "눌렀다"; };
  return O.join("\n");
};
</script>
```

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '1,12p'
가. File — instanceof File=true · instanceof Blob=true · name=wa28b-31-dot.png · size=73 · type=image/png
   f.slice(0, 8) → Blob size=8 · 바이트 = 89 50 4e 47 0d 0a 1a 0a
나. createObjectURL → 「blob:」 + 이 문서의 출처 + 「/」 로 시작하나=true · 그 뒤 글자 수=36
   <img src=그 URL> → load · 3×2
다. readAsDataURL → (readAsDataURL 이 돌아옴 · readyState=1) → loadstart → progress → load → loadend · 결과 앞부분 = data:image/png;base64, · 길이 122
   <img src=데이터 URL> → load · 3×2
라. 올리기 둘을 보냈다 — 서버 로그에서
마. 풀기 전 fetch(URL) → then · status 200 · 73바이트
   revokeObjectURL 뒤 fetch(URL) → catch · TypeError 「Failed to fetch」
   revokeObjectURL 뒤 <img src=URL> → error 이벤트
   같은 URL 을 또 풀기 · 없는 URL 풀기 · blob 아닌 글자 풀기 → 예외 없음
바. new Blob(['가나']) — FileReader.readAsText → "가나" · blob.text() → "가나" · size=6
(exit 0)
```

- **가 — `File` 은 `Blob` 이다**(`instanceof` 둘 다 `true` — 명세의 `interface File : Blob`). ★ **`f.slice(0, 8)` 은 `File` 이 아니라 `Blob`** 이고(`size=8`), 바이트는 PNG 서명 `89 50 4e 47 0d 0a 1a 0a` 다. **복사를 하는지는 재지 않았다**(머리말).
- **나 — 오브젝트 URL 은 `blob:` + 이 문서의 출처 + `/` + 36자**(UUID)다 — 명세의 「generate a new blob URL」 그대로다. `<img>` 가 그대로 **3×2** 로 읽었다.
- ★★ **다 — `FileReader` 는 이벤트형이다** — `readAsDataURL` 이 **돌아온 직후 `readyState=1`**(LOADING)이고 **그 뒤에** `loadstart → progress → load → loadend`. 명세 — `loadstart` 는 **태스크로 큐에** 넣는다. ★ 73바이트에도 **`progress` 가 한 번** 났다 — 명세 문장은 「대략 50ms 마다」라 이 칸은 **구현 관찰**이다. 결과는 **`data:image/png;base64,` 로 시작하는 122글자** — 바이트를 글자로 **바꿔 담은 사본**이다.
- **라 — 올리기 둘**은 서버 로그로 본다((2)).
- ★★★ **마 — 풀기 전 `fetch(URL)` 은 `status 200 · 73바이트`, 푼 뒤는 `TypeError 「Failed to fetch」`, `<img>` 는 `error`.** 명세 — 풀린 뒤의 역참조는 **network error**(Fetch 의 `blob` 스킴: 항목이 null 이면 network error).
- ★ **같은 URL 을 또 풀기 · 없는 URL · `blob` 이 아닌 글자를 풀어도 예외 없음** — 명세의 「조용히 끝난다」. **풀었는지 확인하는 수단이 예외가 아니다.**
- **바 — `readAsText` 와 `blob.text()` 는 같은 `"가나"`** 를 준다. `size=6` — UTF-8 바이트다.

```text
   파일 하나를 넘기는 길 (이 판)

   input.files[0]  (File — Blob 의 한 종류)
     │
     ├─ 미리보기 ① URL.createObjectURL(f) ─▶ <img src=blob:…>      바이트는 그대로 · 풀어야 끝난다
     ├─ 미리보기 ② FileReader.readAsDataURL(f) ─▶ <img src=data:…>  바이트를 글자로 바꾼 사본(122글자)
     ├─ 올리기 ①  FormData.append("f", f) ─▶ fetch body            multipart · filename · image/png
     ├─ 올리기 ②  fetch(url, { body: f })                          Content-Type = f.type
     └─ 저장      <a href=blob:… download="…"> .click()            ((4))
```

### (2) ★★ 올리기 둘 — 서버가 받은 것

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '/^--- 서버/,$p'
--- 서버 로그 ---
A POST /echo?id=u1  Content-Type=multipart/form-data; boundary=----WebKitFormBoundary<16자> · 본문 259바이트
    서버 파싱 → 칸 1개 · f[filename=wa28b-31-dot.png][image/png]=<73바이트>
A POST /echo?id=u2&save=up.png  Content-Type=image/png · 본문 73바이트
    서버 파싱 → (Content-Type 으로 고를 파서 없음)
(exit 0)
```

- ★★ **`FormData` 에 넣으면 multipart** — 파일 칸의 `filename` 은 **`File.name`**(`wa28b-31-dot.png`), `Content-Type` 은 **`File.type`**(`image/png`), 값 73바이트. 30편 (3)의 파일 칸과 같은 규칙이다.
- ★★ **`body: f` 로 그대로 넣으면 `Content-Type=image/png` · 73바이트** — 본문이 파일 바이트 **그 자체**다(아래 (4)의 마지막 줄 — 서버가 받은 바이트가 원본과 **같다**). 30편 (1)의 「`type` 있는 `Blob` 은 그 `type`」과 같은 칸이다.

### (3) ★★ 미리보기 둘의 차이 — 번호표 대 사본

```text
   같은 파일, 미리보기 두 길 (이 판의 관찰)

                        createObjectURL(f)                 readAsDataURL(f)
   돌아오는 것          blob:<출처>/<36자>                  data:image/png;base64,… (122글자)
   동기? 비동기?        즉시 돌려준다(문자열)                이벤트 — 돌아온 직후 readyState=1
   <img> 가 읽나        load · 3×2                          load · 3×2
   다른 출처로 넘기면   ✕ 다른 출처의 탭은 못 읽었다        글자라서 옮길 수 있다(던지지 않았다)
   끝내기               revokeObjectURL 해야 번호가 끊긴다  문자열이 사라지면 끝(할 일 없음)
```

- ★ **오브젝트 URL 은 「번호」이고 데이터 URL 은 「사본」이다** — 앞쪽은 풀어야 끊기고, 뒤쪽은 바이트가 글자로 늘어난다(73바이트 → 122글자). **어느 쪽이 메모리를 덜 쓰는지는 재지 않았다.**

### (4) ★★ 저장 — `<a download>` 로 떨어진 파일

**풀지 않은 URL 로** `<a href=… download="wa28b-31-saved.png">` 를 누른다. 하네스는 CDP `Browser.setDownloadBehavior({ behavior: "allow" })` 로 받은 폴더에 **실제로 떨어진 파일**을 읽는다.

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '/^내려받기/p;/^서버가/p'
내려받기 → 제안된 이름 wa28b-31-saved.png · 떨어진 파일 73바이트 · 원본과 바이트가 같나 = True
서버가 body: file 로 받아 저장한 바이트가 원본과 같나 = True
(exit 0)
```

- ★★ **제안된 이름은 `download` 속성 그대로, 떨어진 파일은 73바이트, 원본과 바이트가 같다(`True`).** 오브젝트 URL 은 **서버를 안 거치는 저장**이다(서버 로그에 없다 — (2)의 두 줄뿐).
- **둘째 줄 — 서버가 `body: file` 로 받아 저장한 바이트도 원본과 같다(`True`).** 하네스가 서버 쪽 파일과 원본을 견줬다.

```text
   같은 파일을 밖으로 — 두 길 (이 판)

   <a href=blob:… download="wa28b-31-saved.png"> .click()
        └─▶ 브라우저가 blob URL store 에서 꺼내 디스크로      서버 로그 없음 · 73바이트 · 원본과 같음
   fetch("/echo", { body: f })
        └─▶ 서버가 받아 파일로                               서버 로그 한 줄 · 73바이트 · 원본과 같음
```

### (5) ★★★ 본체 — URL 수명 표: 누가 · 언제 읽나

첫 탭이 만든 **풀지 않은 URL** 을 다른 문서가 `fetch` 한다. 하네스가 탭을 열고 · 첫 탭을 떠나게 하고 · 뒤로 가고 · 닫는다(28편 (1)의 `blob` 모드). 다른 탭의 코드는 한 줄이다.

```html
<!-- wa28b-31-other.html -->
<!DOCTYPE html>
<meta charset="utf-8"><link rel="icon" href="data:,">
<title>31 other</title>
<script>
// 다른 문서 — 받은 blob: URL 을 fetch 해 본다
window.__읽기 = async url => {
  try { const r = await fetch(url); return "then · status " + r.status + " · " + (await r.arrayBuffer()).byteLength + "바이트"; }
  catch (e) { return "catch · " + e.name + " 「" + e.message + "」"; }
};
</script>
```

```text
$ python3 wa28b-net.py blob wa28b-31-file.html wa28b-31-dot.png | sed -n '/^다른 탭(같은/,/떠난 뒤, 다른 탭(A) → catch/p'
다른 탭(같은 출처 A) → then · status 200 · 73바이트
다른 탭(다른 출처 B) → catch · TypeError 「Failed to fetch」
첫 탭이 다른 문서로 떠난 뒤, 다른 탭(A) → then · status 200 · 73바이트
첫 탭에서 뒤로 → 스크립트 상태(window.__남긴URL)가 남아 있나 = True
첫 탭을 닫은 뒤, 다른 탭(A) → catch · TypeError 「Failed to fetch」
넷째 탭(unload 리스너를 단 문서)이 만든 URL — 떠나기 전, 다른 탭(A) → then · status 200 · 1바이트
                                             떠난 뒤, 다른 탭(A) → catch · TypeError 「Failed to fetch」
(exit 0)
```

- ★★ **같은 출처 A 의 다른 탭 → 읽힌다**(`status 200 · 73바이트`). 명세 — blob URL store 는 **브라우저에 하나**다. 문서가 달라도 된다.
- ★★ **다른 출처 B 의 탭 → `TypeError`** — 명세의 접근 제한(「storage key 가 같은 환경에서만」). 번호표가 새어도 **다른 출처는 못 꺼낸다.**
- ★★★ **첫 탭이 다른 문서로 떠난 뒤에도 → 읽힌다.** 그리고 첫 탭에서 **뒤로** 가니 **스크립트 상태(`window.__남긴URL`)가 그대로** 있었다 — 떠난 문서가 **bfcache 에 들어가 파괴되지 않았다**는 증거다. 명세는 **unloading document cleanup** 에서 지우는데, bfcache 에 들어간 문서는 아직 그 단계를 안 거쳤다고 읽는다(HTML 명세의 bfcache 절은 이 판에서 열지 않았다 — 관찰로 적는다).
- ★★★ **첫 탭을 닫은 뒤 → `TypeError`.** 만든 문서가 사라지자 **풀지 않은 URL 도 끊겼다** — 「문서 수명에 묶임」 그대로다.
- ★★ **대조 — unload 리스너를 단 문서가 만든 URL 은 떠나기 전 읽히고, 떠난 뒤 `TypeError`.** 24편 (4)의 「`unload` 리스너 하나로 bfcache 에서 빠진다」를 **스위치로** 썼다 — bfcache 에 못 들어간 문서는 떠나는 순간 파괴되고 URL 도 끊긴다. **「떠났다」와 「사라졌다」가 갈리는 자리가 bfcache 다.**

```text
   URL 수명 표 — 만든 문서의 처지별 (이 판)

   만든 문서의 처지                       다른 탭(A)의 fetch(URL)
   살아 있음                              then · 73바이트
   다른 문서로 떠남 (bfcache 에 들어감)   then · 73바이트        ← 뒤로 하면 같은 문서가 되살아났다
   닫힘                                   ✕ TypeError
   다른 문서로 떠남 (unload 리스너 — bfcache 밖)   ✕ TypeError  ← 떠나는 순간 파괴
   (다른 출처 B 의 탭은 언제나)           ✕ TypeError
```

### (6) 그래서 — 「안 풀면 무엇이 남나」에 이 판이 답하는 것

**관찰한 것** — 풀지 않은 URL 은 **만든 문서가 살아 있는 동안**(bfcache 에 들어가 있는 동안까지) **같은 출처의 어느 문서에서든 읽혔다.** 명세의 blob URL entry 는 **객체를 들고 있다** — 그래서 URL 이 살아 있는 동안 그 `Blob` 은 **URL 로 닿을 수 있는 상태**로 남는다.

**관찰하지 않은 것** — 그 바이트가 **얼마나** 자리를 차지하는지 · 페이지의 다른 참조가 다 끊겼을 때 **실제로 해제되는지.** 이 편은 「메모리가 샌다」를 주장하지 않는다. 대신 **「풀지 않은 URL 은 문서가 사라질 때까지 읽힌다」** 는 것을 근거로, 오래 사는 페이지(단일 페이지 앱)에서 미리보기를 바꿀 때마다 URL 을 만들면 **읽히는 URL 이 그만큼 쌓인다**는 데까지만 간다.

```text
   미리보기를 세 번 바꾼 단일 페이지 앱 — 풀지 않으면 (이 판의 관찰로 말할 수 있는 것까지)

   createObjectURL(파일1) ─▶ URL1   ┐
   createObjectURL(파일2) ─▶ URL2   ├─ 셋 다 문서가 사라질 때까지 읽힌다
   createObjectURL(파일3) ─▶ URL3   ┘   (<img> 는 URL3 만 보는데도)
   ★ 얼마나 자리를 차지하나 — 재지 않았다
   처방: 새 URL 을 만들기 전에 앞 것을 revokeObjectURL · 또는 <img> 가 load 한 뒤 푼다
```

## 문법 — 형태와 규칙

이 갈래는 문법 표면이 단순하므로 이 절은 「**형태 — 어디서 헷갈리나**」로 읽는다.

### 형태 — 이 주제의 표면 전부

```text
   Blob       new Blob(부분들, { type })  ·  .size · .type · .slice(시작, 끝, type) → 새 Blob
              .text() · .arrayBuffer() · .bytes() · .stream()          ← 프라미스·스트림형
   File       Blob 의 하위 — .name · .lastModified 가 더 있다  ·  new File(부분들, 이름, { type })
              input.files[0] · DataTransfer · FormData.get(파일 칸)
   FileReader .readAsDataURL · .readAsText · .readAsArrayBuffer         ← 이벤트형
              readyState 0 EMPTY · 1 LOADING · 2 DONE  ·  loadstart → progress → load → loadend
   URL        URL.createObjectURL(blob) → "blob:<출처>/<UUID>"
              URL.revokeObjectURL(url)  ← 무엇을 줘도 예외 없음
   저장       a.href = objectURL; a.download = "이름"; a.click()
```

### 어디서 헷갈리나

- **`File` 은 `Blob` 이다** — `Blob` 을 받는 자리에 그대로 넣는다(`body` · `FormData` · `createObjectURL`).
- **`slice` 는 `File` 이 아니라 `Blob`** 을 준다((1)) — `name` 이 없다.
- **`FileReader` 는 이벤트, `blob.text()` 는 프라미스** — 결과는 같다((1)).
- **`revokeObjectURL` 은 무엇을 줘도 조용하다** — 실패를 예외로 알 수 없다((1)).

## 어디서 틀리나

### 1. 「`revokeObjectURL` 을 안 해도 페이지를 떠나면 풀린다」

**bfcache 에 들어가면 안 풀렸다**((5)) — 떠난 문서가 살아 있는 동안 URL 도 읽혔다. 풀린 것은 **문서가 파괴될 때**다(닫기 · bfcache 에 못 들어간 이동).

### 2. `<img>` 에 넣자마자 푼다

**`load` 뒤에 푼다.** 풀린 뒤의 역참조는 network error 다((1) — `<img>` 는 `error`). 명세는 「**풀기 전에 시작한 요청**은 성공해야 한다」고 적는다 — 기준은 **요청이 시작됐나**다.

### 3. 오브젝트 URL 을 다른 사이트에 넘기면 그쪽에서도 쓸 수 있다고 믿는다

**다른 출처는 못 읽는다**((5)). 넘겨야 하면 **바이트**(데이터 URL·업로드)를 넘긴다.

### 4. 미리보기에 `readAsDataURL` 을 쓰고 「번호표보다 가볍다」고 믿는다

**바이트를 글자로 바꾼 사본**이다(73바이트 → 122글자). 어느 쪽이 가벼운지는 **재지 않았다** — 적어도 「풀 필요가 없다」는 장점과 「사본이 생긴다」는 대가가 같이 온다((3)).

### 5. 파일을 올릴 때 `readAsArrayBuffer` 로 읽은 뒤 보낸다

**`File` 을 그대로 `body` 나 `FormData` 에** 넣는다((2)) — 서버가 받은 바이트가 원본과 같았다. 읽을 필요가 없다.

### 6. 「`revokeObjectURL` 이 예외를 안 던졌으니 풀렸다」

**없는 URL · 엉뚱한 글자에도 예외가 없다**((1)). 풀렸는지는 **읽어 봐야** 안다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `File` 은 `Blob` 의 하위 · `slice` 는 새 `Blob` | **명세**(File API) · 이 판도 그랬다((1)) |
| 오브젝트 URL 의 모양 `blob:<출처>/<UUID>` | **명세**(generate a new blob URL) · 이 판도 그랬다((1)) |
| `FileReader` — 돌아온 직후 LOADING · `loadstart` 는 태스크 · `load → loadend` | **명세**(read operation) · 이 판도 그랬다((1)) |
| 73바이트에도 `progress` 한 번 | ★ **이 판의 관찰** — 명세 문장은 「대략 50ms 마다」 |
| 풀린 뒤 역참조 → network error(`TypeError`) · 잘못된 인자에도 예외 없음 | **명세**(revokeObjectURL · Fetch `blob` 스킴) · 이 판도 그랬다((1)) |
| 같은 출처의 다른 문서가 읽는다 · 다른 출처는 못 읽는다 | **명세**(blob URL store 는 하나 · storage key 접근 제한) · 이 판도 그랬다((5)) |
| 만든 문서가 파괴되면 URL 이 끊긴다 | **명세**(Lifetime of blob URLs — unloading document cleanup) · 이 판도 그랬다((5)) |
| ★ **bfcache 에 들어간 문서의 URL 은 살아 있었다** | ★ **이 판의 관찰** — bfcache 에 들어가느냐는 구현(24편). HTML 명세의 bfcache 절은 열지 않았다 |
| `<a download>` 로 떨어진 파일 이름 · 바이트 | ★ **이 판의 관찰**(CDP 로 허용한 내려받기) |
| 메모리를 얼마나 붙드나 · `slice` 가 복사하나 | ★ **재지 않았다** |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 이미지·동영상 미리보기 | `createObjectURL` + `load` 뒤 `revokeObjectURL` | 만들고 잊기 |
| 미리보기를 문자열로 저장·전송해야 | `readAsDataURL` | 오브젝트 URL(다른 출처·다른 세션에서 못 쓴다) |
| 업로드 | `body: file` 또는 `FormData.append("f", file)` | 먼저 읽어서 보내기 |
| 스크립트가 만든 데이터를 파일로 저장 | `new Blob([...], { type })` → `createObjectURL` → `<a download>` → 뒤에 풀기 | 데이터 URL 로 긴 링크 만들기 |
| 파일 내용을 텍스트로 | `await file.text()` | `FileReader` 이벤트 배선(같은 결과) |

## 핵심 문장

1. **`File` 은 `Blob` 이다** — 미리보기(`createObjectURL`·`readAsDataURL`) · 업로드(`body`·`FormData`) · 저장(`<a download>`) 모두 그대로 넘긴다.
2. **오브젝트 URL 은 번호표다** — 풀면 그 번호로는 `TypeError`, 풀지 않으면 **만든 문서가 사라질 때까지** 같은 출처 어디서든 읽힌다.
3. **다른 출처는 못 읽는다** — 번호표가 새도 된다.
4. ★ **「떠났다」와 「사라졌다」는 다르다** — bfcache 에 들어간 문서의 URL 은 살아 있었고, 닫거나 bfcache 밖이면 끊겼다.
5. **`revokeObjectURL` 은 무엇을 줘도 조용하다** — 그리고 이 편은 메모리를 재지 않았다. 관찰은 「URL 이 아직 읽힌다」까지다.

## 관련 자료

- [`../README.md`](../README.md) — 웹 플랫폼 API 주제 목록(이 주제는 31번)
- [30번 주제](../30-request-body-and-content-type/2-summary.md) — `FormData` 의 파일 칸 규칙(`Blob` 은 이름 `"blob"` 인 `File`). 여기는 **파일 입력의 `File`** 을 넘기는 쪽
- [24번 주제](../24-document-lifecycle-events/2-summary.md) — **bfcache 의 정본**((4) — `unload` 리스너가 bfcache 에서 뺀다). 여기는 그것이 **오브젝트 URL 의 수명**을 가르는 자리
- [20번 주제](../20-listener-lifetime/2-summary.md) — 「무엇이 무엇을 붙들어 두나」를 리스너 쪽에서 본 편
- [`../../memory-management/`](../../memory-management/README.md) — 힙·가비지 컬렉션의 원리. 그쪽은 **메모리가 무엇인가**, 여기는 **URL 이 언제까지 읽히나**(메모리는 재지 않았다)
- **HTML 갈래 31번**(파일 업로드 — `accept`·`multiple`·`capture`) — 폴더는 아직 없다. 마크업 쪽 파일 입력은 그쪽 몫

## 용어 풀이

- **`Blob`** — 바이트 덩어리 + `type`. 불변이다.
- **`File`** — 이름·수정 시각이 붙은 `Blob`.
- **오브젝트 URL(blob URL)** — `blob:<출처>/<UUID>`. 브라우저의 blob URL store 에서 `Blob` 을 찾는 번호표.
- **blob URL store** — 브라우저에 하나 있는 장부. 항목마다 객체와 **만든 환경(문서)** 을 적는다.
- **`revokeObjectURL`** — 장부에서 그 번호를 지운다. 무엇을 줘도 예외가 없다.
- **데이터 URL** — `data:<타입>;base64,…`. 바이트를 글자로 바꿔 담은 사본.
- **URL 수명 표** — 풀지 않은 URL 하나를 만든 문서의 처지별로 다른 탭에서 읽은 표. 이 편의 본체.

## 더 들어가면

- **`MediaSource` 의 오브젝트 URL** · **워커가 만든 URL** 은 던지지 않았다(명세도 워커 훅을 숙제로 적었다).
- **최상위 문서로 `blob:` URL 을 여는 것**(새 탭에서 바로 보기)은 접근 제한의 예외다(명세) — 던지지 않았다.
- **메모리** — 힙 스냅숏·프로세스 메모리로 「남는 것」을 재는 일은 이 판의 몫이 아니다(머리말).
