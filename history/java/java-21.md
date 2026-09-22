# Java 21 (2023년 9월, LTS)

> 원본: `~/project/java-history/java/java-21.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/메서드 이름·자바 코드블록 9개·「릴리스 정보」와 「참고 출처」 목록은 원문 그대로다.\
> ASCII 도식 2개는 원문 mermaid 도식 2개를 글자로 옮긴 것이고, 새로 그린 도식은 없다.\
> 「한눈에」의 창구 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 「미리보기에서 정식까지」 표의 「미리보기였던 편」 칸은 같은 시리즈의 다른 편(`java-17.md`~`java-20.md`)에서 끌어온 보충이고, 출처 편을 칸마다 적었다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> Java 17 이후 첫 LTS. **가상 스레드(JEP 444)·레코드 패턴(JEP 440)·switch 패턴 매칭(JEP 441)이 모두 정식화**되어, 현대 Java의 동시성과 데이터 중심 프로그래밍 패러다임을 확정한 분기점이 된 릴리스. 총 15개 JEP를 담았다.

이 편을 하나의 비유로 읽으면 **창구 직원이, 서류가 오기를 기다리는 민원 건을 붙들고 있지 않고 서랍에 넣어 둔 뒤 다음 손님을 부르게 된 일**이다.\
창구 수는 그대로인데 접수해 둘 수 있는 민원 건수가 수십만으로 늘어난다.\
**가상 스레드도 똑같은 구조다** — 원문 자신이 「가상 스레드」 절에서 그 동작을 이렇게 적는다: "가상 스레드가 블로킹 작업(I/O, `sleep`, 락 대기 등)에 진입하면 JVM이 그 스레드를 캐리어에서 **언마운트**하고, 캐리어는 다른 가상 스레드를 실행한다. 블로킹이 끝나면 다시 마운트되어 이어서 실행된다."

본문 흐름에 쓰는 비유는 이 창구 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 창구(그 앞에 앉은 직원) | 캐리어 스레드 — 원문 표현으로 "플랫폼(OS) 스레드(**캐리어 스레드**)" |
| 처리 중인 민원 한 건 | 가상 스레드 — 원문 표현으로 "JVM이 관리하는 경량 스레드" |
| 서류가 오기를 기다리는 시간 | 원문이 든 블로킹 작업 셋, 즉 "I/O, `sleep`, 락 대기 등" |
| 기다리는 건을 서랍에 넣어 둔다 | 언마운트 — 원문 도식 라벨로 "힙에 스택 보관 (대기)" |
| 서류가 오면 빈 창구에 다시 올려 이어서 처리 | 재마운트 — 원문 표현으로 "블로킹이 끝나면 다시 마운트되어 이어서 실행된다" |
| 손님이 창구를 붙들고 놓지 않는 경우 | 고정(pinning) — 원문 표현으로 "가상 스레드가 캐리어에 **고정**(pinning)되어" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **가상 스레드가 "항상 더 빠른 스레드"인 것이 아니다.**\
  원문이 「주의할 점 (실무)」에서 못 박은 그대로다 — "CPU 바운드 작업에는 이점이 적다. 가상 스레드의 강점은 **블로킹 I/O가 많은 워크로드**에서 나온다."
- **블로킹이 사라지는 것이 아니다.** 블로킹은 그대로 하되 그동안 창구를 놓아주는 것이다.\
  원문 표현으로 "블로킹 I/O를 마음껏 호출 — OS 스레드를 점유하지 않는다"이고, 놓아주지 못하는 예외가 바로 위 표의 고정(pinning)이다.
- **가상 스레드는 풀에 넣어 두고 돌려쓰는 것이 아니다.**\
  원문이 같은 절에 적은 그대로다 — "가상 스레드는 **풀링하지 않는다**. "필요할 때마다 새로 생성"이 올바른 사용법이다."

### 미리보기에서 정식까지 — 이 편이 거둔 것

이 편에서 "정식"이 된 기능은 대부분 앞선 편에서 몇 차례 미리보기를 거친 것들이다. 아래 표의 왼쪽 두 칸은 이 편 원문이 적은 것이고, 오른쪽 칸은 그 편들의 원문에서 확인한 보충이다.

| 기능 | 이 편(21)에서의 상태 | 미리보기였던 편 |
|---|---|---|
| 가상 스레드 (JEP 444) | 원문 표현으로 "두 차례 프리뷰를 거쳐 **정식 기능**이 되었다" | `java-19.md` 1차 프리뷰(JEP 425) · `java-20.md` 2차 프리뷰(JEP 436) |
| 레코드 패턴 (JEP 440) | 원문 표현으로 "프리뷰를 거쳐 **정식**이 되었다" | `java-19.md` 1차 프리뷰(JEP 405) · `java-20.md` 2차 프리뷰(JEP 432) |
| switch를 위한 패턴 매칭 (JEP 441) | 원문 표현으로 "**네 차례의 프리뷰**를 거쳐 마침내 정식이 되었다" | `java-17.md` 프리뷰(JEP 406) · `java-18.md` 2차 프리뷰(JEP 420) · `java-19.md` 3차 프리뷰(JEP 427) · `java-20.md` 4차 프리뷰(JEP 433) |
| Foreign Function & Memory API (JEP 442) | **정식이 아니다** — 원문 표현으로 "세 번째 프리뷰" | `java-19.md` 1차 프리뷰(JEP 424) · `java-20.md` 2차 프리뷰(JEP 434). 정식화는 원문이 적은 대로 Java 22(JEP 454) |
| Scoped Values (JEP 446) | **정식이 아니다** — 원문 표현으로 "인큐베이터에서 **프리뷰**로 승격" | `java-20.md` 1차 인큐베이터(JEP 429) |
| 구조적 동시성 (JEP 453) | **정식이 아니다** — 원문 표현으로 "인큐베이터를 거쳐 **프리뷰**로 승격" | `java-19.md` 1차 인큐베이터(JEP 428) · `java-20.md` 2차 인큐베이터(JEP 437) |
| 문자열 템플릿 (JEP 430) | **정식이 아니다** — 이 편이 1차 프리뷰이고, 원문 주에 따르면 이후 **철회**되었다 | 없음(이 편이 처음) |

## 릴리스 정보
- 정식 출시일: 2023년 9월 19일
- LTS 여부: **예 (Long-Term Support)** — Java 17(2021), Java 25(2025)와 함께 장기 지원 라인
- 포함 JEP 수: **15개** (정식/일반 8개, 프리뷰 6개, 인큐베이터 1개)

> **LTS(Long-Term Support, 장기 지원)** — 6개월마다 나오는 릴리스 가운데 몇 개를 골라 오래 보안 패치를 제공하는 버전. 기업이 운영에 올려 두고 몇 년을 버틸 수 있는 자리다.\
> 예: 원문이 이 자리에서 21과 같은 라인으로 든 것이 Java 17(2021)과 Java 25(2025)다.

> **프리뷰(preview) / 인큐베이터(incubator)** — 정식으로 굳히기 전에 미리 내보내 피드백을 받는 단계. 같은 시리즈 `README.md`가 적는 구분은 "preview는 언어/API 기능, incubator는 모듈 단위 API"다.\
> 예: 이 편 원문이 프리뷰 기능에 붙인 자바 코드블록 다섯 개에는 모두 `--enable-preview 필요`라는 주석이 달려 있고, 정식이 된 가상 스레드의 코드블록에는 반대로 `정식 기능 — --enable-preview 불필요`가 적혀 있다.

## 시대적 배경

Java 21은 2021년 9월 Java 17 이후 **2년 만의 LTS**다. 그 2년간 18·19·20을 거치며 프리뷰·인큐베이터로 검증된 기능들이 한꺼번에 정식으로 쏟아져 나오면서, "여러 해에 걸친 빅 프로젝트(Loom·Amber·Panama)의 수확기"가 되었다.

가장 큰 사건은 **Project Loom의 가상 스레드 정식화**다.\
십수 년간 진행되어 온 경량 동시성 작업이 마침내 운영 환경에서 쓸 수 있는 정식 기능이 되었고, 이는 그동안 고동시성을 위해 리액티브 프로그래밍에 의존하던 Java 생태계의 흐름을 되돌렸다.\
Spring Boot 3.2가 곧바로 가상 스레드를 지원하는 등 프레임워크 채택이 빠르게 이어졌다.

> **Project Loom / Amber / Panama** — 원문이 "여러 해에 걸친 빅 프로젝트"로 묶어 부르는 세 갈래의 이름. 이 편 원문은 셋을 괄호에 묶어 이름만 들고, 그 가운데 Loom·Amber가 내놓은 것만 짝지어 적는다.\
> 예: Loom은 가상 스레드(정식화)를, Amber는 "패턴 매칭(레코드 패턴 + switch 패턴 매칭)"을 내놓았다. Panama와 Foreign Function & Memory API(이 편에서는 3차 프리뷰)의 짝은 이 편이 아니라 같은 시리즈 `java-22.md`가 짝짓는다.

> **리액티브 프로그래밍** — 원문이 가상 스레드 이전의 대안으로 드는 쪽. 원문 표현으로 "비동기·논블로킹(리액티브) 코드"이고, 원문이 그 비용으로 든 것이 "코드 복잡도·디버깅 난이도·스택트레이스 단절"이다.\
> 예: 원문은 가상 스레드를 "리액티브 수준의 확장성"을 같은 값으로 주는 쪽으로 적는다 — 빠르기가 아니라 확장성의 비교다.

동시에 Project Amber의 **패턴 매칭**(레코드 패턴 + switch 패턴 매칭)이 정식화되고, 여기에 이미 Java 17(JEP 409)에서 정식화돼 있던 sealed 타입이 결합되면서, Java는 함수형·데이터 지향 스타일을 일급으로 표현할 수 있게 되었다. **Sequenced Collections**라는 오래 기다려 온 컬렉션 API 보강도 정식 포함됐다.

대부분의 기업이 LTS만 운영에 올린다는 점에서, Java 21은 "실무 Java의 다음 기준선"이 된 릴리스다.

> **sealed 타입** — 상속·구현할 수 있는 대상을 만든 쪽이 목록으로 닫아 두는 타입. 원문은 이것이 이 편에서 새로 생긴 것이 아니라 "이미 Java 17(JEP 409)에서 정식화돼 있던" 것이라고 적는다.\
> 예: 이 편 원문의 코드에 나오는 `sealed interface Shape permits Circle, Rectangle {}`가 그것이고, 닫혀 있기 때문에 원문 주석대로 "sealed → 컴파일러가 전체성 보장, default 불필요"가 성립한다.

---

## 주요 추가 기능 (정식)

### 가상 스레드 (JEP 444, Final/정식) ⭐⭐⭐
Java 19(JEP 425)·20(JEP 436)의 두 차례 프리뷰를 거쳐 **정식 기능**이 되었다. Java 21을 정의하는 단 하나의 기능을 꼽으라면 단연 이것이다.

**무엇인가**
- 가상 스레드는 **JVM이 관리하는 경량 스레드**다. OS 스레드와 1:1로 묶이지 않고, 다수의 가상 스레드가 소수의 플랫폼(OS) 스레드(**캐리어 스레드**) 위에서 M:N으로 다중화된다.
- 가상 스레드가 블로킹 작업(I/O, `sleep`, 락 대기 등)에 진입하면 JVM이 그 스레드를 캐리어에서 **언마운트**하고, 캐리어는 다른 가상 스레드를 실행한다. 블로킹이 끝나면 다시 마운트되어 이어서 실행된다.
- 결과적으로 **수십만~수백만 개의 가상 스레드**를 생성해도 OS 스레드는 적게 유지된다. 생성·전환 비용이 매우 저렴하다.

> **캐리어 스레드(carrier thread)** — 가상 스레드를 실제로 얹어 돌리는 진짜 OS 스레드. 원문 표현으로 "플랫폼(OS) 스레드"이고, 비유의 창구에 해당한다.\
> 예: 원문 도식이 캐리어를 담은 칸에 붙인 이름이 "소수 캐리어 스레드 (ForkJoinPool, OS 스레드)"이고, 그 안에 `Carrier-1`·`Carrier-2` 둘만 그려져 있다.

> **M:N 다중화** — 많은 쪽(M)이 적은 쪽(N) 위에서 갈아 끼워지며 돌아가는 방식. 원문은 이 쪽을 "OS 스레드와 1:1로 묶이지 않고"라고 적는다.\
> 예: 원문이 두 모델을 나란히 적은 그대로다 — 플랫폼 스레드는 "OS 스레드와 1:1로 묶이지만", 가상 스레드는 "캐리어 스레드 위에서 M:N으로 다중화된다".

> **마운트 / 언마운트(mount / unmount)** — 가상 스레드를 캐리어 위에 올리는 것 / 캐리어에서 내려놓는 것. 내려놓을 때 하던 일이 사라지는 것이 아니라 보관되었다가 이어진다.\
> 예: 원문 도식이 내려놓은 자리에 붙인 라벨이 "힙에 스택 보관 (대기)"이고, 돌아오는 화살표에 붙인 라벨이 "I/O 완료 → 다른 캐리어에 재mount"다 — 같은 캐리어로 돌아온다고 적지 않는다.

**왜 중요한가**
- 그동안 높은 처리량을 위해서는 스레드 풀을 아껴 쓰고 비동기·논블로킹(리액티브) 코드를 작성해야 했다. 이는 코드 복잡도·디버깅 난이도·스택트레이스 단절이라는 큰 비용을 동반했다.
- 가상 스레드는 "**요청 하나당 스레드 하나(thread-per-request)**"라는 단순하고 직관적인 모델을 유지하면서도 리액티브 수준의 확장성을 제공한다. 즉, **동기·블로킹 스타일의 읽기 쉬운 코드로 고동시성**을 달성한다.

> **thread-per-request(요청 하나당 스레드 하나)** — 들어온 요청 하나마다 스레드 하나를 붙여 처음부터 끝까지 순서대로 처리하는 모델. 원문이 이 모델에 붙인 말이 "단순하고 직관적인"이고, 그동안 높은 처리량에는 "스레드 풀을 아껴 쓰고 비동기·논블로킹(리액티브) 코드"가 필요했다고 적는다.\
> 예: 원문이 이 모델의 실물로 보여 주는 것이 아래 코드의 `Executors.newVirtualThreadPerTaskExecutor()`이고, 거기에 `IntStream.range(0, 1_000_000)`만큼의 작업을 밀어 넣는다.

**20 대비 정식화에서의 변경**
- 2차 프리뷰(JEP 436)와 비교한 가장 큰 변화는 가상 스레드가 **`ThreadLocal`을 완전히 지원**하게 된 것이다(thread-local 사용을 opt-out 하는 옵션 제거). 호환성을 위해 thread-local을 신뢰성 있게 동작시키는 방향으로 정리되었다.

같은 시리즈 `java-20.md`도 이 변경이 20이 아니라 여기서 이뤄졌다고 못 박는다 — "가상 스레드가 `ThreadLocal`을 항상 지원하도록 한 변경은 20이 아니라 21 정식화에서 이루어진다."

> **`ThreadLocal`** — 스레드마다 따로 한 칸씩 갖는 저장소. 같은 코드가 여러 스레드에서 돌아도 각자 자기 칸만 본다.\
> 예: 원문이 이 절에서 적은 변화가 "thread-local 사용을 opt-out 하는 옵션 제거"다 — 즉 20까지는 끌 수 있는 선택지가 있었고, 21에서는 그 선택지를 없앴다.

**사용 예시**
```java
// 정식 기능 — --enable-preview 불필요

