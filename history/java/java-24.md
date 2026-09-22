# Java 24 (2025.03)

> 원본: `~/project/java-history/java/java-24.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-20).\
> 연도·버전·JEP 번호·클래스/옵션/알고리즘 이름·자바 코드블록 3개와 셸 코드블록 1개·「릴리스 정보」의 JEP 목록·「참고 출처」는 원문 그대로다.\
> 도식은 넣지 않았다 — 원문에 도식이 없고, 원문이 절차로 적은 AOT 세 단계는 원문 셸 코드블록의 주석에 이미 번호로 나뉘어 있다.\
> 「한눈에」의 전날 손질 비유와 대응표, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.\
> 「이 편의 기능은 지금 어디쯤인가」 표의 「그 앞」·「그 뒤」 칸은 같은 시리즈의 다른 편(`java-21.md`~`java-23.md`·`java-25.md`·`java-26.md`)에서 끌어온 보충이고, 출처 편을 칸마다 적었다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 무려 24개의 JEP를 담은 대형 비-LTS 릴리스. 클래스 파일 API와 스트림 Gatherers를 정식화하고, 양자내성 암호(ML-KEM·ML-DSA)와 AOT 클래스 로딩을 도입했으며, 32비트 x86 포트를 정리하기 시작했다.

이 편이 처음 들여온 것 하나를 비유로 읽으면 **가게를 열 때마다 재료를 꺼내 손질하던 것을, 전날 손질해 둔 것을 그대로 쓰게 된 일**이다.\
**AOT 클래스 로딩·링킹도 똑같은 구조다** — 원문 자신이 그 절에서 이렇게 적는다: "애플리케이션이 사용할 클래스를 미리 로드·링크한 캐시를 만들어 시작 시간을 크게 단축한다."

본문 흐름에 쓰는 비유는 이 전날 손질 하나뿐이다 — 용어 블록의 정의에 쓰는 낱말은 비유가 아니라 그 용어의 풀이다.

| 비유 | 실체 |
|---|---|
| 전날 미리 손질해 둔 재료 | AOT 캐시 — 원문 표현으로 "미리 로드·링크한 캐시" |
| 손질 순서를 적어 둔 메모 | 원문이 1단계 주석으로 적은 "학습 단계: AOT 설정 기록" |
| 문을 열자마자 바로 장사 시작 | 원문 표현으로 "시작 시간을 크게 단축한다" |
| 금방 문 닫는 가게일수록 이득이 큰 점 | 원문 표현으로 "특히 단명(short-lived) 프로그램과 마이크로서비스 콜드 스타트에 효과적" |

초보자가 가장 자주 하는 오해부터 짚어 두면 이렇다.

- **이 편의 AOT는 "미리 컴파일"이 아니라 "미리 로드·링크"다.** JEP 제목이 그대로 `Ahead-of-Time Class Loading & Linking`이고, 원문이 캐시에 담긴다고 적은 것도 "애플리케이션이 사용할 클래스"다.
- **Class-File API가 ASM을 없애려는 것이 아니다.** 원문이 그 절에 직접 적어 둔 그대로다 — "외부 ASM 등 서드파티 바이트코드 라이브러리를 폐기 대상으로 삼는 것은 목표가 아니다."
- **JEP 491은 가상 스레드를 빠르게 만든 것이 아니다.** 붙어서 안 떨어지던 자리를 푼 것이다. 원문 표현으로 "동기화 코드 안에서도 가상 스레드가 자유롭게 언마운트되어, Loom의 확장성 제약이 크게 완화되었다"이다.

### 이 편의 기능은 지금 어디쯤인가

가운데 칸은 이 편 원문이 적은 것이고, 양옆 칸은 그 편들의 원문에서 확인한 보충이다.

| 기능 | 그 앞 | 이 편(24)에서의 상태 | 그 뒤 |
|---|---|---|---|
| Class-File API (JEP 484) | `java-22.md` 1차 프리뷰(JEP 457) · `java-23.md` 2차(JEP 466) | **정식** | — |
| Stream Gatherers (JEP 485) | `java-22.md` 1차 프리뷰(JEP 461) · `java-23.md` 2차(JEP 473) | **정식** | — |
| ML-KEM (JEP 496) / ML-DSA (JEP 497) | `java-21.md` JEP 452가 KEM 표준 API를 먼저 깔아 두었다 | **정식** | — |
| Ahead-of-Time Class Loading & Linking (JEP 483) | — (이 편이 처음) | **정식** | `java-25.md`의 JEP 514·515로 이어진다 |
| Synchronize Virtual Threads without Pinning (JEP 491) | `java-21.md`가 이 한계를 "JDK 24의 JEP 491에서 해소된다"고 예고해 두었다 | **정식** | — |
| ZGC: Remove the Non-Generational Mode (JEP 490) | `java-21.md` JEP 439(세대 모드 추가) · `java-23.md` JEP 474(기본값 전환) | **정식**(비-세대 모드 제거) | — |
| Key Derivation Function API (JEP 478) | — (이 편이 1차) | 프리뷰 | `java-25.md` **정식**(JEP 510) |
| Flexible Constructor Bodies (JEP 492) | `java-22.md` 1차(JEP 447, 당시 이름은 "Statements before super(...)") · `java-23.md` 2차(JEP 482) | 3차 프리뷰 | `java-25.md` **정식**(JEP 513) |
| Module Import Declarations (JEP 494) | `java-23.md` 1차 프리뷰(JEP 476) | 2차 프리뷰 | `java-25.md` **정식**(JEP 511) |
| Scoped Values (JEP 487) | `java-21.md` 1차 프리뷰(JEP 446) | 4차 프리뷰 | `java-25.md` **정식**(JEP 506) |
| Simple Source Files and Instance Main Methods (JEP 495) | `java-21.md` 1차 프리뷰(JEP 445) | 4차 프리뷰 | `java-25.md`에서 "Compact Source Files"라는 이름으로 **정식**(JEP 512) |
| Structured Concurrency (JEP 499) | `java-21.md` 1차 프리뷰(JEP 453) | 4차 프리뷰 | `java-26.md` 6차 프리뷰(JEP 525)까지도 **정식이 아니다** |
| Primitive Types in Patterns, instanceof, and switch (JEP 488) | `java-23.md` 1차 프리뷰(JEP 455) | 2차 프리뷰 | `java-26.md` 4차 프리뷰(JEP 530)까지도 **정식이 아니다** |
| Vector API (JEP 489) | `java-23.md` 8차 인큐베이터(JEP 469) | 9차 인큐베이터 | `java-26.md` 11차 인큐베이터(JEP 529)까지도 **정식이 아니다** |
| Generational Shenandoah (JEP 404) / Compact Object Headers (JEP 450) | — | **실험적** | `java-25.md`에서 둘 다 **정식**(JEP 521 · JEP 519) |

한 기능의 이름이 편마다 달라지기도 한다 — 초보자 친화 진입점은 `java-21.md`에서 "미명명 클래스와 인스턴스 main 메서드", `java-22.md`·`java-23.md`에서 "Implicitly Declared Classes and Instance Main Methods", 이 편에서 "Simple Source Files and Instance Main Methods", `java-25.md`에서 "Compact Source Files and Instance Main Methods"로 적힌다. JEP 번호는 편마다 다르니(445·463·477·495·512), 각 편 JEP 목록의 "N차 프리뷰" 차수로 따라가면 같은 줄기다.

## 릴리스 정보
- 정식 출시일: 2025년 3월 18일
- LTS 여부: 아니오 (단기 지원 / Java 25 LTS로 대체)
- 포함 JEP 목록 (총 24개):
  - JEP 404: Generational Shenandoah (실험적)
  - JEP 450: Compact Object Headers (실험적)
  - JEP 472: Prepare to Restrict the Use of JNI
  - JEP 475: Late Barrier Expansion for G1
  - JEP 478: Key Derivation Function API (프리뷰)
  - JEP 479: Remove the Windows 32-bit x86 Port (정식)
  - JEP 483: Ahead-of-Time Class Loading & Linking (정식)
  - JEP 484: Class-File API (정식)
  - JEP 485: Stream Gatherers (정식)
  - JEP 486: Permanently Disable the Security Manager (정식)
  - JEP 487: Scoped Values (4차 프리뷰)
  - JEP 488: Primitive Types in Patterns, instanceof, and switch (2차 프리뷰)
  - JEP 489: Vector API (9차 인큐베이터)
  - JEP 490: ZGC: Remove the Non-Generational Mode (정식)
  - JEP 491: Synchronize Virtual Threads without Pinning (정식)
  - JEP 492: Flexible Constructor Bodies (3차 프리뷰)
  - JEP 493: Linking Run-Time Images without JMODs (정식)
  - JEP 494: Module Import Declarations (2차 프리뷰)
  - JEP 495: Simple Source Files and Instance Main Methods (4차 프리뷰)
  - JEP 496: Quantum-Resistant Module-Lattice-Based Key Encapsulation Mechanism (정식)
  - JEP 497: Quantum-Resistant Module-Lattice-Based Digital Signature Algorithm (정식)
  - JEP 498: Warn upon Use of Memory-Access Methods in sun.misc.Unsafe
  - JEP 499: Structured Concurrency (4차 프리뷰)
  - JEP 501: Deprecate the 32-bit x86 Port for Removal

> **실험적(experimental)** — 프리뷰·인큐베이터와 나란히 놓이는 또 하나의 시험 단계. 같은 시리즈 `README.md`가 셋을 갈라 적기를 "experimental은 주로 JVM/GC 기능을 시험 배포한다"이다.\
> 예: 이 편에서 그 표시를 단 둘이 JEP 404(Generational Shenandoah)와 JEP 450(Compact Object Headers)인데, 둘 다 GC·메모리 쪽이다.

## 시대적 배경

Java 25 LTS 직전의 마지막 비-LTS 릴리스로, JEP 24개라는 역대급 분량을 담았다.\
LTS를 6개월 앞두고 여러 기능을 정식화·안정화하여 LTS의 완성도를 끌어올리려는 의도가 뚜렷하다.\
시대적으로는 **양자컴퓨팅에 대비한 포스트양자 암호(PQC)** 의 표준 도입(ML-KEM, ML-DSA)이 가장 상징적이다. 미국 NIST가 2024년 PQC 표준을 확정한 직후 JDK에 곧바로 반영된 것으로, 자바 플랫폼의 보안 대응 속도를 보여준다.\
또한 가상 스레드의 핀닝(pinning) 문제 해결, AOT 클래스 로딩(Project Leyden의 첫 결실) 등 운영 성능 개선도 두드러진다.

> **PQC(포스트양자 암호)** — 양자컴퓨터가 나와도 버티도록 만든 암호. 원문은 이 편의 도입이 "미국 NIST가 2024년 PQC 표준을 확정한 직후"였다고 적는다.\
> 예: 이 편이 들여온 둘이 ML-KEM과 ML-DSA이고, 그 자리를 같은 시리즈 `java-21.md`가 JEP 452로 먼저 깔아 두었다 — "포스트 양자 암호(PQC) 알고리즘 다수가 KEM 형태라는 점에서, 양자 내성 암호 시대를 대비한 기반 작업이다".

> **Project Leyden** — 원문이 AOT 클래스 로딩을 "첫 결실"로 부르는 갈래의 이름.\
> 예: 원문은 같은 절에서 이것을 "**Project Leyden**의 첫 정식 산출물"이라 한 번 더 적는다.

## 주요 추가 기능

### Class-File API (JEP 484, 정식)
- 클래스 파일을 파싱·생성·변환하는 표준 API가 정식화되었다(22 프리뷰 → 23 2차 프리뷰 → 24 정식). JDK가 내부적으로 두고 있던 ASM 사본을 이 표준 API로 대체할 수 있게 하는 것이 목표이며, 외부 ASM 등 서드파티 바이트코드 라이브러리를 폐기 대상으로 삼는 것은 목표가 아니다.

원문이 "목표이며 … 목표가 아니다"로 둘을 갈라 적은 자리다. 대체 대상은 **JDK 안에 있는 ASM 사본**이고, 바깥에서 각자 쓰는 ASM은 대상이 아니다.

```java
import java.lang.classfile.*;

