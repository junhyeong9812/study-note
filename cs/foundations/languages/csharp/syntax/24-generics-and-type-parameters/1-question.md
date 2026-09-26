# csharp/syntax/24 — 제네릭과 타입 매개변수 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ★★★ 이 주제의 질문은 「**런타임이 `T` 를 아는가**」 하나로 거의 다 풀린다 — 그리고 「**타입이 따로인 것**」과 「**코드가 따로인 것**」을 갈라라.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-langversion:latest` · `-preferreduilang:en-US`. 대비는 **javac 21.0.5** 다.
> ★★★ **본체 창은 ③ 리플렉션과 C# 대 Java 격자다.** 코드 주소·메서드 핸들은 **「같나 다르나」로만** 견줬다(값은 실행마다 다르다).
> 선행 — [03번](../03-boxing-and-unboxing/)(박싱 — 그 (4)가 이 주제로 넘겼다).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 제네릭을 리플렉션으로 물으면 (예측)

```csharp
// cs24b-refl.cs
using System;
using System.Collections.Generic;
class Holder<T> { public static int Count; }
static class Gen {
    public static string Name<T>()            => typeof(T).Name;
    public static T Make<T>() where T : new() => new T();
    public static T[] Arr<T>(int n)           => new T[n];
    public static T Def<T>()                  => default!;
    public static bool Is<T>(object o)        => o is T;
    public static string Over(List<int> xs)    => "List<int> 판";
    public static string Over(List<string> xs) => "List<string> 판";
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] typeof(List<int>) == typeof(List<string>) : {typeof(List<int>) == typeof(List<string>)}");
        object xs = new List<string>();
        Console.WriteLine($"[2] 인자 : {string.Join(",", Array.ConvertAll(xs.GetType().GetGenericArguments(), t => t.Name))}");
        Console.WriteLine($"[3] xs is List<int> : {xs is List<int>} · xs is List<string> : {xs is List<string>}");
        Console.WriteLine($"[4] Name<int>() = {Gen.Name<int>()} · Name<string>() = {Gen.Name<string>()}");
        Console.WriteLine($"[5] Make<List<int>>().GetType() = {Gen.Make<List<int>>().GetType().Name}");
        Console.WriteLine($"[6] Arr<string>(3).GetType() = {Gen.Arr<string>(3).GetType()} · Arr<int>(3) = {Gen.Arr<int>(3).GetType()}");
        Console.WriteLine($"[7] Def<int>() = {Gen.Def<int>()} · Def<string>() is null = {Gen.Def<string>() is null}");
        Console.WriteLine($"[8] Is<string>(\"a\") = {Gen.Is<string>("a")} · Is<int>(\"a\") = {Gen.Is<int>("a")}");
        Console.WriteLine($"[9] {Gen.Over(new List<int>())} · {Gen.Over(new List<string>())}");
        Holder<int>.Count = 1; Holder<string>.Count = 2; Holder<object>.Count = 3;
        Console.WriteLine($"[10] Holder<int>.Count={Holder<int>.Count} Holder<string>.Count={Holder<string>.Count} Holder<object>.Count={Holder<object>.Count}");
        Console.WriteLine($"[11] typeof(List<>) = {typeof(List<>)} · IsGenericTypeDefinition={typeof(List<>).IsGenericTypeDefinition}");
    }
}
```

- `[1]`\~`[11]` 에 무엇이 찍히는가?
- ★★★ `[1]` 과 `[3]` — 타입 인자까지 구별되는가?
- ★★ `[6]` `Arr<string>(3)` 은 `object[]` 인가 다른 것인가?
- ★★ `[10]` 세 `Count` 는 같은 필드인가?

### 2. ★★ `T` 를 쓰는 다섯 메서드의 IL (예측)

```csharp
// cs24b-il.cs
using System;
public static class Gen {
    public static string Name<T>()            => typeof(T).Name;
    public static T Make<T>() where T : new() => new T();
    public static T[] Arr<T>(int n)           => new T[n];
    public static T Def<T>()                  => default!;
    public static bool Is<T>(object o)        => o is T;
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Name", "Make", "Arr", "Def", "Is" }) Il.Dump(typeof(Gen), n);
    }
}
```

- 다섯 메서드의 IL 에 **`T` 가 토큰으로 그대로 나오는 명령**은 각각 무엇인가?
- ★★ `Make`(`new T()`)는 생성자를 **직접** 부르는가?

### 3. ★★★ 같은 모양 10칸 — C# 을 돌리고 Java 를 던지면 (예측)

