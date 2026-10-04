# web-platform/06-browser-storage — 정답

## 정답

### 1. 네 축과 배치

- 축: **누가 읽나**(서버·스크립트·HttpOnly 여부), **동기인가**, **얼마나 담나**(쿼터), **언제 지워지나**(만료·축출·ITP).
- 세션 식별자 → `HttpOnly; Secure; SameSite` 쿠키(또는 BFF 서버 세션).
- 테마 설정 → localStorage(작고 동기 읽기가 편함).
- 오프라인 초안 → IndexedDB(비동기·대용량·트랜잭션). 서버에 자주 동기화.

### 2. HttpOnly vs localStorage

```text
(실험, headless Chrome 151)
document.cookie="theme=dark" | localStorage.access_token=eyJ...demo
브라우저 쿠키 저장소(CDP): sid httpOnly=true sameSite=Lax, theme httpOnly=false sameSite=Lax
```

- `document.cookie`는 `theme=dark`만. `sid`는 HttpOnly라 안 보인다.
- localStorage 토큰은 그대로 읽힌다.
- 교훈: 페이지에서 도는 스크립트(XSS·변조된 서드 파티 스크립트 포함)는 localStorage를 다 읽는다. 장기 자격 증명은 HttpOnly 쿠키나 서버 세션에 둔다.

### 3. localStorage 쿼터

```text
QuotaExceededError (code 22) at key k4: stored 4 MiB chars + 1020 KiB chars
같은 문자 수를 한글로: QuotaExceededError at k4 (4 MiB chars stored)
```

- 다섯 번째(`k4`)에서 `QuotaExceededError`(code 22). 남은 공간을 1Ki 문자씩 채우면 1020개 더 들어갔다. 합계 약 5Mi 문자.
- 한글도 같은 지점에서 막혔다. UTF-8 바이트(한글 3바이트)로 셌다면 더 일찍 막혔어야 한다.
- 문자 단위(UTF-16 2바이트)로 세고 한도는 10 MiB 바이트다. Chromium 소스로 확인된다: `kPerStorageAreaQuota` = 10485760(`storage_area.mojom`), 사용량 = (키 길이 + 값 길이) × `sizeof(UChar)`(`storage_area_map.cc`).

### 4. 동기 쓰기 비용

- 60Hz 한 프레임은 약 16.7ms다. 42~54ms는 2~3프레임 이상 메인 스레드를 막는다. 그 동안 입력 처리·렌더링이 멈춘다.
- IndexedDB는 비동기 API라 호출이 즉시 돌아오고 결과는 이벤트로 온다. Chromium에서는 실제 저장을 렌더러 밖(브라우저 쪽 저장소 서비스)에서 한다. 값의 구조적 복제 비용은 메인 스레드에 남는다.

### 5. 키 순서와 롤백

```text
키 정렬=[2,10,"Date(0)","a","b",[1]] | 충돌 트랜잭션=abort ConstraintError, new1 남았나=없음(롤백)
```

- 숫자 → Date → 문자열 → 배열(W3C IndexedDB 키 비교: Number < Date < String < Binary < Array).
- 두 번째 `add`가 `ConstraintError`로 실패했고, `error` 핸들러에서 `preventDefault()`를 안 했으므로 트랜잭션이 abort됐다(§5.10). 앞선 `new1`도 롤백돼 남지 않는다.

### 6. 출처 경계 vs 쿠키 경계

```text
다른 포트 페이지: localStorage.mine=null document.cookie="theme=dark"
```

- localStorage는 출처(스킴·호스트·포트)마다 따로라 못 본다(제3자 iframe이면 Chrome 115+는 최상위 사이트로도 나눈다).
- 쿠키는 포트로 나뉘지 않는다(RFC 6265 §8.5). 그래서 `theme`이 보였다.

### 7. best-effort vs persistent, 축출

- best-effort: 기본값. 공간 압박 때 브라우저가 지울 수 있다.
- persistent: `navigator.storage.persist()`가 허락된 경우. 축출에서 제외된다. Firefox는 사용자에게 묻고, Chrome·Edge·Safari는 사용 이력으로 판정한다. 실험에서는 `false`였다.
- 축출: 가장 오래 안 쓴(LRU) 출처부터, 그 출처 데이터 **전부**를 지운다(MDN, 기본 버킷 하나일 때). Chromium 122+ Storage Buckets로 버킷을 나누면 버킷별로 지울 수 있다.

### 8. Safari 초안 소실

- Safari ITP의 7일 상한: 사용자 상호작용 없이 Safari 사용 7일이 지나면 스크립트가 쓴 저장소(IndexedDB·localStorage·서비스 워커 등록·캐시 등)를 지운다(WebKit 2020-03-24). 서버가 설정한 쿠키는 제외(MDN).
- 또는 공간 압박 축출.
- 대처: 초안을 서버에 자주 동기화하고, 앱 시작 시 로컬 데이터가 없으면 서버에서 복구한다. 홈 화면 웹 앱은 별도로 센다.

### 9. 트랜잭션 안의 await fetch

- IndexedDB 트랜잭션은 대기 중인 요청이 없고 이벤트 루프로 돌아가면 자동 커밋된다. `fetch`를 기다리는 동안 트랜잭션이 끝나, 이후 `put`은 `TransactionInactiveError`가 난다.
- 순서: 네트워크로 먼저 받는다 → 새 트랜잭션을 열고 → 동기적으로 `put`을 이어서 건다 → `oncomplete`를 기다린다.

### 10. Chromium IndexedDB 백엔드

- LevelDB와 파일 혼합 구현에서 SQLite로 바뀌는 중이다. blink-dev 공지(2026-04-25): 148 DevTrial, 150 출시, 새 저장소부터 적용, 기존 데이터 이전은 다음 단계.
- LevelDB = LSM 트리: 쓰기를 순차 로그·메모리 테이블에 모으고 나중에 병합한다. 쓰기에 유리, 읽기·병합 비용.
- SQLite = B-트리: 페이지 단위 정렬 트리, 제자리 갱신. 범위 읽기가 곧다.
- 이 노트 실험(Playwright로 띄운 Chrome 151 디스크 프로필)에서는 `*.indexeddb.leveldb` 폴더가 생겼다. 필드 트라이얼을 끈 실행이라 일반 사용자 프로필의 백엔드는 확인 못 했다.