ClassModel cm = ClassFile.of().parse(bytes);
for (MethodModel m : cm.methods()) {
    System.out.println(m.methodName().stringValue());
}
```

### Stream Gatherers (JEP 485, 정식)
- 사용자 정의 중간 연산 API가 정식화되었다(22 프리뷰 → 23 2차 프리뷰 → 24 정식). `Stream.gather(...)`와 `Gatherers` 팩토리를 표준으로 사용할 수 있다.

```java
List<List<Integer>> windows = Stream.of(1, 2, 3, 4, 5)
    .gather(Gatherers.windowSliding(2))
    .toList(); // [[1, 2], [2, 3], [3, 4], [4, 5]]
```

같은 시리즈 `java-22.md`가 프리뷰 시절에 든 예와 나란히 놓고 보면 이름 하나가 다르다 — 거기서는 `Gatherers.windowFixed(2)`로 `[[1, 2], [3, 4], [5]]`가 나왔고, 여기서는 `Gatherers.windowSliding(2)`로 `[[1, 2], [2, 3], [3, 4], [4, 5]]`가 나온다. 두 주석 모두 원문의 것이다.

### 양자내성 암호 — ML-KEM (JEP 496) / ML-DSA (JEP 497, 정식)
- NIST가 표준화한 격자 기반 포스트양자 암호 알고리즘을 JDK 표준 API로 제공한다. **ML-KEM**(FIPS 203, 키 캡슐화)과 **ML-DSA**(FIPS 204, 디지털 서명)이며, 양자컴퓨터 등장 시에도 안전한 키 교환·서명을 가능케 한다.

> **키 캡슐화 / 디지털 서명** — 상대에게 대칭키를 안전하게 건네는 일 / 이 내용이 나에게서 나왔음을 증명하는 표식을 붙이는 일. 원문이 두 알고리즘에 짝지어 적은 괄호가 각각 "(FIPS 203, 키 캡슐화)"와 "(FIPS 204, 디지털 서명)"이다.\
> 예: 아래 코드에서 앞쪽이 `KeyPairGenerator.getInstance("ML-KEM")`으로 키 쌍만 만들고, 뒤쪽은 `Signature.getInstance("ML-DSA")`까지 가서 `sig.sign()`으로 서명을 만든다.

```java
// ML-KEM 키 쌍 생성 (키 캡슐화용)
KeyPairGenerator kemKpg = KeyPairGenerator.getInstance("ML-KEM");
KeyPair kemKp = kemKpg.generateKeyPair();

