# cs/issue/python/language-and-stdlib-traps — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 출처 원문 대조. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **통과한다.** Python에서 `bool`은 `int`의 하위 타입이라 `isinstance(True, int)`가 참이다. 그래서 JSON의 `true`가 "정수" 검증을 통과해 `1`로 쓰여 터미널 크기가 1×1로 적용되는 결함이었다(리뷰에서 발견). 정수만 받으려면 하위 타입을 거부하는 `type(x) is int`를 쓰거나 `not isinstance(x, bool)`을 명시한다. 같은 함정이 포트·시각 필드 검증에서도 나왔다. `nxt in "ei"`는 **부분문자열 검사**이고 빈 문자열은 모든 문자열의 부분문자열이라, "다음 모음 없음"을 `""`로 표현하면 조건이 **항상 참**이 된다. 단일 문자 멤버십은 튜플 `nxt in ("e", "i")`로 쓴다 — `"" in ("e", "i")`는 거짓이다. 이 패턴은 한 곳을 고친 뒤 같은 패턴 6곳을 전수 수정했다.
   > **하위 타입(subtype)** — 상위 타입의 모든 연산을 지원해 `isinstance` 검사를 통과하는 타입. "정수인가?"와 "정확히 int인가?"는 다른 질문이다.

2. **대입문은 우변을 끝까지 평가한 뒤에야 좌변의 옛 참조를 놓는다.** `self.index = read_index(new)`에서 새 인덱스를 다 읽는 동안 `self.index`는 여전히 옛 인덱스를 가리키므로 **둘이 동시에 메모리에 산다.** 교체 전후 크기 비교(`new.ntotal == self.index.ntotal`)도 두 객체를 동시에 요구했다. 그래서 피크가 2배 가까이 올라 호스트 OOM이 났다. 교정은 검증에 필요한 값만 먼저 꺼내고 → 옛 참조를 놓고(`None` 대입·`del`·`gc.collect()`) → 새로 읽는 순서다. 단, 새 파일이 손상됐을 때 **되읽을 원본이 없으면 미리 놓지 않는다**(정확성 우선). 피크는 222GB → 약 148GB(산정)로 줄었고, 실기동 동시 로드 성공으로 확인했다. `except` 블록 안에서는 **처리 중인 예외의 traceback이 발생 지점까지의 프레임과 그 지역변수를 참조**한다. 그래서 거기서 `del obj`를 해도 참조가 하나 남아 객체가 해제되지 않았고, 원본을 되읽으면서 다시 2배가 됐다. 교정은 except에서 플래그만 세우고 정리·복원을 블록 밖으로 옮기는 것이다. 회귀 테스트는 복원 읽기 시점에 캐시 객체의 weakref가 죽어 있음을 단언한다.
   > **traceback 프레임 참조** — 예외 객체의 `__traceback__`은 호출 스택의 프레임을 붙들고, 프레임은 지역변수를 붙든다. except 블록이 끝나야 이 연결이 풀린다.

3. **Python은 이름·속성·시그니처를 호출 시점에 해석하기 때문이다.** import·기동은 모듈 최상위만 실행하므로, 함수 본문 안의 `QueryBuilder.Prefix`(없는 속성), `query.get(...)`(실제로는 튜플), 오타 난 변수명, 빠진 필수 인자는 **그 분기가 실행될 때까지** 아무 오류도 내지 않는다. 드문 입력·옵션·지역 분기에서만 그 줄이 실행되고, 여러 분기를 복붙한 구조에서는 한 곳만 어긋나도 그 분기만 500이 된다. 인스턴스 메서드를 인스턴스 없이 `Class.method(a, b)`로 부르면 Python은 **첫 인자를 `self`에 바인딩**한다 — `self=a`, 첫 파라미터=`b`가 되고 마지막 인자가 비어 `missing 1 required positional argument`가 난다. 진입점은 `@staticmethod`, 내부는 인스턴스 메서드로 섞여 있던 한 분기만 이 결함이 있었다. 템플릿 엔진도 같은 계열이다 — Jinja2의 `x.items`는 속성 조회를 먼저 시도하므로 dict의 키 `items`보다 **메서드**가 반환되어 "not iterable"이 난다.
   > **늦은 바인딩(late binding)** — 이름이 가리키는 대상을 코드를 읽을 때가 아니라 그 줄을 실행할 때 찾는 방식. 실행되지 않은 줄의 오류는 발견되지 않는다.

