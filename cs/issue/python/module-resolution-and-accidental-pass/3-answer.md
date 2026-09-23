# cs/issue/python/module-resolution-and-accidental-pass — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `test-reliability`

## 정답

<!-- 질문 1:1 대응 -->

1. 두 실행 방식이 `sys.path`의 맨 앞에 넣는 폴더가 다르다. **`python -m pytest`** 는 파이썬이 `-m`으로 모듈을 실행할 때 규칙대로 **현재 작업 폴더(CWD)** 를 `sys.path`에 넣는다 — 그래서 CWD 아래에 `app/`이 있으면 `from app import ...`가 찾아진다. **그냥 `pytest`** 는 그런 CWD 삽입을 하지 않고, 수집한 **테스트 파일이 있는 폴더**(rootdir 기반)를 경로에 넣는다 — 코드가 옆(다른) 폴더에 있으면 `app`을 못 찾는다. 같은 코드·같은 테스트인데 경로에 무엇이 들어가느냐가 실행 방식에 따라 달라 결과가 갈린다.
   > **`sys.path`** — 파이썬이 `import X`를 만났을 때 `X`를 찾으러 뒤지는 폴더 목록. import의 성패는 이 목록에 달려 있고, 이 목록은 "무엇을 어떻게 실행했나"에 따라 달라진다.

2. **우연한 통과(accidental pass)** 는 코드가 계약을 만족해서가 아니라, 실행 환경이 우연히 빠진 조건을 대신 채워줘서 나는 초록불이다. 성립 조건: (a) 코드에 **환경 의존 결함**이 있고(여기선 "app을 어디서 찾을지"가 코드·설정에 고정돼 있지 않음), (b) 개발자가 쓰는 특정 실행 방식이 그 결함을 **우연히 가려주는** 부수효과를 갖는다(`-m`의 CWD 삽입). 두 조건이 겹치면, 그 실행 방식 안에서만 초록불이고 환경이 바뀌면 깨진다 — 초록불이 코드가 아니라 환경의 속성이 된다.
   > **우연한 통과(accidental pass)** — 코드의 정당성이 아니라 실행 환경의 우연한 성질에 기대어 나는 통과. 환경이 재현되지 않으면 사라지는, 신뢰할 수 없는 초록불.

3. 로컬에서 `python -m pytest`로 개발하면 CWD가 경로에 들어가 import가 계속 풀리므로 **개발자는 결함을 볼 일이 없다** — 항상 초록불이다. 그런데 CI나 깨끗한 환경은 관례적으로 그냥 `pytest`를 돌리고, 그러면 CWD 삽입이 없어 `from app import ...`가 **collection error(ImportError)** 로 죽는다. 결함은 처음부터 있었지만 로컬의 실행 방식이 그것을 상시 가려왔기 때문에, 실행 방식이 다른 첫 환경(CI)에서야 드러난다. "개발 중엔 안 보였다"는 곧 "내 실행 방식이 결함을 대신 메워주고 있었다"는 뜻이다.

4. 공통 뿌리는 **"코드(`app` 패키지)와 그것을 부르는 쪽(테스트/기동 명령)이 서로 다른 폴더에 있는데, `app`을 절대 import로 부른다 → `app`을 찾을 기준 폴더가 코드·설정에 고정돼 있지 않다"** 이다. 이 뿌리는 두 실행 경로에서 각각 터지므로 각각 못 박아야 한다: 런타임은 `uvicorn app.app:app --app-dir src`로 "import 기준 폴더 = src"를 서버에 알리고, 테스트는 `pyproject.toml`의 `pythonpath = ["src"]`로 pytest 실행 시 src를 경로에 넣는다. **한 뿌리(모듈 검색 기준의 부재), 두 고정점(런타임·테스트).**
   > **`--app-dir src`** — uvicorn에게 "임포트의 기준 폴더는 src다"라고 알려주는 옵션. 그래야 `app.app:app`(= src/app/app.py 안의 app 객체)을 찾아 띄운다. `pythonpath=["src"]`는 이와 같은 일을 pytest 실행 경로에서 한다.