// ML-DSA 키 쌍 생성 후 디지털 서명
KeyPairGenerator dsaKpg = KeyPairGenerator.getInstance("ML-DSA");
KeyPair dsaKp = dsaKpg.generateKeyPair();

Signature sig = Signature.getInstance("ML-DSA");
sig.initSign(dsaKp.getPrivate());
sig.update("hello".getBytes());
byte[] signature = sig.sign();
```

### Ahead-of-Time Class Loading & Linking (JEP 483, 정식)
- 애플리케이션이 사용할 클래스를 미리 로드·링크한 캐시를 만들어 시작 시간을 크게 단축한다. **Project Leyden**의 첫 정식 산출물로, 특히 단명(short-lived) 프로그램과 마이크로서비스 콜드 스타트에 효과적이다.

> **콜드 스타트(cold start)** — 막 띄운 직후, 아직 아무것도 데워지지 않은 상태에서의 출발.\
> 예: 원문이 이 기능이 특히 잘 듣는다고 든 둘이 "단명(short-lived) 프로그램"과 "마이크로서비스 콜드 스타트"다.

```bash
# 1) 학습 단계: AOT 설정 기록
java -XX:AOTMode=record -XX:AOTConfiguration=app.aotconf -cp app.jar App
# 2) 생성 단계: AOT 캐시 생성
java -XX:AOTMode=create -XX:AOTConfiguration=app.aotconf -XX:AOTCache=app.aot -cp app.jar
# 3) 실행: 캐시 사용
java -XX:AOTCache=app.aot -cp app.jar App
```

원문이 위 셸 블록에 `# 1)`·`# 2)`·`# 3)`으로 세 단계를 나누고 각 단계에 이름을 붙여 두었다 — "학습 단계: AOT 설정 기록" → "생성 단계: AOT 캐시 생성" → "실행: 캐시 사용"이다.\
세 줄에서 같은 파일 이름이 이어 달린다 — 1단계가 만든 `app.aotconf`를 2단계가 읽어 `app.aot`를 만들고, 3단계가 그 `app.aot`를 쓴다.