4. **비용이 0이 아니다.** 로깅 호출의 인자는 **함수에 들어가기 전에** 평가되므로, 레벨 판정으로 출력을 버려도 `json.dumps`는 매 요청 대형 쿼리를 직렬화한다. `if logger.isEnabledFor(logging.DEBUG):`로 감싸야 비용이 사라진다. `dict.get(k, default)`의 default는 **키가 없을 때만** 쓰인다. 키가 있고 값이 `null`이면 `None`이 반환되고, 이어지는 `f"{score:.4f}"`가 TypeError를 낸다. 필드 정렬을 하면 검색 결과의 점수가 `null`로 오므로 이 경로가 실제로 열린다. 원래 특정 검색 전용이던 점수 로깅의 가드가 주석 처리되어 **모든 검색**에서 이 코드가 돌았고, 그래서 관찰용 코드가 정상 요청의 크래시 지점이 됐다. 교정(계획): 가드 복원 + debug로 강등 + `hit.get("_score") or 0.0` + `logger.debug(json.dumps(...))` 패턴 전수 교체.
   > **eager 평가** — 인자 식을 호출 전에 모두 계산하는 규칙. 결과를 쓰지 않을 호출이어도 인자 계산 비용과 부작용은 이미 일어난다.

5. 기본값은 **그 계층을 지날 때만** 적용되고, 모르면 조용히 데이터를 제한한다.
   - **csv 필드 상한** — `csv` 리더는 셀 하나를 기본 131072바이트로 제한한다. 여러 값을 한 셀에 이어붙이는 wide 포맷이 커지자 **읽기 단계**에서 `field larger than field limit`로 실패했다 → `csv.field_size_limit(sys.maxsize)`(메모리가 허용하는 범위에서 — C long이 32비트인 플랫폼(Windows)에선 `sys.maxsize`가 OverflowError라 더 작은 값을 준다).
   - **정규식 방언** — 표준 `re`는 `\p{Mn}` 같은 유니코드 속성 클래스를 지원하지 않는다. 다른 언어의 정규식을 1:1로 **포팅할 때** 그대로 옮길 수 없다 → `unicodedata.normalize("NFD")` + `category(ch) != "Mn"` 필터. 같은 포팅 함정으로 `split("\\s+")`(정규식 분할)과 Python `split(" ")`은 다르고, 가까운 대응은 인자 없는 `split()`이다(선행 공백이 만드는 빈 첫 원소 처리 등 세부는 다르다).
   - **JSON 인코더** — 표준 인코더는 `datetime`을 모른다 → **직렬화 시점**에 `not JSON serializable` → isoformat으로 변환.
   - **ORM 쪽 default** — `Column(default=0)`(SQLAlchemy의 클라이언트 쪽 default)은 SQLAlchemy가 INSERT 문을 생성할 때(ORM flush·Core `insert()`)만 채워진다. `text("INSERT ...")` raw SQL은 **DB 서버의 DEFAULT만** 적용되므로 NOT NULL 위반이 났다 → INSERT에 값을 명시(또는 서버 쪽 default).
   - **logging 전역 이름** — logger는 이름 기반 전역 싱글톤이라, 파일명(basename)으로 이름을 지으면 같은 파일명의 모듈들이 logger 하나를 공유한다. 재설정 때 핸들러를 close하지 않고 비우면 fd가 샌다. `FileHandler`는 회전하지 않는다. 상대경로 로그 디렉터리는 cwd에 따라 볼륨 밖을 가리킬 수 있다(잠재 이슈로 진단).