// 1) 단일 가상 스레드
Thread.startVirtualThread(() ->
        System.out.println("Running in " + Thread.currentThread()));

// 2) 빌더 API
Thread vt = Thread.ofVirtual()
        .name("worker-", 0)
        .start(() -> doWork());
vt.join();

// 3) 요청당 스레드 — 가상 스레드 ExecutorService
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 1_000_000).forEach(i ->
        executor.submit(() -> {
            // 블로킹 I/O를 마음껏 호출 — OS 스레드를 점유하지 않는다
            Thread.sleep(Duration.ofSeconds(1));
            return fetchFromDatabase(i);
        }));
} // close()가 모든 작업 완료까지 대기
```

원문 코드는 `// 1)`·`// 2)`·`// 3)`으로 세 토막을 나누고 각 토막에 이름을 붙여 두었다 — "단일 가상 스레드"가 `Thread.startVirtualThread(...)`, "빌더 API"가 `Thread.ofVirtual()`, "요청당 스레드 — 가상 스레드 ExecutorService"가 `Executors.newVirtualThreadPerTaskExecutor()`다.\
원문이 세 번째 블록의 마지막 줄 주석에 적어 둔 것이 그 정리를 마치는 방법이다 — "close()가 모든 작업 완료까지 대기".

**주의할 점 (실무)**
- 가상 스레드는 **풀링하지 않는다**. "필요할 때마다 새로 생성"이 올바른 사용법이다.
- `synchronized` 블록 안에서 블로킹하면 가상 스레드가 캐리어에 **고정**(pinning)되어 확장성이 떨어질 수 있다(이 한계는 이후 JDK 24의 JEP 491에서 해소된다). 21에서는 `ReentrantLock` 사용이 권장됐다.
- CPU 바운드 작업에는 이점이 적다. 가상 스레드의 강점은 **블로킹 I/O가 많은 워크로드**에서 나온다.