5. 빈 `conftest.py`는 내용이 없어도 **존재만으로** pytest에게 그 폴더를 rootdir/경로 계산의 기준으로 삼게 하는 부수효과가 있어, import가 우연히 풀렸다. 그것이 임시방편인 이유: (a) "왜 통하는지"가 파일 내용이 아니라 파일의 *위치가 만드는 부수효과*라 의도가 코드에 드러나지 않고, (b) 목적("src를 import 경로에 넣는다")이 어디에도 명시돼 있지 않아 다음 사람이 지우거나 옮기면 조용히 깨진다. 정식 해법은 목적을 **직접 선언**하는 것 — `pyproject.toml`에 `pythonpath = ["src"]`, `testpaths = ["src/test"]`로 "무엇을 경로에 넣고 어디서 테스트를 찾을지"를 명시하면, 우연이 아니라 설정으로 통한다. 정식화 후 빈 conftest는 삭제했다.
   > **`conftest.py`** — pytest가 자동으로 인식하는 설정·픽스처 파일. 있는 것만으로 경로 계산에 영향을 주므로, "부수효과로 경로를 잡는" 용도로 오용되면 의도가 숨는다.

6. "누가 맞나 따지기"는 두 사람의 *주장*을 비교하는 것이라, 둘 다 서로 다른 실행 방식을 전제로 말하면 영원히 안 좁혀진다("나는 되는데" vs "나는 안 되는데"). **"conftest 없이 pytest를 직접 돌려 재현"** 은 주장이 아니라 **산출물**(실제 collection error)을 만들어낸다 — 그 error는 누가 옳다고 우기든 상관없이 그 조건에서 재현되는 사실이다. 그래서 "직접 실행해 재현"이 옳은 판정 방식이다: 논쟁을 관측 가능한 사실로 환원한다. 이 프로젝트의 원칙이 "누가 맞는지 따지지 말고 실측한다"인 이유다.

7. 우연한 통과는 **green 위장**(초록불이 실제 정당성을 반영하지 못함)의 한 형태이고, green 위장은 silent failure의 특수한 사례다 — 검증 장치(테스트)가 "통과"라는 성공 신호를 내지만 그 신호가 코드의 옳음이 아니라 실행 환경의 우연을 반영한다. 즉 **실패(환경 의존 결함)가 발생 가능한데도 성공 신호가 나가 아무도 못 알아챈다.** "테스트 통과 ≠ 검증 완료"는 바로 이 지점을 겨눈다 — 통과가 **어느 환경에서든 재현되는 산출물**인지(CWD 삽입 같은 우연에 안 기대는지)를 되물어야 검증이 완료된다. 그래서 초록불을 볼 게 아니라 "다른 실행 방식·깨끗한 환경에서도 같은가"를 실측해야 한다.
   > **green 위장(false green)** — 검증이 계약이 아니라 엉뚱한 것(실행 환경의 우연)을 재고 있어, 초록불인데 제품/코드가 틀린 상태. 검증이라는 산출물마저 거짓 성공 신호가 된 silent failure.

## 문제 구조 (추상화 코드)

### 변형 A — 옆 폴더의 패키지를 절대 import, 검색 기준이 실행 방식에 맡겨짐
① 문제 코드
```text
project/
  src/
    app/        api.py:  from app.domain.envelope import ok   # 절대 import
    test/       test_endpoints.py: from app import api
  conftest.py   (빈 파일 — 존재만으로 경로 계산이 바뀌어 우연히 통과)
```
```sh
python -m pytest     # CWD 가 sys.path 에 들어감 → 통과 (우연)
pytest               # CWD 삽입 없음 → collection error (ImportError)
```
② 고친 코드
```toml
# pyproject.toml — 테스트 실행 경로의 기준을 선언
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths  = ["src/test"]
```
```dockerfile
# 런타임 실행 경로의 기준을 선언
COPY src ./src
CMD ["uvicorn", "app.app:app", "--app-dir", "src", ...]
```
```text
빈 conftest.py 삭제 — 판정은 "conftest 없이 pytest 직접 실행 → collection error 재현"으로 실측
```
무엇이 깨졌나: 모듈 검색 기준 폴더가 코드·설정 어디에도 없었고, 개발자의 실행 방식(`-m`의 CWD 삽입)과 빈 파일의 부수효과가 그 빈자리를 우연히 메웠다.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A)은 "모듈 검색 기준을 실행 경로마다 설정으로 선언한다"이다. 같은 원리(실행 경로·해석 순서·import 시점에 따라 초록불이 우연히 켜지거나 꺼진다)에 다른 방안이 쓰인 사례:

### 방안 1 — 해석 순서 자체를 계약으로 고정 (JVM 클래스패스 순서)
```kotlin
// 문제: 커스텀 테스트 소스셋 — 컴파일 클래스패스엔 main 출력이 있지만 런타임 클래스패스엔 없음
val checkImplTest by tasks.registering(Test::class) {
    classpath = checkImpl.output + /* main.output 없음 */ testRuntimeClasspath   // 런타임에 인터페이스 없음 → 테스트 1개만 발견·실패
}
// 고친: 앞선 항목이 이긴다 — 순서가 곧 "구현이 스켈레톤을 덮고, main 이 빈 클래스를 메운다"는 계약
val checkImplTest by tasks.registering(Test::class) {
    classpath = checkImpl.output + test.output + main.output + testRuntimeClasspath
}
```
앞선 두 사례는 구현 쪽에 모든 클래스가 있어 드러나지 않았고, 일부 클래스만 구현하는 세 번째 사례에서야 잡혔다.

### 방안 2 — 패키지 `__init__`의 import 시점 부작용 제거 (등록을 lifespan으로)
```python
# 문제: search/__init__.py — import 만 해도 모든 하위 구성요소를 즉시 등록(DB 인스턴스 생성 포함)
from .comp_a import register as ra; ra(registry)
from .comp_b import register as rb; rb(registry)       # 한 구성요소의 선택 의존성만 없어도
# ...                                                   #   하위 모듈 어떤 것을 import 하든 전체 수집 실패

# 고친: search/__init__.py 는 비움 → 앱 시작 시 등록
@asynccontextmanager
async def lifespan(app):
    register_all(registry)                               # 테스트는 import 만으로 부작용 없음
    yield
```
결과: 수집 실패 때문에 코드 리뷰로 검증을 대신하던 테스트 모듈들이 다시 수집되고, 이후 전체 스위트가 0 failed로 통과했다.

### 방안 3 — import 시점 외부 연결 제거 (lazy factory + lifespan warming)
```python
# 문제: instances.py — 모듈 레벨 싱글톤이 import 시점에 연결
search_db = SearchClient(hosts)          # from main import app 만 해도 연결 시도
rdb = RelationalDB(dsn)                  #   → DB 없는 CI 에서 테스트 수집 불가

# 고친 (권고 단계)
@lru_cache
def get_search_db() -> SearchClient:     # 첫 사용 시 생성
    return SearchClient(hosts)

@asynccontextmanager
async def lifespan(app):
    get_search_db()                      # 기동 시 미리 데움 — 연결 시점을 수명주기가 통제
    yield
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 검색 기준을 실행 경로별로 선언 | 실행 경로(테스트·런타임)가 여럿이다 | 설정 두 곳 | 새 실행 경로(스크립트·CI 잡)가 선언 없이 추가되면 재발 | 코드와 호출자가 다른 폴더에 있는 레이아웃 |
| 1. 해석 순서를 계약으로 고정 | 같은 이름의 클래스가 여러 곳에 있고 앞선 것이 이긴다 | 순서 한 줄 + 회귀 확인 | 순서가 바뀌면 조용히 다른 구현이 로드됨 | 스켈레톤·구현을 겹쳐 쓰는 빌드 |
| 2. `__init__` 부작용 제거 | import 가 등록·연결을 일으킨다 | 등록 지점 이동 | 등록을 잊은 구성요소는 기동 후 없음 | 선택 의존성이 구성요소마다 다른 패키지 |
| 3. lazy factory + lifespan | 모듈 레벨 싱글톤이 외부 자원에 연결한다 | 접근 경로를 함수로 교체 | 워밍 누락 시 첫 요청이 연결 비용을 짐 | 테스트·CI 가 외부 자원 없이 돌아야 할 때 |

**결론**: 초록불이 "어떻게 실행했나"에 따라 갈리면, 그 차이를 만든 **암묵적 입력**을 찾아 명시한다.\
검색 기준이 암묵적이면 설정으로 선언하고(기본), 해석 순서가 암묵적이면 순서를 계약으로 고정한다(1).\
import가 부작용(등록·연결)을 일으키면 부작용을 수명주기(lifespan)로 옮겨, import는 이름만 가져오게 만든다(2·3).