6. **공통 원인: 제출하자마자 기다렸다.** 루프 안에서 `f = ex.submit(...)` 직후 `f.result()`로 블로킹하면, 다음 작업을 제출하기 전에 현재 작업의 완료를 기다리므로 풀이 있어도 **순차 실행**이다. 게다가 워커 함수 본문에서 대형 사전·DB 연결을 매 태스크마다 초기화했다. 교정: `ProcessPoolExecutor(initializer=_worker_init)`로 워커 프로세스당 1회만 로드하고(1,072회 → 4회), `max_workers*2` 크기 청크를 한꺼번에 제출한 뒤 `as_completed`로 모았다(예상 7.4일 → 1.8일). 비동기 크롤러도 루프 안에서 `await fetch(u)`를 하나씩 하면 직렬이다 → `asyncio.Semaphore(5)` + `gather`. `multiprocessing.Pool`의 initializer가 예외로 죽으면 워커가 **재생성을 반복**하고(Pool의 일반 동작 — 원문은 "에러 없이 무한 hang"만 기록), 그 오류가 부모로 전달되지 않아 `imap` 호출자는 **에러 없이 영원히 기다린다.** (`concurrent.futures.ProcessPoolExecutor`는 다르다 — Python 3.7+에서 initializer 실패 시 풀이 깨져 대기 중 future가 `BrokenProcessPool`로 실패한다.) 실제 원인은 로컬 환경에 DB 인증 플러그인용 암호화 패키지가 없던 것이었다(컨테이너 이미지에는 포함).
   > **제출-대기 분리** — 작업을 먼저 모두 제출(fan-out)하고 완료를 나중에 모으는(fan-in) 구조. 이 분리가 없으면 풀·이벤트 루프는 병렬성을 쓰지 못한다.

7. 이 부류는 "그 줄이 실행될 때"만 드러나므로 **그 줄을 실행시키는 수단**이 필요하다.
   - **전 경로 실행 테스트** — 동적 타입 결함 묶음은 API 통합 테스트로 분기×검색유형 조합을 전수 호출해서 발견됐다. 발견 수단 자체가 "모든 경로를 한 번씩 실행"이었다.
   - **정적 검사** — 없는 속성·import 오류는 import 전수 검증 스크립트나 mypy/pyflakes 같은 도구로 실행 전에 잡을 수 있다(도입 검토 언급 단계).
   - **경계값 테스트** — `True`를 정수 자리에 넣기(그리고 커널에 적용된 실제 터미널 크기를 조회해 이전 값이 유지됐는지 단언), `null` 점수, 빈 문자열, 대문자 해시처럼 "의미상 이상하지만 타입상 통과하는" 값을 넣는다. 외부 도구 출력(소문자 hex)과 비교할 값은 같은 정규형으로 강제하고, 스키마 검증이 실패하면 롤백을 거부한다(fail-closed).
   - **실제 자원 계측** — 메모리 함정은 코드 리뷰가 아니라 실측(피크 RSS, weakref 사망 단언, 실기동 동시 로드)으로만 입증됐다. "Python이 해제하면 OS RSS가 돌아온다"는 가정도 실기동에서야 확인됐다(일반론으로는 할당기에 따라 해제가 곧바로 RSS 감소로 이어지지 않을 수 있다 — 대형 네이티브 할당은 보통 반환되지만 작은 객체 풀은 남는다. 그래서 가정이 아니라 계측 대상이다).

## 문제 구조 (추상화 코드)

### 변형 A — 타입·멤버십 검사가 직관과 다름
① 문제 코드
```python
if not (isinstance(cols, int) and isinstance(rows, int)):   # True 통과 → resize(1, 1)
    return
if c == "c":
    return SOFT if nxt in "ei" else HARD                 # nxt == "" → 항상 SOFT
if rec.date and len(rec.date) >= 4:                         # date 가 list 가 되면 요소 개수 비교
    year = rec.date[:4]                                     #   슬라이스도 리스트 슬라이스
```
② 고친 코드
```python
if type(cols) is not int or type(rows) is not int:          # 하위 타입(bool) 거부
    return
if c == "c":
    return SOFT if nxt in ("e", "i") else HARD            # 원소 멤버십
years = {d[:4] for d in rec.date} if isinstance(rec.date, list) else {rec.date[:4]}
```
무엇이 깨졌나: 값의 "모양"(하위 타입·빈 문자열·str/list)에 따라 같은 연산의 의미가 바뀌는데 검사는 한 가지 모양만 가정했다.\
같은 구조: 콤마 구분 문자열과 리스트를 `!=`로 비교해 항상 True → 문자열은 split 후 set 비교.\
같은 구조: 대문자 해시가 truthy 검사만 통과 → 외부 도구 출력(소문자)과 비교 어긋남 → `^[0-9a-f]{40}$` 강제 + `not isinstance(x, bool)`.\
같은 구조: 값 없는 클래스 본문 애노테이션 `x: int`는 `__annotations__`에만 기록되고 클래스 속성을 만들지 않는다(`hasattr(Cls, "x")`는 False) — 클래스 속성이 필요하면 값을 대입하고, 클래스 변수임은 `x: ClassVar[int] = 0`처럼 표시한다(`ClassVar` 자체는 dataclass·타입 검사기용 표시일 뿐 값 없이는 역시 속성을 만들지 않는다).\
같은 구조: `if not self.collection:` → `if self.collection is None:` — 라이브러리 버전 변화에서 진리값 판정이 버그가 되어 명시적 None 비교로 교체(원문은 수정 사실만 기록).