> **고정(pinning)** — 가상 스레드가 캐리어에서 내려오지 못한 채 붙어 있는 상태. 내려오지 못하니 그 캐리어는 다른 가상 스레드를 받을 수 없다.\
> 예: 원문이 이 절에서 조건으로 든 것이 `synchronized` 블록 안에서의 블로킹이고, 도식 쪽에서 든 것은 "synchronized / native 안 블로킹"이다.

> **CPU 바운드 / 블로킹 I/O** — 계산하느라 바쁜 일 / 바깥에서 답이 오기를 기다리는 일. 기다리는 쪽만 창구를 비워 줄 수 있다.\
> 예: 원문은 앞쪽을 "이점이 적다"로, 뒤쪽을 강점이 나오는 자리로 갈라 적는다.

아래 흐름도는 가상 스레드의 mount/unmount 동작을 보여준다. 다수의 가상 스레드가 소수의 캐리어(플랫폼) 스레드 위에서 실행되다가, 블로킹 작업을 만나면 캐리어를 반납(unmount)하고 다른 가상 스레드가 그 캐리어에 mount된다. 덕분에 적은 OS 스레드로 수백만 개의 가상 스레드를 다룰 수 있다. 단, `synchronized` 블록·네이티브 호출 안에서 블로킹하면 가상 스레드가 캐리어에 고정(pinning)되어 반납되지 않을 수 있다.

