# cpp/syntax/21 — 추상 클래스·순수 가상·vtable 비용 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **「이 호출이 어셈블리에서 무엇이 되나」를 맞히는 것**이 절반이다 — 「가상이니까 느리다」로 뭉개지 말고
> **간접 호출 · 이름으로 부르는 직접 호출 · `call` 이 사라진 인라인** 셋을 갈라야 한다.
> **환경** — g++ 13.3.0 · clang 18.1.3 · javac 21.0.5 · x86-64 Linux.
> 기본 명령은 `g++ -std=c++20 -Wall -Wextra -pedantic <파일>.cpp -o ex && ./ex`.
> ★★★ **이 주제의 본체는 「`-O2` 어셈블리」다**(5번) — 탐침 여덟 × 두 컴파일러 × `-O0`/`-O2` 격자.
> ★★★ **이 편은 시간을 재지 않았다.** 「가상 호출이 느리다」는 **이 문서의 답이 아니다** — 답은 **명령**으로 적는다.
> ★ **「부적용인 창」이 있다** — ASan. 이 주제의 실패는 메모리 오류가 아니라 `terminate` 다.
> ★★ **[19번](../19-inheritance-virtual-functions-override-final/)이 「부적용」으로 넘긴 비용의 창을 여기서 연다.**

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. ★★ 순수 가상 셋 중 하나만 덮은 파생 (예측)

```cpp
/* abs01.cpp */
// 순수 가상이 셋인 인터페이스 — 하나만 덮은 파생을 만들면 컴파일러가 남은 이름을 나열하나
struct Codec {
    virtual int  encode(int) const = 0;
    virtual int  decode(int) const = 0;
    virtual const char* name() const = 0;
    virtual ~Codec() = default;
};
struct Half : Codec {
    int encode(int x) const override { return x + 1; }        // 셋 중 하나만 덮었다
};

int main() {
    Codec c;                             // 1. 인터페이스 자체를 만든다
    Half h;                              // 2. 하나만 덮은 파생을 만든다
    Codec* p = new Half;                 // 3. new 로 만든다
    (void)c; (void)h; (void)p;
}
```

- 1\~3번 중 **몇 줄이 에러**인가?
- ★★ 두 컴파일러는 에러와 함께 **남은 순수 가상의 이름**을 나열하나 — 나열한다면 `Half` 의 목록에 `encode` 가 들어 있나?
- ★ 3번(`new Half`)에도 목록이 또 나오나?

### 2. ★★ 본체가 있는 순수 가상 (예측)

```cpp
/* abs02.cpp */
// 순수 가상에 본체를 준다 — 그래도 추상인가, 그 본체는 누가 부르나
#include <cstdio>
#include <type_traits>

struct Logger {
    virtual void log(const char* m) const = 0;       // 순수 가상 — 파생이 반드시 덮는다
    virtual ~Logger() = default;
};
void Logger::log(const char* m) const {              // ★ 그런데 본체가 있다(클래스 밖에서 정의)
    std::printf("      Logger::log  [기본 형식] %s\n", m);
}

struct Stamp : Logger {
    void log(const char* m) const override {
        std::printf("      Stamp::log   앞에 도장을 찍고 ->\n");
        Logger::log(m);                              // ★ 기반의 본체를 이름으로 부른다
    }
};

int main() {
    std::printf("(1) is_abstract<Logger> = %d · is_abstract<Stamp> = %d\n",
                (int)std::is_abstract_v<Logger>, (int)std::is_abstract_v<Stamp>);
    Stamp s;
    const Logger& r = s;
    std::printf("(2) r.log(\"hi\") — 가상 호출\n");
    r.log("hi");
    std::printf("(3) r.Logger::log(\"hi\") — 이름으로 부르면 가상 디스패치가 꺼진다\n");
    r.Logger::log("hi");
}
```

- ★★ `is_abstract<Logger>` 는 0 인가 1 인가?
- `(2)` 와 `(3)` 에서 각각 **어느 함수들이** 찍히나?
- ★ 본체를 `virtual void log(...) const = 0 { … }` 처럼 **클래스 안에 한 줄로** 쓰면?

### 3. ★★★ 생성자 안에서 순수 가상을 직접 부르면 (예측)