### Synchronize Virtual Threads without Pinning (JEP 491, 정식)
- 가상 스레드가 `synchronized` 블록/메서드 안에서 블로킹될 때 캐리어 스레드에 고정(pinning)되던 문제를 해결한다. 이제 동기화 코드 안에서도 가상 스레드가 자유롭게 언마운트되어, Loom의 확장성 제약이 크게 완화되었다.

**왜 이게 나왔나** — 같은 시리즈 `java-21.md`가 이 문제를 정식화 당시의 한계로 적어 두고 그 해소 시점까지 지목해 두었다: "`synchronized` 블록 안에서 블로킹하면 가상 스레드가 캐리어에 **고정**(pinning)되어 확장성이 떨어질 수 있다(이 한계는 이후 JDK 24의 JEP 491에서 해소된다). 21에서는 `ReentrantLock` 사용이 권장됐다."

> **고정(pinning) / 언마운트** — 가상 스레드가 캐리어 스레드에 붙어 내려오지 못하는 상태 / 캐리어에서 내려놓는 것. 정의는 같은 시리즈 `java-21.md`의 가상 스레드 절에 있다.\
> 예: 원문이 이 편의 변화로 적은 것이 "동기화 코드 안에서도 가상 스레드가 자유롭게 언마운트되어"이다.