```text
[수십만~수백만 가상 스레드]                 VT-1 · VT-2 · VT-3 · VT-n ...
[소수 캐리어 스레드 (ForkJoinPool, OS 스레드)]  Carrier-1 · Carrier-2

VT-1                             -->  Carrier-1                   mount (실행)
VT-2                             -->  Carrier-2                   mount (실행)
VT-1                             ..>  힙에 스택 보관 (대기)        블로킹 I/O 만남 → unmount (캐리어 반납)
VT-3                             -->  Carrier-1                   비어 있는 캐리어에 mount
힙에 스택 보관 (대기)              ..>  Carrier-2                   I/O 완료 → 다른 캐리어에 재mount
synchronized / native 안 블로킹    ..>  Carrier-1                   pinning: 캐리어 점유 유지
```

- 이 그림은 원문의 mermaid 흐름도를 글자로 옮긴 것이다 — 화살표 여섯으로 원문의 화살표 수와 같고, 방향과 순서도 원문과 같다.
- 각 줄 오른쪽에 적은 말은 원문이 그 화살표에 붙인 라벨 글자 그대로이고, 대괄호 두 줄과 칸 이름(`VT-1`·`Carrier-1` 등)도 원문의 것이다.
- `-->`는 원문의 실선 화살표, `..>`는 원문의 점선 화살표다. 점선 셋이 각각 캐리어를 놓는 일·돌아오는 일·놓지 못하는 일이다.

플랫폼 스레드 모델과 가상 스레드 모델의 매핑 차이는 다음과 같다. 플랫폼 스레드는 OS 스레드와 1:1로 묶이지만, 가상 스레드는 캐리어 스레드 위에서 M:N으로 다중화된다.

```text
  플랫폼 스레드 모델 (1:1)               가상 스레드 모델 (M:N)
  ───────────────────────               ──────────────────────
  Platform Thread --- OS Thread         Virtual Thread ─┐
  Platform Thread --- OS Thread         Virtual Thread ─┼──>  Carrier (OS Thread)
                                        Virtual Thread ─┘
```

- 왼쪽 두 줄의 `---`는 원문의 무방향 선이고, 오른쪽 셋의 화살표는 원문의 `-->`다. 칸 이름은 전부 원문의 것이다.
- 오른쪽에서 화살표 셋이 **같은 칸 하나**로 모이는 것이 원문 그대로다 — 원문도 세 `Virtual Thread`를 `Carrier (OS Thread)` 한 칸에 잇는다. 그것이 "M:N"의 M과 N이다.
- 두 칸은 원문이 나란히 둔 두 모델이고, 가로로 같은 줄에 놓인 것끼리는 짝이 아니다 — 원문은 두 모델 사이에 아무 선도 긋지 않는다.

### 레코드 패턴 (JEP 440, Final/정식) ⭐
Java 19(JEP 405)·20(JEP 432)의 프리뷰를 거쳐 **정식**이 되었다.
- 패턴 매칭에서 **레코드를 분해**(deconstruct)하여 컴포넌트를 곧바로 바인딩한다. `instanceof`와 `switch` 모두에서 사용 가능하다.
- **중첩**이 가능해, 깊은 객체 구조를 한 줄로 풀어낸다. sealed 타입과 결합하면 컴파일러가 전체성을 검증한다.

> **분해(deconstruct) / 바인딩** — 통째로 받은 객체를 그 안의 칸들로 쪼개어, 각 칸에 이름을 붙여 바로 쓰게 하는 것.\
> 예: 아래 코드의 `obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))`가 `Line` 하나를 `x1`·`y1`·`x2`·`y2` 네 이름으로 쪼갠다.

> **중첩(nested) 패턴** — 쪼갠 칸 안에 또 패턴을 적어 더 깊이 들어가는 것. 원문 표현으로 "깊은 객체 구조를 한 줄로 풀어낸다".\
> 예: 위 패턴에서 바깥이 `Line(...)`이고 그 안에 다시 `Point(var x1, var y1)`이 들어 있는 두 겹이 그것이다.

> **전체성(exhaustiveness)** — 있을 수 있는 경우를 빠짐없이 다뤘는지 컴파일러가 확인해 주는 성질.\
> 예: 아래 `area` 코드에서 `Shape`가 `permits Circle, Rectangle`로 닫혀 있어, 원문 주석대로 "sealed → 컴파일러가 전체성 보장, default 불필요"가 된다.

```java
record Point(int x, int y) {}
record Line(Point from, Point to) {}

// instanceof + 중첩 레코드 패턴
static void print(Object obj) {
    if (obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))) {
        System.out.printf("(%d,%d) -> (%d,%d)%n", x1, y1, x2, y2);
    }
}

// switch + 레코드 패턴
sealed interface Shape permits Circle, Rectangle {}
record Circle(double r) implements Shape {}
record Rectangle(double w, double h) implements Shape {}

static double area(Shape s) {
    return switch (s) {
        case Circle(double r)              -> Math.PI * r * r;
        case Rectangle(double w, double h) -> w * h;
    }; // sealed → 컴파일러가 전체성 보장, default 불필요
}
```