```csharp
// cs24b-grid.cs
using System;
using System.Collections.Generic;
class G1<T> where T : new() { public T Make() => new T(); }
class G2<T> { public T[] Arr(int n) => new T[n]; }
class G3<T> { public string Name() => typeof(T).Name; }
class G4<T> { public bool Test(object o) => o is T; }
class G5 { public bool Test(object o) => o is List<string>; }
class G6 { public string F(List<string> a) => "s"; public string F(List<int> a) => "i"; }
class G7 { public List<int> Xs = new(); }
class G8<T> { public static T? Shared; }
class Holder<T> { public static int Count; public void Bump() => Count++; }
class Program {
    static void Main() {
        Console.WriteLine($"[1] {new G1<List<int>>().Make().GetType().Name}");
        Console.WriteLine($"[2] {new G2<string>().Arr(2).GetType()}");
        Console.WriteLine($"[3] {new G3<string>().Name()}");
        Console.WriteLine($"[4] {new G4<string>().Test("a")} {new G4<string>().Test(1)}");
        Console.WriteLine($"[5] {new G5().Test(new List<string>())} {new G5().Test(new List<int>())}");
        Console.WriteLine($"[6] {new G6().F(new List<string>())}{new G6().F(new List<int>())}");
        Console.WriteLine($"[7] {new G7().Xs.GetType().GetGenericArguments()[0]}");
        G8<int>.Shared = 1; G8<string>.Shared = "b";
        Console.WriteLine($"[8] {G8<int>.Shared} {G8<string>.Shared}");
        Console.WriteLine($"[9] List<string> 와 List<int> 의 GetType() 이 같나 : {new List<string>().GetType() == new List<int>().GetType()}");
        new Holder<string>().Bump(); new Holder<int>().Bump();
        Console.WriteLine($"[10] Holder<string>.Count={Holder<string>.Count} Holder<int>.Count={Holder<int>.Count}");
    }
}
```

- C# 쪽 `[1]`\~`[10]` 에 무엇이 찍히는가?
- ★★★ 같은 모양을 Java 로 적으면(`new T()` · `new T[n]` · `T.class` · `instanceof T` · `instanceof List<String>` · `List<String>`/`List<Integer>` 오버로드 · `List<int>` · `static T` 필드) **javac 가 받아 주는 칸**이 있는가?
- ★★★ Java 로 **돌아가는** 두 칸(`getClass()` 비교 · 정적 카운터)은 무엇을 찍는가?

### 4. ★★★ 코드 주소와 핸들을 견주면 (예측)

```csharp
// cs24b-canon.cs
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
class Box<T> {
    [MethodImpl(MethodImplOptions.NoInlining)] public int Size() => 1;
}
class Program {
    static IntPtr Code(Type t, string m) {
        var mi = t.GetMethod(m)!;
        RuntimeHelpers.PrepareMethod(mi.MethodHandle, new[] { t.TypeHandle });   // JIT 을 먼저 시킨다
        return mi.MethodHandle.GetFunctionPointer();
    }
    static IntPtr Desc(Type t, string m) => t.GetMethod(m)!.MethodHandle.Value;
    static void Main() {
        Console.WriteLine($"[1] System.__Canon 이 있나 : {typeof(object).Assembly.GetType("System.__Canon") is not null}");
        Type ls = typeof(List<string>), lo = typeof(List<object>), li = typeof(List<int>), ll = typeof(List<long>);
        Console.WriteLine($"[2] 코드 주소  List<string>.Add == List<object>.Add : {Code(ls, "Add") == Code(lo, "Add")}");
        Console.WriteLine($"[3] 코드 주소  List<string>.Add == List<int>.Add    : {Code(ls, "Add") == Code(li, "Add")}");
        Console.WriteLine($"[4] 코드 주소  List<int>.Add    == List<long>.Add   : {Code(li, "Add") == Code(ll, "Add")}");
        Console.WriteLine($"[5] 메서드 핸들 List<string>.Add == List<object>.Add : {Desc(ls, "Add") == Desc(lo, "Add")}");
        Console.WriteLine($"[6] 메서드 핸들 List<int>.Add    == List<long>.Add   : {Desc(li, "Add") == Desc(ll, "Add")}");
        Type bs = typeof(Box<string>), bu = typeof(Box<Uri>), bi = typeof(Box<int>);
        Console.WriteLine($"[7] 코드 주소  Box<string>.Size == Box<Uri>.Size    : {Code(bs, "Size") == Code(bu, "Size")}");
        Console.WriteLine($"[8] 코드 주소  Box<string>.Size == Box<int>.Size    : {Code(bs, "Size") == Code(bi, "Size")}");
        Console.WriteLine($"[9] 타입 핸들  Box<string> == Box<Uri>              : {bs.TypeHandle.Value == bu.TypeHandle.Value}");
    }
}
```