### ZGC: Remove the Non-Generational Mode (JEP 490, 정식)
- Java 23에서 세대별 ZGC가 기본이 된 뒤, 이 버전에서 비-세대 모드를 완전히 제거했다. `-XX:-ZGenerational` 옵션은 무시되고 향후 제거된다.

이 세 편이 한 줄기다 — `java-21.md`의 JEP 439가 세대 모드를 더했고(당시엔 비세대가 기본), `java-23.md`의 JEP 474가 기본값을 뒤집었고, 이 편의 JEP 490이 옛 모드를 없앴다.

## 그 외 변경
- **Prepare to Restrict the Use of JNI (JEP 472)**: FFM API 정식화에 이어, JNI 사용 시 경고를 발생시켜 향후 제한을 예고. 네이티브 상호운용을 더 안전한 FFM으로 유도한다.
- **Permanently Disable the Security Manager (JEP 486, 정식)**: 오래전 폐기 예고된 SecurityManager를 영구 비활성화(런타임에서 활성화 불가).
- **Key Derivation Function API (JEP 478, 프리뷰)**: HKDF 등 키 유도 함수 표준 API의 첫 프리뷰. (Java 25에서 정식화됨.)
- **Generational Shenandoah (JEP 404, 실험적)** / **Compact Object Headers (JEP 450, 실험적)**: GC·메모리 풋프린트 개선을 실험 단계로 도입.
- **Late Barrier Expansion for G1 (JEP 475)**: G1 GC의 배리어 코드를 컴파일 후반에 확장해 C2 컴파일 비용을 줄인다.
- **Linking Run-Time Images without JMODs (JEP 493, 정식)**: JMOD 파일 없이 `jlink`로 런타임 이미지를 생성할 수 있게 한다. 단 이는 `--enable-linkable-runtime`으로 빌드한 JDK에서만 가능하며, 기본 빌드는 여전히 JMOD를 포함한다. 이를 통해 JDK 설치 크기를 줄일 수 있다.
- **Remove the Windows 32-bit x86 Port (JEP 479)** / **Deprecate the 32-bit x86 Port for Removal (JEP 501)**: 32비트 x86 지원을 단계적으로 종료(윈도우는 제거, 리눅스는 폐기 예고). Java 25에서 완전 제거된다.
- **Warn upon Use of sun.misc.Unsafe Memory-Access Methods (JEP 498)**: 23에서 폐기 예고한 메서드 사용 시 런타임 경고 발생.
- **계속 진행 중인 프리뷰**: Scoped Values(JEP 487, 4차), Structured Concurrency(JEP 499, 4차), Flexible Constructor Bodies(JEP 492, 3차), Module Import Declarations(JEP 494, 2차), Primitive Types in Patterns(JEP 488, 2차), Simple Source Files and Instance Main Methods(JEP 495, 4차), Vector API(JEP 489, 9차 인큐베이터).