### switch를 위한 패턴 매칭 (JEP 441, Final/정식) ⭐
Java 17부터 18·19·20까지 **네 차례의 프리뷰**를 거쳐 마침내 정식이 되었다.
- `switch`의 `case` 라벨에 **타입 패턴**을 쓸 수 있고, `when` 절로 **가드 조건**을 붙일 수 있다.
- `null`을 `case null`로 명시적으로 다룰 수 있다.
- 패턴 switch는 **모든 입력값을 빠짐없이 처리**(전체성)해야 한다. sealed 타입·enum과 결합하면 컴파일 타임에 누락이 잡힌다.

네 차례가 어느 편이었는지는 같은 시리즈에서 확인된다 — `java-17.md`의 JEP 406(프리뷰), `java-18.md`의 JEP 420(2차), `java-19.md`의 JEP 427(3차), `java-20.md`의 JEP 433(4차)이다.\
아래 코드가 쓰는 `when` 가드도 처음부터 있던 문법은 아니다 — `java-19.md`는 3차 프리뷰의 "가장 눈에 띄는 변화"로 "가드 조건을 `&&`가 아니라 **`when` 키워드**로 표현하게 바뀐 점"을 들고, `java-17.md`는 "17 시대(JEP 406)의 가드 문법은 `when`이 아니라 `&&`였다"고 적는다.

> **타입 패턴** — 값이 어떤 타입인지 가려내는 일과 그 타입의 이름으로 값을 받는 일을 `case` 한 줄에서 함께 하는 것. 원문 표현으로 "`switch`의 `case` 라벨에 **타입 패턴**을 쓸 수 있고"이다.\
> 예: 아래 `case Integer i`가 그것이고, 뒤이어 `"정수 " + i`처럼 `i`를 바로 쓴다.

> **가드 조건(`when` 절)** — 타입이 맞아도 한 가지 조건을 더 걸어 그때만 그 갈래로 가게 하는 것.\
> 예: 아래 `case Bird b when b.canFly()`가 원문 주석의 "짹짹 (날 수 있음)" 쪽으로 가고, 그렇지 않은 새는 바로 아래 `case Bird b`가 받아 "짹짹 (못 남)"으로 간다.

```java
sealed interface Animal permits Dog, Cat, Bird {}
record Dog(String name) implements Animal {}
record Cat(String name) implements Animal {}
record Bird(boolean canFly) implements Animal {}

static String sound(Animal a) {
    return switch (a) {
        case Dog d            -> d.name() + ": 멍멍";
        case Cat c            -> c.name() + ": 야옹";
        case Bird b when b.canFly() -> "짹짹 (날 수 있음)";
        case Bird b           -> "짹짹 (못 남)";
    }; // sealed → default 불필요
}

// null 통합 처리 + 타입 패턴
static String describe(Object obj) {
    return switch (obj) {
        case null       -> "널 값";
        case Integer i  -> "정수 " + i;
        case String s   -> "문자열 " + s;
        default         -> "기타 " + obj;
    };
}
```

위 두 코드블록이 원문이 든 세 가지를 하나씩 보여 준다 — 첫 블록의 `case Dog d`가 타입 패턴, `when b.canFly()`가 가드 조건이고, 둘째 블록의 `case null`이 널 처리다.\
전체성은 두 블록에서 다르게 채워진다 — 첫 블록은 `sealed`라 원문 주석대로 "default 불필요"이고, 둘째 블록은 대상이 `Object`라 `default`가 붙어 있다.

### Sequenced Collections (JEP 431, Final/정식) ⭐
- **순서가 있는 컬렉션을 위한 통일된 인터페이스**를 새로 도입했다. 그동안 "첫/마지막 원소 접근"이나 "역순 순회"가 컬렉션 종류마다 제각각(예: `List.get(0)` vs `Deque.getFirst()` vs `LinkedHashSet`은 방법 없음)이었던 문제를 해결한다.
- 새 인터페이스: `SequencedCollection`, `SequencedSet`, `SequencedMap`.
- 공통 메서드: `getFirst()`, `getLast()`, `addFirst()`, `addLast()`, `removeFirst()`, `removeLast()`, 그리고 **역순 뷰** `reversed()`.

> **`SequencedCollection` / `SequencedSet` / `SequencedMap`** — 원문이 "새 인터페이스"로 든 셋. 원문 표현으로 "순서가 있는 컬렉션을 위한 통일된 인터페이스"다.\
> 예: 원문이 통일 이전의 제각각인 상태로 든 셋이 `List.get(0)`·`Deque.getFirst()`·"`LinkedHashSet`은 방법 없음"이고, 아래 코드에서 그 셋 중 마지막이 `set.getFirst()`로 해결된다.

```java
List<Integer> list = new ArrayList<>(List.of(1, 2, 3));
list.getFirst();   // 1  (기존 list.get(0))
list.getLast();    // 3  (기존 list.get(list.size()-1))
list.addFirst(0);  // [0, 1, 2, 3]
list.reversed();   // [3, 2, 1, 0] (뷰)

LinkedHashSet<String> set = new LinkedHashSet<>(List.of("a", "b", "c"));
set.getFirst();    // "a"  — 이전엔 깔끔한 방법이 없었다
set.getLast();     // "c"

SequencedMap<String,Integer> map = new LinkedHashMap<>();
map.putFirst("x", 1);
map.putLast("y", 2);
map.firstEntry();  // x=1
```

### Generational ZGC (JEP 439, Final/정식)
- 저지연 가비지 컬렉터 **ZGC에 세대(generational) 모드**를 추가했다. 객체를 젊은 세대와 오래된 세대로 나눠 관리한다.
- "대부분의 객체는 금방 죽는다"는 약한 세대 가설을 활용해, 젊은 세대를 더 자주·저렴하게 수집한다. 결과적으로 **할당 stall 감소, 더 적은 힙 여유로 동일 성능, CPU 오버헤드 감소**.
- 21에서는 `-XX:+UseZGC -XX:+ZGenerational`로 활성화(비세대 ZGC가 기본). 이후 세대 ZGC가 기본이 되고 비세대 모드는 폐기 수순을 밟는다.