```cpp
/* abs03.cpp */
// 생성자 안에서 순수 가상을 「직접」 부른다 — 19편의 「생성자 속 가상 호출은 기반 것」의 극단
#include <cstdio>

struct Base {
    Base() { std::fprintf(stderr, "      Base() 가 init() 을 직접 부른다\n"); init(); }
    virtual void init() = 0;                          // 순수 가상 — 본체가 없다
    virtual ~Base() = default;
};
struct Derived : Base {
    void init() override { std::fprintf(stderr, "      Derived::init\n"); }
};

int main() { Derived d; }
```

- ★★★ g++ 와 clang 각각에서 **컴파일·링크·실행 중 어디서** 멈추나?
- ★★ 두 컴파일러가 **경고**를 내나?
- ★ `Derived::init` 은 한 번이라도 불리나?

### 4. ★★★ 비가상 함수를 한 번 거쳐서 부르면 (예측)

```cpp
/* abs04.cpp */
// 생성자 안에서 순수 가상을 「비가상 함수를 한 번 거쳐」 부른다
// 마커는 표준 오류로 찍는다 — terminate 로 abort 하면 표준 출력 버퍼가 통째로 사라진다
#include <cstdio>

struct Base {
    Base() { std::fprintf(stderr, "      Base() 가 setup() 을 부른다\n"); setup(); }
    void setup() { std::fprintf(stderr, "      setup() 이 init() 을 부른다\n"); init(); }  // 비가상 중간 다리
    virtual void init() = 0;
    virtual ~Base() = default;
};
struct Derived : Base {
    void init() override { std::fprintf(stderr, "      Derived::init\n"); }
};

int main() {
    std::fprintf(stderr, "(1) Derived 를 만든다\n");
    Derived d;
    std::fprintf(stderr, "(2) 여기까지 왔다\n");
}
```

- ★★★ **경고는 몇 건**이고 **`run exit`** 는 무엇인가 — 두 컴파일러가 같은가?
- ★★ 표준 출력으로 마커를 찍었다면 무엇이 보였을까 — 왜 `stderr` 로 찍었나?
- ★ `pure virtual method called` 는 **누가** 찍는 문구인가?

### 5. ★★★ 같은 `f()` 를 여덟 자리에서 부른다 (예측)

```cpp
/* devirt.cpp */
// 디버추얼라이제이션 탐침 — 같은 f() 를 여덟 가지 자리에서 부른다. 함수마다 어셈블리를 센다
struct B            { virtual int f() const; virtual ~B() = default; };
struct Dn : B       { int f() const override { return 3; } };        // 아무것도 안 붙였다
struct Df final : B { int f() const override { return 1; } };        // 클래스에 final
struct Dm : B       { int f() const final    { return 2; } };        // 함수에 final
struct N            { int g() const { return 4; } };                 // 가상이 아니다

extern "C" {
int t1_base_ref(const B& b)        { return b.f(); }   // 1. 기반 참조로 부른다
int t2_derived_ref(const Dn& d)    { return d.f(); }   // 2. 파생 참조 — 그 밑에 또 파생이 있을 수 있다
int t3_final_class(const Df& d)    { return d.f(); }   // 3. 정적 타입이 final 클래스
int t4_final_func(const Dm& d)     { return d.f(); }   // 4. 정적 타입의 f 가 final
int t5_local_object()              { Dn d; return d.f(); }          // 5. 지역 객체 — 동적 타입이 보인다
int t6_new_then_call()             { B* p = new Dn; int r = p->f(); delete p; return r; }  // 6. 방금 new 한 것
int t7_qualified(const Dn& d)      { return d.Dn::f(); }            // 7. 이름으로 부른다
int t8_nonvirtual(const N& n)      { return n.g(); }                // 8. 비가상 — 대조군
}
```

- ★★★ `-O2` 에서 **1번(`const B&`)** 은 간접 호출로 남나?
- ★★★ **3·4·5번**(`final` 클래스 · `final` 함수 · 지역 객체)은 **`-O0`** 에서 간접인가 직접인가?
- ★★ **2번(`const Dn&`)** 을 `-O2` 로 내리면 g++ 와 clang 이 같은 코드를 내나?
- ★ 8번(비가상)은 `-O2` 에서 `call` 이 남나?