### 변형 B — 참조 수명이 메모리 피크를 만듦
① 문제 코드
```python
def reload(self):
    loaded = read_index(path)                         # 우변 평가 동안 self.index(옛것)도 생존
    if loaded.ntotal != self.index.ntotal:            # 비교가 두 객체 동시 상주를 요구
        # ...
    self.index = loaded

try:
    configure(loaded)
except ConfigureError:
    del loaded                                        # traceback 이 프레임을 붙듦 → 해제 안 됨
    self.index = read_index(original)                 # 다시 2배
```
② 고친 코드
```python
def reload(self):
    current = self.index
    expected = current.ntotal if current is not None else None   # ① 값만 보관
    if restorable:                                              # 되읽을 원본이 있을 때만
        self.index = None; del current; gc.collect()             # ② 읽기 전 반납
    loaded = read_index(path)                                    # ③ 로드

failed = False
try:
    configure(loaded)
except ConfigureError:
    failed = True                                     # except 안에서는 플래그만
if failed:
    del loaded; gc.collect()                          # 블록 밖에서 정리
    self.index = read_index(original)
# 테스트: 복원 읽기 시점에 weakref(loaded)() is None 단언
```
무엇이 깨졌나: 코드상 "교체"가 메모리상으로는 "공존" 구간을 가졌고, 예외 처리 중에는 보이지 않는 참조가 하나 더 있었다.

### 변형 C — 호출 시점에만 해석되는 이름·시그니처
① 문제 코드
```python
query = Builder.build_with_collection(param)          # 실제 반환은 (query, params) 튜플
check_limit(query.get("query", {}))                   # 'tuple' object has no attribute 'get'

class QueryBuilder:
    @staticmethod
    def build(name, search_type):
        return QueryBuilder._build_ops(parsed, search_type)   # 인스턴스 메서드를 클래스로 호출
    def _build_ops(self, parsed, search_type): ...            #   self=parsed → search_type 누락

QueryBuilder.Prefix(...)                              # 없는 속성 → 그 분기에서만 AttributeError
```
② 고친 코드
```python
query, collected = Builder.build_with_collection(param)   # 튜플 언패킹

return QueryBuilder()._build_ops(parsed, search_type)     # 상태 없는 클래스 → 인스턴스화해 bound 호출

class QueryBuilder:
    Prefix = PrefixQuery                                  # 없던 바인딩 추가
```
무엇이 깨졌나: 반환형·시그니처·속성 존재를 호출부가 가정했고, 그 분기를 실행하는 테스트가 없었다.\
같은 구조: 선언과 다른 변수명 참조(NameError), 필수 인자 누락(TypeError), 빈 문자열이 validator에서 None으로 바뀐 뒤 `None.replace()`(null/빈 가드 추가), enum `.value` 이중 호출, 빈 리스트 인덱싱(IndexError → `if not field_names: return`).\
같은 구조: 템플릿 변수 키 `items`가 dict 메서드 `.items`에 가려짐 → 키 이름을 `rows`로, `items/keys/values` 키 금지.