원문이 말하는 그 "이후"가 어느 편인지는 같은 시리즈에서 확인된다 — `java-23.md`의 JEP 474가 세대별 모드를 기본으로 바꾸고, `java-24.md`의 JEP 490이 비-세대 모드를 제거한다.

> **약한 세대 가설** — 원문 표현으로 "대부분의 객체는 금방 죽는다"는 관찰. 이 가설이 맞으면 갓 만들어진 것들만 자주 훑어도 대부분이 치워진다.\
> 예: 원문이 그 활용으로 적는 것이 "젊은 세대를 더 자주·저렴하게 수집한다"이다.

> **할당 stall** — 새 객체를 만들려는데 자리가 나기를 기다리느라 애플리케이션이 멈칫하는 것.\
> 예: 원문이 세대 모드의 결과로 든 셋 가운데 첫째가 "할당 stall 감소"다.

### Key Encapsulation Mechanism API (JEP 452, Final/정식)
- **키 캡슐화 메커니즘**(KEM)을 위한 표준 API(`javax.crypto.KEM`)를 도입했다. KEM은 공개키 암호로 대칭키를 안전하게 전달하는 현대적 기법이다.
- **포스트 양자 암호(PQC)** 알고리즘 다수가 KEM 형태라는 점에서, 양자 내성 암호 시대를 대비한 기반 작업이다.

> **KEM(키 캡슐화 메커니즘)** — 원문 표현으로 "공개키 암호로 대칭키를 안전하게 전달하는 현대적 기법". 이 편이 도입한 것은 그 기법 자체가 아니라 그것을 위한 표준 API(`javax.crypto.KEM`)다.\
> 예: 원문이 이 API를 기반 작업으로 부르는 근거가 "포스트 양자 암호(PQC) 알고리즘 다수가 KEM 형태"라는 점이다.

---

## 미리보기·인큐베이터 기능

*(여기 놓인 것은 이 편에서 정식이 아니다 — 아래 일곱 항목 전부가 제목에 프리뷰 또는 인큐베이터 차수를 달고 있다.)*

### 문자열 템플릿 (JEP 430, Preview/1차 프리뷰)
- 문자열에 표현식을 끼워 넣는 보간 메커니즘. 기본 제공 `STR`·`FMT` 프로세서는 표준 보간을 수행할 뿐 그 자체로 모든 인젝션을 자동 방지하지는 않으며, **도메인별 템플릿 프로세서를 직접 구현해 입력을 검증·이스케이프**하도록 만들 수 있다는 점이 보안상의 핵심이다. `STR`, `FMT`, `RAW` 등의 템플릿 프로세서를 제공한다.
- 백틱이 아니라 `\{...}` 구문을 쓴다.

> **보간(interpolation)** — 문자열 안에 값이 들어갈 자리를 뚫어 두고 실행할 때 그 자리를 채우는 것.\
> 예: 아래 코드의 `STR."Hello \{name} \{version}!"`에서 `\{name}`·`\{version}` 두 자리가 채워져 원문 주석대로 `"Hello Java 21!"`가 된다.

```java
// --enable-preview 필요
String name = "Java";
int version = 21;
String msg = STR."Hello \{name} \{version}!"; // "Hello Java 21!"
```
> 주의: 문자열 템플릿은 이후 설계 재검토로 **22에서 2차 프리뷰**를 거친 뒤 제거(철회)되었다. Java 21 시점에는 프리뷰였다.

원문의 이 주는 같은 시리즈에서 그대로 확인된다 — `java-22.md`가 JEP 459를 2차 프리뷰로 적고, `java-23.md`는 "23에서는 프리뷰에서조차 제거되었다 — 5년 만에 처음으로 정식화에 이르지 못한 프리뷰 기능이 되었다"고 적는다.\
그러니 이 기능은 **정식이 된 적이 없다.** 연도만 보고 "21에서 나온 기능"으로 외우면 틀린다.

### 미명명 패턴과 변수 (JEP 443, Preview/1차 프리뷰)
- 쓰지 않는 패턴 컴포넌트나 변수를 **`_`**(언더스코어)로 표기한다. 의도적으로 무시함을 명확히 한다.

```java
// --enable-preview 필요
if (obj instanceof Point(int x, _)) { /* y는 무시 */ }

try { ... } catch (Exception _) { log("실패"); } // 예외 변수 미사용 명시

for (var _ : items) count++;
```

이 기능은 다음 편에서 정식이 된다 — `java-22.md`가 JEP 456을 "Unnamed Variables & Patterns (정식)"으로 적는다.

### 미명명 클래스와 인스턴스 main 메서드 (JEP 445, Preview/1차 프리뷰)
- 입문자를 위해 **보일러플레이트 없는** `main`을 허용한다. `public static void`나 `String[] args`, 클래스 선언 없이도 프로그램을 작성할 수 있다.

```java
// --enable-preview 필요 — 파일 전체가 이게 전부일 수 있다
void main() {
    System.out.println("Hello, World!");
}
```

> **보일러플레이트(boilerplate)** — 뜻은 없는데 형식상 꼭 적어야 하는 상투적인 코드.\
> 예: 원문이 이 자리에서 없앨 수 있다고 든 것이 `public static void`, `String[] args`, 그리고 클래스 선언 셋이다.

이 기능은 이 편 이후로도 이름이 계속 바뀌며 프리뷰를 이어간다 — `java-22.md`는 "Implicitly Declared Classes and Instance Main Methods"(JEP 463, 2차 프리뷰), `java-25.md`는 "Compact Source Files and Instance Main Methods"(JEP 512, 정식)로 적는다. 즉 **정식화는 Java 25다.**

### Scoped Values (JEP 446, Preview/1차 프리뷰)
- Java 20(JEP 429) 인큐베이터에서 **프리뷰**로 승격. 가상 스레드 및 자식 스레드로 불변 데이터를 안전·경량으로 공유한다. `ThreadLocal`의 대안.

```java
// --enable-preview 필요
final static ScopedValue<User> USER = ScopedValue.newInstance();

ScopedValue.where(USER, currentUser).run(() -> handle()); // 이 범위에서만 USER.get() 유효
```