### 6. ★★ g++ 의 2번 탐침 어셈블리가 하는 일 (왜)

- ★★ g++ `-O2` 의 `t2_derived_ref` 에 있는 `leaq _ZNK2Dn1fEv(%rip)` · `cmpq` · `jne` 세 줄은 **무엇을 확인하나**?
- ★★ 그렇게 확인할 거면서 왜 **간접 호출(`jmp *%rax`)도 남겨 두나**?
- ★ 그 동작을 끄는 g++ 옵션은 무엇이고, 끄면 코드가 어떻게 되나?

### 7. ★★ 인터페이스 둘을 물려받으면 (예측)

```cpp
/* abs05.cpp */
// 인터페이스 관용구 — 데이터 없는 순수 가상만의 클래스, 그리고 둘을 함께 물려받으면
#include <cstdio>
#include <type_traits>

struct Reader { virtual int  read() = 0;     virtual ~Reader() = default; };   // 데이터가 없다
struct Writer { virtual void write(int) = 0; virtual ~Writer() = default; };

struct Pipe : Reader, Writer {                   // 인터페이스 둘을 구현한다
    int buf = 0;
    int  read() override       { return buf; }
    void write(int v) override { buf = v; }
};

int main() {
    std::printf("(1) sizeof  Reader %zu · Writer %zu · Pipe %zu (int 는 %zu)\n",
                sizeof(Reader), sizeof(Writer), sizeof(Pipe), sizeof(int));
    std::printf("(2) is_abstract  Reader %d · Pipe %d  |  is_polymorphic Reader %d\n",
                (int)std::is_abstract_v<Reader>, (int)std::is_abstract_v<Pipe>,
                (int)std::is_polymorphic_v<Reader>);
    Pipe p;
    Reader* r = &p;
    Writer* w = &p;
    w->write(42);
    std::printf("(3) w->write(42) 뒤 r->read() = %d\n", r->read());
    std::printf("(4) 같은 객체인데 포인터 값이 다른가: (char*)w - (char*)r = %td\n",
                (char*)w - (char*)r);
}
```

- `sizeof` 는 `Reader`·`Writer`·`Pipe` 각각 얼마인가?
- ★★ `(char*)w - (char*)r` 은 0 인가 — 아니라면 얼마인가?
- ★ `Pipe` 의 vtable 에서 `offset_to_top` 칸의 값은 19편 때처럼 0 인가?

### 8. ★★★ 「비용」으로 무엇을 셌나 (경계)

- ★★★ 이 편이 「가상 호출의 비용」으로 **센 것 셋**은 무엇인가?
- ★★★ 그 셋에서 「**그래서 느리다**」로 가려면 무엇이 더 있어야 하나 — 이 편은 그것을 했나?
- ★ 실행 시간 창을 「부적용」이 아니라 「안 잰 것」으로 둔 이유는?

### 9. ★★ C# 과 Java 는 이 자리를 어디서 푸나 (연결)

- ★★ C# 의 `sealed` 타입 가상 메서드 호출은 IL 에서 무엇이 되나 — 어느 갈래 몇 번이 쟀나?
- ★★ 자바의 `final` 클래스 메서드 호출은 바이트코드에서 무엇이 되나?
- ★ C++ 에서 같은 자리(`final` 클래스)는 `-O0` 에서 무엇이 되나?

### 10. ★★ 이 주제의 사실이 다섯 층 중 어디에 있나 (경계)

- ★★ 「**가상 함수를 vtable 로 디스패치한다**」는 표준인가?
- ★★ 「**`offset_to_top` 이 -8 이다**」는 어느 층인가 — 19편이 vtable 배치를 둔 층과 같은가?
- ★★ 「**g++ 만 추측 디버추얼라이제이션을 한다**」는 어느 층인가?
- ★ 「생성자에서 순수 가상을 가상 호출」은?

### 11. 다른 주제와 잇기 (연결)

- ★★ **19편이 넘긴 「부적용인 창」은** 무엇이었고 이 편 어느 절이 이어받았나?
- ★ 5번 질문의 6번 탐침(`new` 직후) `-O0` 의 「간접 2」 중 하나는 무엇을 부르는 것인가 — 어느 편의 무엇인가?
- ★ **순수 가상 소멸자**의 정본은 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
