# cs/issue/python/module-resolution-and-accidental-pass — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

> 메타 태그: `accidental-pass` · `silent-failure` · `module-resolution`

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

## 이번 프로젝트 사례

- [llm/issue3](../../../../project/study-note-deploy-system/llm/issue3/) — LLM 래퍼를 `src/app` ↔ `src/test` 미러 구조로 정리하며 "`pytest`는 죽고 `python -m pytest`는 통과"의 정체를 규명. 임시방편이던 빈 `conftest.py`를 지우고 `pyproject.toml`의 `pythonpath = ["src"]`·`testpaths = ["src/test"]`로 정식화, 런타임은 `Dockerfile`에서 `uvicorn app.app:app --app-dir src`로 기동 경로를 고정(당시 25건 green). 판정은 "conftest 없이 직접 pytest 실행 → collection error 재현"으로 실측.

## 검증 기록

- 2026-09-23: 이슈 README(llm/issue3) + 실제 코드·설정 대조 (Claude 초안).
- 코드 확인 (`.../study-note-deploy-system-llm/wrapper/`):
  - `pyproject.toml` L1-3 — `[tool.pytest.ini_options]` / `pythonpath = ["src"]` / `testpaths = ["src/test"]`(테스트 실행 경로에서 뿌리 고정).
  - `Dockerfile` L6-8 — `COPY src ./src` / `CMD ["uvicorn", "app.app:app", "--app-dir", "src", ...]`(런타임 실행 경로에서 뿌리 고정).
  - `conftest.py` 부재 확인 — `find . -name conftest.py` 결과 없음(임시방편 삭제됨).
  - `src/app/api.py` L11-14, `src/app/app.py` L11-12 — `from app.domain.envelope import ...` / `from app import api` 등 `app` 절대 import(코드가 옆 폴더의 `app`을 부르는 구조).
  - `src/test/` — `test_api.py`·`domain/test_envelope.py`·`domain/test_prompt.py`·`usecase/test_rewrite.py` 등 `src/app` 미러 구조 확인.