정식화는 이 편이 아니다 — `java-25.md`가 JEP 506을 정식으로 적는다.

### 구조적 동시성 (JEP 453, Preview/1차 프리뷰)
- Java 19·20의 인큐베이터를 거쳐 **프리뷰**로 승격(패키지가 `java.util.concurrent`로 이동). 가상 스레드와 결합해 다중 작업을 하나의 단위로 다룬다.

```java
// --enable-preview 필요
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var user  = scope.fork(() -> findUser(id));
    var order = scope.fork(() -> fetchOrder(id));
    scope.join().throwIfFailed();          // 모두 대기 + 실패 시 전파
    return new Response(user.get(), order.get());
}
```

> **구조적 동시성** — 원문 표현으로 "다중 작업을 하나의 단위로 다"루는 것. 여럿을 띄웠으면 그 여럿이 한 덩어리로 끝나거나 한 덩어리로 취소된다.\
> 예: 위 코드에서 `scope.fork(...)`로 띄운 둘을 `scope.join().throwIfFailed()` 한 줄이 함께 받아 내고, 원문 주석이 그것을 "모두 대기 + 실패 시 전파"라 적는다.

이 기능은 **이 시리즈가 끝나는 편까지도 정식이 되지 않는다** — `java-25.md`가 JEP 505를 5차 프리뷰로, `java-26.md`가 JEP 525를 6차 프리뷰로 적는다.

### Foreign Function & Memory API (JEP 442, Third Preview/3차 프리뷰)
- 19·20의 프리뷰에 이은 **세 번째 프리뷰**. JNI 없이 네이티브 함수 호출과 힙 밖 메모리 접근을 다룬다. 정식화는 Java 22(JEP 454).

### Vector API (JEP 448, Sixth Incubator/6차 인큐베이터)
- SIMD 벡터 연산 API의 **여섯 번째 인큐베이터**. FFM API와 보조를 맞춰 계속 인큐베이터로 유지되었다.

Vector API도 이 시리즈 안에서 정식이 되지 않는다 — `java-26.md`가 JEP 529를 11차 인큐베이터로 적으며 그 사유로 "Valhalla 의존성"을 든다.

---

## 그 외 변경
- **JEP 449: Windows 32-bit x86 포트 폐기 예고** — 향후 제거를 위한 deprecation. 가상 스레드를 32비트에서 fallback 구현해야 하는 부담 등이 배경이다.
- **JEP 451: 에이전트의 동적 로딩 제한 준비** — 실행 중인 JVM에 자바 에이전트를 동적으로 붙일 때 경고를 내보내, 향후 기본 비허용으로 전환할 준비를 한다. 무결성·보안 강화 흐름의 일부.
- 다수의 라이브러리 API 추가, 성능·보안 개선, deprecation 정리.

> **deprecation(폐기 예고)** — 아직 동작은 하지만 앞으로 없앨 것이라고 미리 표시해 두는 일. 쓰는 쪽에 옮길 시간을 준다.\
> 예: 원문이 이 절에서 그 대상으로 든 것이 Windows 32-bit x86 포트이고, 실제 제거는 `java-24.md`의 JEP 479(윈도우 제거)와 `java-25.md`의 JEP 503(완전 제거)에서 이뤄진다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 불릿과 앞뒤 두 문단은 원문의 것이다.)*

Java 21은 **Java 17 이후 가장 중요한 LTS**, 나아가 Java 8 이래 가장 큰 패러다임 전환을 담은 릴리스로 평가된다.

- **가상 스레드(JEP 444)**: Java 동시성 모델을 근본부터 바꿨다. 리액티브 프로그래밍의 복잡성 없이 고동시성을 달성하는 길을 열었고, Spring Boot 3.2, Helidon, Quarkus, Micronaut 등이 빠르게 지원에 나섰다. "thread-per-request의 부활"이라 불린다.
- **패턴 매칭 완성(JEP 440 + 441 + sealed)**: 레코드·sealed·패턴 매칭이 한데 모여, Java가 대수적 데이터 타입(ADT)과 데이터 지향 프로그래밍을 일급으로 표현할 수 있게 되었다. `switch` 한 표현식으로 타입 분기와 분해, 전체성 검사를 동시에 수행한다.
- **Sequenced Collections(JEP 431)**: 25년 묵은 컬렉션 프레임워크의 빈틈(통일된 순서 접근)을 메웠다.
- **Generational ZGC**: 대용량 힙에서 저지연을 유지하는 GC 기술이 한 단계 성숙했다.

LTS라는 점에서 이 모든 기능이 기업 운영 환경의 "기본값"이 되었다. 많은 조직이 Java 8/11/17에서 21로의 점프를 계획하면서, Java 21은 사실상 **현대 Java의 새 기준선**으로 자리 잡았다.

## 용어 풀이