> **JNI 제한 / SecurityManager 영구 비활성화** — 원문이 이 절에 나란히 적은 두 가지 조이기. 앞쪽은 "경고를 발생시켜 향후 제한을 예고"하는 단계이고, 뒤쪽은 이미 "영구 비활성화(런타임에서 활성화 불가)"다.\
> 예: 앞쪽이 가리키는 대안이 FFM API인데, 그 FFM이 정식이 된 편을 같은 시리즈 `java-22.md`가 JEP 454로 적는다.

> **JMOD / `jlink`** — JDK를 이루는 모듈 묶음 파일 형식 / 필요한 모듈만 골라 런타임 이미지를 만들어 주는 도구.\
> 예: 원문이 단 단서가 "`--enable-linkable-runtime`으로 빌드한 JDK에서만 가능하며, 기본 빌드는 여전히 JMOD를 포함한다"이다 — 아무 JDK에서나 되는 것이 아니다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다 — 아래 네 문장은 원문의 것이다.)*

Java 24는 LTS 직전 릴리스답게 "정식화 러시"를 보여준다.\
클래스 파일 API·스트림 Gatherers의 정식화는 라이브러리/프레임워크 생태계의 기반을 바꾸었고, 가상 스레드 핀닝 해결은 Loom 채택의 마지막 큰 장애물을 제거했다.\
양자내성 암호의 신속한 표준 도입은 자바가 보안 패러다임 전환에 선제 대응함을 보여준다.\
여기서 안정화된 기능들이 6개월 뒤 Java 25 LTS에서 그대로 정식 기반이 된다.

## 용어 풀이

- **실험적(experimental)** — 프리뷰·인큐베이터와 나란히 놓이는 또 하나의 시험 단계. 같은 시리즈 `README.md`가 "experimental은 주로 JVM/GC 기능을 시험 배포한다"로 적는다.
- **PQC(포스트양자 암호)** — 양자컴퓨터가 나와도 버티도록 만든 암호. 원문은 이 편의 도입이 "미국 NIST가 2024년 PQC 표준을 확정한 직후"였다고 적는다.
- **키 캡슐화 / 디지털 서명** — 상대에게 대칭키를 안전하게 건네는 일 / 이 내용이 나에게서 나왔음을 증명하는 표식을 붙이는 일. 원문이 ML-KEM에 "(FIPS 203, 키 캡슐화)", ML-DSA에 "(FIPS 204, 디지털 서명)"을 짝지어 적는다.
- **Project Leyden** — 원문이 AOT 클래스 로딩을 "첫 정식 산출물"로 부르는 갈래의 이름.
- **콜드 스타트(cold start)** — 막 띄운 직후, 아직 아무것도 데워지지 않은 상태에서의 출발. 원문이 이 기능이 잘 듣는 자리로 "마이크로서비스 콜드 스타트"를 든다.
- **고정(pinning) / 언마운트** — 가상 스레드가 캐리어 스레드에 붙어 내려오지 못하는 상태 / 캐리어에서 내려놓는 것. 그 정의는 같은 시리즈 `java-21.md`의 가상 스레드 절에 있고, 이 편의 JEP 491이 앞쪽을 풀었다.
- **JMOD / `jlink`** — JDK를 이루는 모듈 묶음 파일 형식 / 필요한 모듈만 골라 런타임 이미지를 만들어 주는 도구. 원문은 JMOD 없이 만드는 길이 `--enable-linkable-runtime`으로 빌드한 JDK에서만 열린다고 적는다.

## 참고 출처
- [JDK 24 - OpenJDK 프로젝트 페이지](https://openjdk.org/projects/jdk/24/)
- [Java 24 Delivers New Experimental and Many Final Features - InfoQ](https://www.infoq.com/news/2025/03/java24-released/)
- [Java 24 Features (with Examples) - HappyCoders](https://www.happycoders.eu/java/java-24-features/)
- [Six JDK 24 Features You Should Know About - foojay.io](https://foojay.io/today/six-jdk-24-features-you-should-know-about/)
- [Java version history - Wikipedia](https://en.wikipedia.org/wiki/Java_version_history)
