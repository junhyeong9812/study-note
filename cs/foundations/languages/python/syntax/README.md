# Python — 문법·API 주제 목록

> 1단계 리스트업이다. 아래 주제들의 3파일(질문·서머리·정답)은 **아직 없다**.
> 기준 소스: [Python 3.12 언어 레퍼런스](https://docs.python.org/3.12/reference/index.html) · [표준 라이브러리 3.12](https://docs.python.org/3.12/library/index.html) · [PEP 인덱스](https://peps.python.org/)
> 실행 검증: **가능**. 이 머신에 `python3` 3.12.3 이 있어 3.12 까지의 예시는 실제로 돌려 출력을 확인한다. 3.13 전용 동작(PEP 696 기본값·`TypeIs`·free-threaded)은 설치본이 없어 문서·PEP 로만 접지하고 「미실행」으로 표기한다.
> 기준일 2026-09-20.

## 이 언어에서 무엇을 자르는 축

Python 은 **모든 것이 객체**이고 이름은 그 객체에 붙는 꼬리표라는 한 가지 모델 위에 문법이 얹혀 있다.
그래서 축을 ①**객체·이름·가변성**(여기서 조용히 틀리는 사고가 가장 많이 난다) ②**시퀀스·매핑·집합의 공통 연산** ③**반복 — 컴프리헨션에서 이터레이터·제너레이터까지 하나로 이어지는 프로토콜** ④**함수와 스코프**(인자 규칙·클로저·데코레이터) ⑤**클래스와 특수 메서드**(언어 문법이 객체 쪽으로 위임되는 지점) ⑥**예외·컨텍스트 매니저** ⑦**타입 힌트** ⑧**표준 라이브러리에서 실무 빈도가 높은 모듈** ⑨**동시성**으로 자른다.
언어 레퍼런스의 장 구분(어휘·데이터 모델·실행 모델·식·문)은 참고만 하고, 학습 단위는 **한 번에 인출할 수 있는 기능 하나**로 잡았다.
JS 와 대비가 값을 내는 자리(동적 타입·컴프리헨션·이터레이터·`async`)는 해당 행 설명에 그 대비를 적어 둔다.
「언제 들어왔나」는 [history/python](../../../../../history/python/)의 몫이고, 여기는 **어떻게 쓰고 무엇을 못 하나**만 다룬다.

## 주제 목록

| # | 주제 | 분류 | 무엇을 인출하게 되나 | 선행 | 기존 주제 | 우선 |
|---|------|------|----------------------|------|-----------|------|
| 01 | 객체와 이름 바인딩 모델 | 문법 | 대입이 값을 복사하지 않고 이름을 객체에 묶는다는 것을 그림으로 설명하고, 두 이름이 한 객체를 가리킬 때 한쪽 변경이 다른 쪽에 보이는지 예측할 수 있다 | — | `cs/foundations/variables-and-memory/` | A |
| 02 | `is` 대 `==` 와 인터닝 | 관용구 | 두 비교가 갈라지는 지점을 설명하고, 작은 정수·짧은 문자열에서 우연히 같아 보이는 이유와 `None` 비교에 무엇을 써야 하는지 판단할 수 있다 | 01 | — | A |
| 03 | 가변·불변과 얕은 복사·깊은 복사 | 관용구 | 중첩 리스트를 `list()`·`copy.copy`·`copy.deepcopy` 로 복사했을 때 각각 어디까지 공유되는지 예측할 수 있다 | 01 | — | A |
| 04 | 숫자 타입과 나눗셈 연산자 | 문법 | `/`·`//`·`%`·`divmod` 가 음수와 실수에서 내는 값을 예측하고 `-7 // 2` 가 왜 `-4` 인지 설명할 수 있다 | — | `cs/foundations/python-basics/` | A |
| 05 | 진릿값과 단축 평가 | 문법 | 빈 컨테이너·0·`None` 의 진릿값을 판정하고, `and`/`or` 가 bool 이 아니라 피연산자를 돌려준다는 성질에 기댄 코드의 결과를 예측할 수 있다 | — | `cs/foundations/python-basics/` | A |
| 06 | 문자열·bytes·유니코드 | 문법 | `str` 과 `bytes` 의 경계, `encode`/`decode` 가 필요한 자리, 인코딩을 틀렸을 때 나는 오류를 설명할 수 있다 | — | `cs/foundations/data-representation/` | A |
| 07 | 문자열 메서드 | 표준 API | `split`·`join`·`strip`·`replace`·`startswith`·`translate` 로 파싱·정규화를 짜고, 정규식을 꺼내야 하는 선을 판단할 수 있다 | 06 | — | B |
| 08 | f-string 과 포맷 스펙 | 문법 | 정렬·자릿수·천단위·`!r`·`=` 디버그 표기를 쓰고, 3.12(PEP 701)에서 완화된 중첩 따옴표·백슬래시 제한을 설명할 수 있다 | 06 | — | B |
| 09 | 시퀀스 공통 연산과 슬라이싱 | 문법 | 음수 인덱스·step·역순 슬라이스의 결과를 예측하고, 슬라이스 대입과 `del` 이 길이를 바꾸는 방식을 설명할 수 있다 | — | `cs/foundations/python-basics/` | A |
| 10 | list 메서드와 정렬 키 | 표준 API | `sort` 와 `sorted` 를 구분하고 `key`·`reverse`·안정 정렬을 이용해 다중 기준 정렬을 설계할 수 있다 | 09 | `cs/foundations/python-basics/` | A |
| 11 | tuple 과 언패킹 | 문법 | 별표 언패킹·중첩 언패킹·스왑을 쓰고, tuple 이 불변인데도 안에 든 리스트는 바뀔 수 있다는 것을 설명할 수 있다 | 09 | `cs/foundations/python-basics/` | A |
| 12 | dict 와 키 요건 | 표준 API | 삽입 순서 보장(3.7+)·`get`·`setdefault`·병합 연산자(3.9+)·뷰의 동적 성질을 쓰고, 어떤 객체가 키가 될 수 있는지 판정할 수 있다 | 02 | `cs/foundations/python-basics/` | A |
| 13 | set 과 frozenset | 표준 API | 집합 연산으로 중복 제거·포함 검사를 설계하고, 순서 없음과 해시 요건이 만드는 제약을 설명할 수 있다 | 12 | `cs/foundations/python-basics/` | B |
| 14 | 컴프리헨션 | 문법 | 조건·중첩·dict/set 컴프리헨션을 읽고 쓰며, 같은 일을 하는 루프와 가독성·성능을 비교 판단할 수 있다 | 09 | `cs/foundations/python-basics/` | A |
| 15 | 제너레이터 표현식과 지연 평가 | 문법 | 괄호 하나 차이로 메모리 사용이 달라지는 이유를 설명하고, 언제 리스트로 물질화해야 하는지 판단할 수 있다 | 14 | — | A |
| 16 | 이터레이터 프로토콜 | 문법 | `iter`/`next`/`StopIteration` 으로 `for` 가 하는 일을 재현하고, 소진된 이터레이터를 다시 돌릴 때 빈 결과가 나오는 것을 예측할 수 있다 | 15 | — | A |
| 17 | 제너레이터 함수와 `yield` | 문법 | `yield` 가 실행을 중단·재개하는 흐름을 추적하고 `yield from`·`send`·`close` 의 효과를 설명할 수 있다 | 16 | — | A |
| 18 | 반복 제어와 `for`/`while`·`else` | 문법 | `break`/`continue`/`else` 흐름과 `enumerate`·`zip`·`range` 의 지연 성질을 설명하고, 순회 중 컨테이너를 바꿀 때의 위험을 판단할 수 있다 | 16 | `cs/foundations/python-basics/` | B |
| 19 | 함수 인자 규칙 | 문법 | 위치·키워드·기본값·`*args`·`**kwargs`·`/`·`*` 전용 인자를 조합한 시그니처에 대해 어떤 호출이 가능한지 판정할 수 있다 | — | — | A |
| 20 | 가변 기본 인자 함정 | 관용구 | `def f(x=[])` 가 호출마다 같은 객체를 쓰는 이유를 설명하고 `None` 센티널로 고칠 수 있다 | 03, 19 | — | A |
| 21 | 스코프 LEGB 와 `global`·`nonlocal` | 문법 | 이름이 어느 스코프에서 풀리는지 판정하고, 대입 한 줄이 지역 변수를 만들어 `UnboundLocalError` 를 내는 경우를 설명할 수 있다 | 01 | — | A |
| 22 | 클로저와 늦은 바인딩 | 문법 | 루프에서 만든 함수들이 같은 값을 내놓는 이유를 설명하고 기본 인자·팩토리로 고칠 수 있다 | 21 | — | A |
| 23 | `lambda` 와 고차 함수 | 문법 | `lambda` 를 쓸 수 있는 자리와 제약을 말하고 `map`·`filter`·정렬 `key` 로 바꿔 쓸 수 있다 | 19 | `cs/foundations/python-basics/` | B |
| 24 | 데코레이터 | 문법 | 함수를 감싸는 데코레이터와 인자 있는 데코레이터를 직접 쓰고, `functools.wraps` 를 빠뜨리면 무엇이 깨지는지 설명할 수 있다 | 22 | — | A |
| 25 | 예외 처리와 `finally` | 문법 | `try`/`except`/`else`/`finally` 실행 순서, 예외 계층에 따른 포착 범위, `raise ... from` 의 체이닝을 설명할 수 있다 | — | — | A |
| 26 | EAFP 대 LBYL | 관용구 | 「먼저 검사」와 「일단 하고 예외」 중 어느 쪽이 경쟁 조건·비용 면에서 맞는지 판단할 수 있다 | 25 | — | B |
| 27 | 예외 그룹과 `except*` | 문법 | 3.11+ `ExceptionGroup` 이 여러 실패를 함께 나르는 방식과 `except*` 의 분배 규칙을 설명할 수 있다 | 25 | — | C |
| 28 | 컨텍스트 매니저와 `with` | 문법 | `__enter__`/`__exit__` 계약과 예외 억제 여부를 설명하고 `contextlib` 로 컨텍스트를 만들 수 있다. 괄호로 감싼 다중 `with` 는 3.10+ | 25 | — | A |
| 29 | 클래스와 속성 탐색 | 문법 | 인스턴스·클래스 속성 탐색 순서와 클래스 변수 공유를 설명하고 `__init__` 과 `__new__` 의 역할을 구분할 수 있다 | 01 | `cs/foundations/oop-basics/` | A |
| 30 | `__repr__`·`__eq__`·`__hash__` 계약 | 문법 | 세 메서드의 계약을 말하고, `__eq__` 만 정의했을 때 해시가 깨지는 이유를 설명하며 집합·dict 키로 쓸 클래스를 설계할 수 있다 | 12, 29 | — | A |
| 31 | 비교 프로토콜과 정렬 가능성 | 문법 | `__lt__` 하나로 정렬이 되는 이유, `functools.total_ordering`, 비교 불가 타입을 섞었을 때의 `TypeError` 를 설명할 수 있다 | 10, 30 | — | B |
| 32 | 컨테이너 프로토콜 | 문법 | `__len__`·`__getitem__`·`__contains__`·`__iter__` 를 구현해 내장 문법과 맞물리는 객체를 만들 수 있다 | 16, 29 | — | B |
| 33 | `property`·디스크립터·`__slots__` | 문법 | 속성 접근을 가로채는 세 장치의 위치를 구분하고 `__slots__` 가 무엇을 막고 무엇을 아끼는지 설명할 수 있다 | 29 | — | B |
| 34 | 상속·MRO·`super()` | 문법 | 다중 상속에서 MRO 를 계산하고 `super()` 가 「부모」가 아니라 「MRO 상 다음」을 가리킨다는 것을 설명할 수 있다 | 29 | `cs/foundations/oop-basics/` | B |
| 35 | 추상 베이스 클래스와 `Protocol` | 문법 | 명시적 ABC 와 구조적 `Protocol` 중 어느 쪽이 맞는지 고르고 런타임 강제 여부를 구분할 수 있다 | 34, 40 | — | B |
| 36 | `dataclasses` | 표준 API | `field`·`default_factory`·`frozen`·`order` 가 어떤 메서드를 만들어 내는지 예측하고 가변 기본값 금지 규칙을 설명할 수 있다 | 20, 30 | — | A |
| 37 | `enum` | 표준 API | `Enum`·`IntEnum`·`StrEnum`(3.11+)·`auto` 의 차이와 비교·직렬화에서의 주의점을 판단할 수 있다 | 29 | — | B |
| 38 | `namedtuple`·`NamedTuple`·`TypedDict` | 표준 API | 세 구조체의 런타임 정체(튜플인가 dict 인가)와 타입 검사상의 의미를 구분해 고를 수 있다 | 11, 12 | — | B |
| 39 | `match` 문 | 문법 | 3.10+ 패턴 종류(리터럴·시퀀스·매핑·클래스·캡처·가드)를 읽고, 소문자 이름이 비교가 아니라 캡처가 되는 함정을 설명할 수 있다 | 11 | — | B |
| 40 | 타입 힌트의 런타임 의미 | 문법 | 힌트가 실행을 바꾸지 않는다는 것과 `__annotations__`·문자열 지연 평가·`from __future__ import annotations` 의 효과를 설명할 수 있다 | 19 | — | A |
| 41 | `typing` 과 제네릭 신문법 | 표준 API | `X \| Y`(03.10+)·`Literal`·`TypeAlias`·PEP 695 `type`/`def f[T]`(03.12)·타입 매개변수 기본값과 `TypeIs`(03.13)의 쓰임을 구분할 수 있다 | 40 | — | B |
| 42 | 모듈·패키지·import 시스템 | 문법 | 절대·상대 import 해석과 `__init__.py` 의 역할, `if __name__ == "__main__"`, 순환 import 가 깨지는 지점을 설명할 수 있다 | — | — | A |
| 43 | `collections` | 표준 API | `deque`·`Counter`·`defaultdict`·`OrderedDict`·`ChainMap` 을 문제에 맞춰 고르고, `defaultdict` 가 조회만으로 키를 만드는 부작용을 설명할 수 있다 | 12 | `cs/data-structure/` (자료구조 원리) | A |
| 44 | `itertools` | 표준 API | `chain`·`islice`·`product`·`combinations`·`groupby` 를 조합하고 `groupby` 가 정렬을 전제한다는 것을 설명할 수 있다 | 16 | — | B |
| 45 | `functools` | 표준 API | `lru_cache`·`partial`·`reduce`·`cached_property`·`singledispatch` 의 효과와 캐시가 가변 인자·메모리에 주는 영향을 판단할 수 있다 | 24 | — | B |
| 46 | `re` | 표준 API | raw 문자열·`match`/`search`/`fullmatch`·그룹·탐욕 대 게으름·`sub` 를 쓰고 컴파일 캐시와 백트래킹 폭발을 설명할 수 있다 | 06 | `cs/algorithm/25-string-matching/` (알고리즘 쪽) | A |
| 47 | `json` | 표준 API | `dumps`/`loads` 의 타입 매핑, dict 키가 문자열로 바뀌는 것, `default`·`object_hook`·`ensure_ascii` 를 설명할 수 있다 | 12 | — | A |
| 48 | `pathlib` 와 파일 I/O | 표준 API | `Path` 조작과 `open` 의 모드·`encoding`·`newline` 을 고르고 텍스트·바이너리 모드의 차이를 설명할 수 있다 | 06, 28 | — | A |
| 49 | `datetime` 과 `zoneinfo` | 표준 API | naive 와 aware 의 차이, `timedelta` 연산, ISO 파싱·포맷, `zoneinfo`(3.9+)로 시간대를 붙이는 법을 설명할 수 있다 | — | — | A |
| 50 | `decimal`·float 정밀도·`round` | 표준 API | `0.1 + 0.2` 문제의 원인, `Decimal` 의 컨텍스트, `round` 의 짝수 반올림을 설명하고 금액 계산에 무엇을 쓸지 판단할 수 있다 | 04 | `cs/foundations/data-representation/` | A |
| 51 | `asyncio` 코루틴 기초 | 표준 API | `async def`/`await` 가 만드는 코루틴과 이벤트 루프·`asyncio.run` 을 설명하고, `await` 없이 호출했을 때 아무 일도 안 일어나는 것을 예측할 수 있다 | 17 | `history/python/06-핵심-개념-진화.md` (도입 역사) | A |
| 52 | `asyncio` 동시성 구조 | 표준 API | `Task`·`gather`·`TaskGroup`(3.11+)·타임아웃·취소 전파를 조합하고 블로킹 호출이 루프를 멈추는 이유를 설명할 수 있다 | 51 | — | B |
| 53 | GIL 과 병행 수단 선택 | 표준 API | `threading`·`multiprocessing`·`concurrent.futures`·`asyncio` 중 작업 성격에 맞는 것을 고르고 GIL 이 무엇을 막는지 설명할 수 있다. 3.13 free-threaded 는 실험적 | 52 | `cs/foundations/process-thread/` | A |

## 기존 주제와 겹치는 것

- **`cs/foundations/python-basics/`** — 부트캠프 교재를 따라 친 입문 노트(리스트·딕셔너리·튜플·집합·연산자·제어문·for·while). 여기 목록의 **#4·5·9·10·11·12·13·14·18·23** 이 같은 문법을 건드린다.
  좁힌 방법: 기존 노트가 **「이렇게 쓴다」**(메서드 호출 예시)까지라면, 이 목록은 **「무엇을 못 하고 어디서 틀리나」**로만 간다 — 슬라이스 대입과 길이 변화(#9), 정렬 `key` 와 안정성(#10), 언패킹 규칙과 불변 tuple 안의 가변 원소(#11), 키 해시 요건과 뷰(#12), 컴프리헨션과 제너레이터 표현식의 평가 시점 차이(#14), 순회 중 변경(#18), 음수 바닥 나눗셈(#4), `and`/`or` 의 반환값(#5).
- **`cs/foundations/variables-and-memory/`·`memory-management/`·`oop-basics/`·`process-thread/`·`data-representation/`** — 같은 교재 계열의 CS 일반론이다. #1·#29·#34·#50·#53 은 그 일반론을 **Python 언어 규칙으로** 좁혀 받는다(참조 모델, 속성 탐색 순서, MRO, `Decimal`, GIL).
- **`cs/data-structure/`** — 자료구조의 원리·복잡도는 그쪽이 정본이다. #43 은 원리가 아니라 **표준 라이브러리 구현을 고르는 기준**만 다룬다.
- **`cs/algorithm/25-string-matching/`** — 문자열 매칭 알고리즘은 그쪽. #46 은 `re` 모듈 API 와 백트래킹 비용만 다룬다.
- **`history/python/`** 7편 — 「언제 들어왔나」는 전부 그쪽이다. 이 목록은 버전을 **제약 조건으로만** 적는다(아래 「버전 기준」).

## 뺀 것과 이유

- **패키징·가상환경·`pip`·`pyproject.toml`** — 언어 문법·표준 API 가 아니고 `history/python/04-패키징-생태계.md` 가 이미 다룬다.
- **서드파티(numpy·pandas·requests·Django 등)** — 표준 라이브러리 밖이다.
- **테스트 프레임워크(`unittest`·`pytest`)·`logging`·`argparse`** — 애플리케이션 골격에 가깝다. 2단계 확정 후 별도 갈래로 제안한다.
- **CPython 내부(바이트코드·참조 카운팅·C 확장·`ctypes`)** — 언어 사용법이 아니라 구현이다. `cs/foundations/compiler-pipeline/`·`memory-management/` 쪽.
- **`socket`·`subprocess`·`os` 저수준** — OS 경계 주제로 `cs/systems/` 축에 가깝다.
- **버전별 릴리스 노트 나열** — `history/python/` 의 몫.

## 버전 기준

**Python 3.12 기준**(이 머신 3.12.3 으로 실행 검증). 3.10~3.13 사이에서 갈리는 것은 행마다 표기했고, 모아 두면 이렇다.

| 버전 | 이 목록에서 해당하는 것 |
|---|---|
| 3.7 | dict 삽입 순서 보장이 언어 보증으로 승격 (#12) |
| 3.9 | dict 병합 연산자, `zoneinfo` (#12, #49) |
| 3.10 | `match` 문(PEP 634), `X \| Y` 유니온(PEP 604), 괄호 다중 `with` (#39, #41, #28) |
| 3.11 | `ExceptionGroup`·`except*`(PEP 654), `asyncio.TaskGroup`, `StrEnum` (#27, #52, #37) |
| 3.12 | PEP 695 타입 매개변수 문법, PEP 701 f-string 형식화 (#41, #8) |
| 3.13 | 타입 매개변수 기본값(PEP 696), `TypeIs`(PEP 742), `ReadOnly`(PEP 705), free-threaded 실험 빌드(PEP 703) (#41, #53) — **이 머신에서 실행 검증 불가** |