- `[1]`\~`[9]` 는 각각 `True` 인가 `False` 인가?
- ★★★ `[2]` 와 `[3]` — 타입 인자가 **무엇일 때** 코드가 같아지는가?
- ★★★ `[7]` 과 `[9]` 는 같은 두 타입을 견줬다 — 답이 같은가?
- ★ `csc -optimize` + `TieredCompilation=0` 판에서 달라지는 줄이 있는가?

### 5. ★★ 제약을 어긴 호출 여섯 (예측)

```csharp
// cs24b-cons.cs
using System;
class NoCtor { NoCtor(int x) { } }
static class C {
    public static void Ref<T>() where T : class { }
    public static void Val<T>() where T : struct { }
    public static void New<T>() where T : new() { }
    public static void Unm<T>() where T : unmanaged { }
    public static void Nn<T>(T x) where T : notnull { }
}
class Program {
    static void Main() {
        C.Ref<int>();
        C.Val<string>();
        C.Val<int?>();
        C.New<NoCtor>();
        C.Unm<string>();
        string? s = null;
        C.Nn(s);
    }
}
```

- 여섯 호출 각각의 **진단 코드**는? 경고인 것이 있는가?
- ★ `C.Val<int?>()` 는 통과하는가 — `int?` 는 구조체다.

### 6. ★★ 박싱이 날 자리 네 줄 (예측)

```csharp
// cs24b-alloc.cs
using System;
using System.Collections;
using System.Collections.Generic;
class Program {
    static int SumObj(object a, object b) => (int)a + (int)b;
    static T Pick<T>(T a, T b) => a;
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        var al = new ArrayList(1000);
        var li = new List<int>(1000);
        long sink = 0;
        Console.WriteLine($"[1] ArrayList.Add(i)         1000번 : {M(() => { al.Clear(); for (int i = 0; i < 1000; i++) al.Add(i); })} 바이트");
        Console.WriteLine($"[2] List<int>.Add(i)         1000번 : {M(() => { li.Clear(); for (int i = 0; i < 1000; i++) li.Add(i); })} 바이트");
        Console.WriteLine($"[3] SumObj(i, i) object 인자 1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += SumObj(i, i); })} 바이트");
        Console.WriteLine($"[4] Pick<int>(i, i)          1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += Pick(i, i); })} 바이트");
        GC.KeepAlive(sink);
    }
}
```

- 네 줄의 바이트는 각각?
- ★★★ 네 판(2×2)에서 갈린 줄은 몇 개인가 — [20번](../20-enum-and-flags/)의 `HasFlag` 와 무엇이 다른가?

### 7. ★★★ 타입 구별과 코드 벌 수는 누가 정하나 (왜)

- 「`List<int>` 와 `List<string>` 이 다른 런타임 타입이다」는 **누가 보장**하나?
- ★★★ 「참조 타입 인자끼리 코드를 나눠 쓴다」는 누가 정하나 — Learn 에 적혀 있으면 보장인가?
- ★ 4번 `[9]` 는 이 둘이 **어떻게 함께 성립**하는지 무엇으로 보여 주는가?

### 8. ★★ Java 쪽 결과의 뿌리 (왜)

- 3번에서 Java 쪽이 그렇게 나온 뿌리를 한 문장으로 말하면?
- ★★ Kotlin 은 같은 JVM 위에서 그중 `is T` 를 어떻게 뚫나 — 그 장치 없이 쓰면 무슨 에러인가?

### 9. ★★ 정적 필드는 어디에 붙나 (경계)

- 1번 `[10]` 의 `Holder<string>` 과 `Holder<object>` 는 4번에 따르면 **코드를 공유**할 것이다 — 그런데 왜 `Count` 가 따로인가?
- ★ 이 성질의 쓸모와 함정을 하나씩.

### 10. ★ Rust·Go 의 제네릭과 (경계)

- Rust 는 인자마다 코드를 몇 벌 만드나 — .NET 과 어디가 다른가?
- ★ Go 의 방식은 어느 쪽에 가까운가 — 이 판에서 확인했나?

### 11. 다른 주제와 잇기 (연결)

- ★★ 박싱 자체와 `List<int>` 대 `ArrayList` 를 한 판에서 잰 주제는?
- ★★ 제약의 **선택 기준**과 `default(T)` 의 정본은 이 목록의 몇 번 주제인가?
- ★ Java 소거의 결과(브리지 메서드 등)는 어느 갈래 몇 번인가?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