### 변형 D — 관찰 코드의 평가 시점·전역 상태
① 문제 코드
```python
# if is_similar and hits:                            # 가드 주석 처리 → 모든 요청에서 실행
for hit in hits:
    score = hit.get("_score", 0)                     # 값이 null → None
    logger.info(f"{score:.4f}")                      # TypeError → 정상 요청 500
logger.debug(json.dumps(query, indent=2))            # debug 꺼져도 매번 직렬화

logger = logging.getLogger(os.path.basename(__file__))   # 같은 파일명 모듈끼리 logger 공유
handler = logging.FileHandler("../logs/all/app.log")     # 회전 없음 · cwd 기준 상대경로
```
② 고친 코드 (계획)
```python
if is_similar and hits:
    for hit in hits:
        score = hit.get("_score") or 0.0
        logger.debug(f"{score:.4f}")
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(json.dumps(query, indent=2))

logger = logging.getLogger(__name__)                     # 모듈 전체 경로
for h in list(logger.handlers):
    h.close(); logger.removeHandler(h)                   # 재설정 시 close — fd 반납
handler = TimedRotatingFileHandler(os.path.join(LOG_DIR, "app.log"), when="midnight", backupCount=30)
```
무엇이 깨졌나: 로깅 인자는 레벨 판정 전에 평가되고, logger는 이름 기반 전역 객체이며, 핸들러는 명시적으로 닫아야 자원이 반납된다.

### 변형 E — 표준 라이브러리·ORM 기본값
① 문제 코드
```python
rows = csv.reader(f)                                  # 셀 > 131072B → field larger than field limit
re.sub(r"\p{Mn}", "", nfd)                            # re 는 \p{..} 미지원
json.dumps({"at": datetime.now()})                    # not JSON serializable
session.execute(text("INSERT INTO outbox (id, payload) VALUES (:id, :p)"))
#   모델: retry_count = Column(Integer, default=0, nullable=False) → raw SQL 엔 적용 안 됨
```
② 고친 코드
```python
csv.field_size_limit(sys.maxsize)
"".join(ch for ch in unicodedata.normalize("NFD", s) if unicodedata.category(ch) != "Mn")
json.dumps({"at": datetime.now().isoformat()})
session.execute(text("INSERT INTO outbox (id, payload, retry_count, max_retries) VALUES (:id, :p, 0, :m)"))
```
무엇이 깨졌나: 기본값·기능 범위가 라이브러리 계층에 있는데, 그 계층을 우회하거나 다른 언어의 기대를 가져왔다.

### 변형 F — 동시성 도구의 사용 규칙
① 문제 코드
```python
with ProcessPoolExecutor(max_workers=5) as ex:
    for batch in batches:
        ok, failed = ex.submit(work, batch).result()      # 제출 직후 대기 → 순차
def work(batch):
    dictionary = load_big_dictionary()                    # 매 태스크 재로드

for url in urls:
    pages.append(await fetch(url))                        # 비동기지만 직렬

with Pool(n, initializer=worker_init) as pool:            # worker_init 가 연결 실패로 예외
    for r in pool.imap(work, items): ...                  #   → 워커 재생성 반복, 호출자 무한 대기
```
② 고친 코드
```python
with ProcessPoolExecutor(max_workers=5, initializer=_worker_init) as ex:   # 워커당 1회 로드
    for chunk in chunks(batches, size=5 * 2):
        futures = [ex.submit(work, b) for b in chunk]                      # 먼저 모두 제출
        for f in as_completed(futures): ...                                # 나중에 수집

sem = asyncio.Semaphore(5)
async def bounded(u):
    async with sem:
        return await fetch(u)
pages = await asyncio.gather(*(bounded(u) for u in urls))
```
무엇이 깨졌나: 병렬 도구를 쓰면서 제출과 대기를 한 걸음에 묶었고, 풀 초기화 실패는 부모에게 전달되지 않는다는 성질을 몰랐다.\
같은 구조: `result()`·후처리·다음 `submit()`을 한 try로 감싸 풀 붕괴(`BrokenProcessPool`)가 직전 성공 배치의 실패로 오귀속되고, try 안에서 `del`한 키를 except에서 다시 `del`해 `KeyError`로 파이프라인 전체가 죽음 → try를 `result()`만으로 좁히고 `pop(future, None)`, 풀 붕괴는 실패 기록 없이 플래그 → 재시도로 넘김.
```python
batch = pending_batches.pop(future, None)
try:
    result = future.result()
except BrokenProcessPool:
    pool_dead = True; retry.append(batch); continue   # 성공 배치를 실패로 적지 않음 — pop 한 배치는 재시도 목록에 보존, 이후 submit 금지
except Exception:
    save_failed(batch); continue                  # 해당 배치만 실패
```

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