- **LTS(Long-Term Support, 장기 지원)** — 6개월마다 나오는 릴리스 가운데 몇 개를 골라 오래 보안 패치를 제공하는 버전. 이 편 원문이 21과 같은 라인으로 든 것이 Java 17(2021)과 Java 25(2025)다.
- **프리뷰(preview) / 인큐베이터(incubator)** — 정식으로 굳히기 전에 미리 내보내 피드백을 받는 단계. 같은 시리즈 `README.md`의 구분으로 "preview는 언어/API 기능, incubator는 모듈 단위 API"다.
- **Project Loom / Amber / Panama** — 원문이 "여러 해에 걸친 빅 프로젝트"로 묶어 부르는 세 갈래. 이 편 원문이 짝지어 적는 것은 Loom(가상 스레드)·Amber(패턴 매칭) 둘이고, Panama와 FFM API의 짝은 같은 시리즈 `java-22.md`가 짝짓는다.
- **리액티브 프로그래밍** — 원문 표현으로 "비동기·논블로킹(리액티브) 코드". 원문이 그 비용으로 든 것이 "코드 복잡도·디버깅 난이도·스택트레이스 단절"이다.
- **sealed 타입** — 상속·구현할 수 있는 대상을 만든 쪽이 목록으로 닫아 두는 타입. 원문은 이것이 "이미 Java 17(JEP 409)에서 정식화돼 있던" 것이라고 적는다.
- **캐리어 스레드(carrier thread)** — 가상 스레드를 실제로 얹어 돌리는 진짜 OS 스레드. 원문 표현으로 "플랫폼(OS) 스레드".
- **M:N 다중화** — 많은 쪽(M)을 적은 쪽(N) 위에 갈아 끼워 가며 돌리는 방식. 원문은 플랫폼 스레드를 "OS 스레드와 1:1", 가상 스레드를 "캐리어 스레드 위에서 M:N"으로 갈라 적는다.
- **마운트 / 언마운트(mount / unmount)** — 가상 스레드를 캐리어 위에 올리는 것 / 캐리어에서 내려놓는 것. 내려놓은 동안 원문 도식 표현으로 "힙에 스택 보관 (대기)"이 되고, 원문 표현대로 "블로킹이 끝나면 다시 마운트되어 이어서 실행된다".
- **thread-per-request(요청 하나당 스레드 하나)** — 요청 하나마다 스레드 하나를 붙여 처리하는 모델. 원문 표현으로 "단순하고 직관적인 모델"이다.
- **`ThreadLocal`** — 스레드마다 따로 한 칸씩 갖는 저장소. 이 편의 변화는 "thread-local 사용을 opt-out 하는 옵션 제거"다.
- **고정(pinning)** — 가상 스레드가 캐리어에 붙어 내려오지 못하는 상태. 원문이 든 조건은 `synchronized` 블록 안에서의 블로킹이고, 원문 표현으로 "확장성이 떨어질 수 있다".
- **CPU 바운드 / 블로킹 I/O** — 계산하느라 바쁜 일 / 바깥에서 답이 오기를 기다리는 일. 원문은 앞쪽에 대해 "이점이 적다", 뒤쪽에 대해 "강점은 **블로킹 I/O가 많은 워크로드**에서 나온다"고 적는다.
- **분해(deconstruct) / 바인딩** — 객체를 그 안의 칸들로 쪼개어 각 칸에 이름을 붙여 바로 쓰는 것. 원문 표현으로 "레코드를 분해(deconstruct)하여 컴포넌트를 곧바로 바인딩한다".
- **중첩(nested) 패턴** — 쪼갠 칸 안에 또 패턴을 적는 것. 원문 표현으로 "깊은 객체 구조를 한 줄로 풀어낸다".
- **전체성(exhaustiveness)** — 있을 수 있는 경우를 빠짐없이 다뤘는지 컴파일러가 확인해 주는 성질. 원문 표현으로 "모든 입력값을 빠짐없이 처리(전체성)"이고, sealed 타입·enum과 결합하면 "컴파일 타임에 누락이 잡힌다".
- **타입 패턴** — `case` 라벨에 타입을 적고 그 타입의 이름으로 값을 받는 것.
- **가드 조건(`when` 절)** — 타입이 맞아도 조건을 하나 더 걸어 그때만 그 갈래로 가게 하는 것. 이 문법은 `java-19.md`가 3차 프리뷰에서 `&&`를 대신해 도입했다고 적는 것이다.
- **`SequencedCollection` / `SequencedSet` / `SequencedMap`** — 이 편이 새로 도입한, 순서가 있는 컬렉션을 위한 세 인터페이스.
- **약한 세대 가설** — 원문 표현으로 "대부분의 객체는 금방 죽는다"는 관찰.
- **할당 stall** — 새 객체를 만들 자리가 나기를 기다리느라 멈칫하는 것. 원문이 세대 ZGC의 결과로 든 셋 중 첫째가 "할당 stall 감소"다.
- **KEM(키 캡슐화 메커니즘)** — 원문 표현으로 "공개키 암호로 대칭키를 안전하게 전달하는 현대적 기법". 이 편이 도입한 것은 그 표준 API(`javax.crypto.KEM`)다.
- **보간(interpolation)** — 문자열 안에 값이 들어갈 자리를 뚫어 두고 실행할 때 채우는 것. 이 편의 문자열 템플릿은 프리뷰였고 이후 철회됐다.
- **보일러플레이트(boilerplate)** — 뜻은 없는데 형식상 꼭 적어야 하는 상투적인 코드. 원문이 없앨 수 있다고 든 것이 `public static void`·`String[] args`·클래스 선언이다.
- **구조적 동시성** — 원문 표현으로 "다중 작업을 하나의 단위로 다"루는 것. 이 편에서는 프리뷰이고, `java-26.md`까지도 프리뷰로 남는다.
- **deprecation(폐기 예고)** — 아직 동작하지만 앞으로 없앨 것이라고 미리 표시해 두는 일.

## 참고 출처
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)
- [JEP 440: Record Patterns](https://openjdk.org/jeps/440)
- [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441)
- [JEP 431: Sequenced Collections](https://openjdk.org/jeps/431)
- [JEP 439: Generational ZGC](https://openjdk.org/jeps/439)
- [JEP 452: Key Encapsulation Mechanism API](https://openjdk.org/jeps/452)
- [JEP 430: String Templates (Preview)](https://openjdk.org/jeps/430)
- [JEP 443: Unnamed Patterns and Variables (Preview)](https://openjdk.org/jeps/443)
- [JEP 445: Unnamed Classes and Instance Main Methods (Preview)](https://openjdk.org/jeps/445)
- [JEP 446: Scoped Values (Preview)](https://openjdk.org/jeps/446)
- [JEP 453: Structured Concurrency (Preview)](https://openjdk.org/jeps/453)
- [JEP 442: Foreign Function & Memory API (Third Preview)](https://openjdk.org/jeps/442)
- [OpenJDK JDK 21 프로젝트 페이지](https://openjdk.org/projects/jdk/21/)
- [InfoQ: Java 21, the Next LTS Release, Delivers Virtual Threads, Record Patterns and Pattern Matching](https://www.infoq.com/news/2023/09/java21-released/)
- [Oracle Java Magazine: Java 21 is here](https://blogs.oracle.com/javamagazine/java-21-now-available/)
