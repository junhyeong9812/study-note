# csharp/syntax/24 — 제네릭과 타입 매개변수 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **코드 주소·핸들의 값**은 싣지 않았다(실행마다 다르다) — **같나 다르나**만 근거로 쓴다.\
> 근거로 쓰는 것은 **리플렉션 결과 · 옵코드와 토큰 · 진단 코드 · javac `exit` · 스크립트가 센 칸 수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.** 「제네릭이 빠르다」는 문장이 **한 줄도 없다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 타입 인자까지 **런타임에 구별된다** — 정적 필드도 **인자마다 따로**

**출력**

```text
===== 소스: cs24b-refl.cs =====
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
===== csc -out:ex.dll cs24b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] typeof(List<int>) == typeof(List<string>) : False
[2] 인자 : String
[3] xs is List<int> : False · xs is List<string> : True
[4] Name<int>() = Int32 · Name<string>() = String
[5] Make<List<int>>().GetType() = List`1
[6] Arr<string>(3).GetType() = System.String[] · Arr<int>(3) = System.Int32[]
[7] Def<int>() = 0 · Def<string>() is null = True
[8] Is<string>("a") = True · Is<int>("a") = False
[9] List<int> 판 · List<string> 판
[10] Holder<int>.Count=1 Holder<string>.Count=2 Holder<object>.Count=3
[11] typeof(List<>) = System.Collections.Generic.List`1[T] · IsGenericTypeDefinition=True
```

**왜 그런가**

- ★★★ **`[1]` `False`** · **`[3]` `False` · `True`** — `List<int>` 와 `List<string>` 은 **다른 런타임 타입**이고, `is` 가 **인자까지** 검사한다.
- ★★★ **`[6]` `System.String[]` · `System.Int32[]`** — `new T[n]` 이 **진짜 그 타입의 배열**을 만든다(`object[]` 가 아니다).
- ★★ **`[4]` `Int32`·`String` · `[5]` ``List`1`` · `[7]` `0`·`True` · `[8]` `True`·`False` · `[9]` 두 오버로드가 각각** 골라진다.
- ★★★ **`[10]` `1 · 2 · 3`** — `Holder<int>`·`Holder<string>`·`Holder<object>` 의 **정적 필드가 각각** 있다.
- ★ **`[11]` ``List`1[T]`` · `True`** — 인자를 안 채운 정의도 런타임 객체다.

### 2. ★★ **`ldtoken T` · `newarr T` · `initobj T` · `isinst T`** — `new T()` 는 **`Activator::CreateInstance`**

**출력**

```text
===== 소스: cs24b-il.cs =====
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
===== csc -r:il.dll -out:ex.dll cs24b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- Gen.Name ---
  IL_0000: ldtoken T
  IL_0005: call System.Type::GetTypeFromHandle
  IL_000a: callvirt System.Reflection.MemberInfo::get_Name
  IL_000f: ret
--- Gen.Make ---
  IL_0000: call System.Activator::CreateInstance
  IL_0005: ret
--- Gen.Arr ---
  IL_0000: ldarg.0
  IL_0001: newarr T
  IL_0006: ret
--- Gen.Def ---
  .locals [0] T
  IL_0000: ldloca.s 0
  IL_0002: initobj T
  IL_0008: ldloc.0
  IL_0009: ret
--- Gen.Is ---
  IL_0000: ldarg.0
  IL_0001: isinst T
  IL_0006: ldnull
  IL_0007: cgt.un
  IL_0009: ret
```

**왜 그런가**

- ★★★ **`Name` `ldtoken T` · `Arr` `newarr T` · `Def` `initobj T` · `Is` `isinst T`** — IL 이 **`T` 를 그대로** 싣고, JIT 이 인스턴스화할 때 실제 타입으로 바꾼다.
- ★★ **`Make` 는 `call System.Activator::CreateInstance`** — 생성자를 **직접 부르지 않고** 런타임에 찾는다. `where T : new()` 가 그것을 허락하는 계약이다.

### 3. ★★★ C# 은 10칸 전부 돌고, Java 는 **10 / 10** 이 막히거나 소거된다

**출력**

```text
===== 소스: cs24b-grid.cs =====
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
===== csc -nullable:enable -out:ex.dll cs24b-grid.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] List`1
[2] System.String[]
[3] String
[4] True False
[5] True False
[6] si
[7] System.Int32
[8] 1 b
[9] List<string> 와 List<int> 의 GetType() 이 같나 : False
[10] Holder<string>.Count=1 Holder<int>.Count=1
===== 소스: G1.java =====
class G1<T> { T make() { return new T(); } }
===== javac -d j24out j24/G1.java (cc exit=1) =====
j24/G1.java:1: error: unexpected type
class G1<T> { T make() { return new T(); } }
                                    ^
  required: class
  found:    type parameter T
  where T is a type-variable:
    T extends Object declared in class G1
1 error
===== 소스: G2.java =====
class G2<T> { T[] arr(int n) { return new T[n]; } }
===== javac -d j24out j24/G2.java (cc exit=1) =====
j24/G2.java:1: error: generic array creation
class G2<T> { T[] arr(int n) { return new T[n]; } }
                                      ^
1 error
===== 소스: G3.java =====
class G3<T> { String name() { return T.class.getName(); } }
===== javac -d j24out j24/G3.java (cc exit=1) =====
j24/G3.java:1: error: cannot select from a type variable
class G3<T> { String name() { return T.class.getName(); } }
                                      ^
1 error
===== 소스: G4.java =====
class G4<T> { boolean test(Object o) { return o instanceof T; } }
===== javac -d j24out j24/G4.java (cc exit=1) =====
j24/G4.java:1: error: Object cannot be safely cast to T
class G4<T> { boolean test(Object o) { return o instanceof T; } }
                                              ^
  where T is a type-variable:
    T extends Object declared in class G4
1 error
===== 소스: G5.java =====
import java.util.List;
class G5 { boolean test(Object o) { return o instanceof List<String>; } }
===== javac -d j24out j24/G5.java (cc exit=1) =====
j24/G5.java:2: error: Object cannot be safely cast to List<String>
class G5 { boolean test(Object o) { return o instanceof List<String>; } }
                                           ^
1 error
===== 소스: G6.java =====
import java.util.List;
class G6 { void f(List<String> a) { } void f(List<Integer> a) { } }
===== javac -d j24out j24/G6.java (cc exit=1) =====
j24/G6.java:2: error: name clash: f(List<Integer>) and f(List<String>) have the same erasure
class G6 { void f(List<String> a) { } void f(List<Integer> a) { } }
                                           ^
1 error
===== 소스: G7.java =====
import java.util.List;
class G7 { List<int> xs; }
===== javac -d j24out j24/G7.java (cc exit=1) =====
j24/G7.java:2: error: unexpected type
class G7 { List<int> xs; }
                ^
  required: reference
  found:    int
1 error
===== 소스: G8.java =====
class G8<T> { static T shared; }
===== javac -d j24out j24/G8.java (cc exit=1) =====
j24/G8.java:1: error: non-static type variable T cannot be referenced from a static context
class G8<T> { static T shared; }
                     ^
1 error
===== 소스: Ex24.java =====
import java.util.ArrayList;
class Holder<T> { static int count; void bump() { count++; } }
public class Ex24 {
    public static void main(String[] a) {
        System.out.println("[9] ArrayList<String> 와 ArrayList<Integer> 의 getClass() 가 같나 : "
            + (new ArrayList<String>().getClass() == new ArrayList<Integer>().getClass()));
        new Holder<String>().bump(); new Holder<Integer>().bump();
        System.out.println("[10] Holder<String> 과 Holder<Integer> 를 한 번씩 bump 한 뒤 count : " + Holder.count);
    }
}
===== javac -d j24out j24/Ex24.java && java -cp j24out Ex24 (cc exit=0 · run exit=0) =====
[9] ArrayList<String> 와 ArrayList<Integer> 의 getClass() 가 같나 : true
[10] Holder<String> 과 Holder<Integer> 를 한 번씩 bump 한 뒤 count : 2
===== 격자 — 행;C# 컴파일;Java 결과 =====
1;new T();C# cc exit=0;Java 막힘(javac exit=1)
2;new T[n];C# cc exit=0;Java 막힘(javac exit=1)
3;typeof(T) · T.class;C# cc exit=0;Java 막힘(javac exit=1)
4;o is T · instanceof T;C# cc exit=0;Java 막힘(javac exit=1)
5;o is List<string> · instanceof List<String>;C# cc exit=0;Java 막힘(javac exit=1)
6;타입 인자만 다른 오버로드;C# cc exit=0;Java 막힘(javac exit=1)
7;값 타입 인자 List<int>;C# cc exit=0;Java 막힘(javac exit=1)
8;정적 필드의 타입이 T;C# cc exit=0;Java 막힘(javac exit=1)
9;두 인스턴스화의 런타임 클래스;C# cc exit=0;Java 소거(같은 클래스)
10;정적 필드가 인스턴스화마다 따로;C# cc exit=0;Java 소거(카운터 하나)
Java 에서 막히거나 소거되는 칸 10 / 10
```

**왜 그런가**

- ★★★ **javac 가 받아 준 칸은 없다** — 1\~8 행이 **전부 `javac exit=1`**: `unexpected type` · `generic array creation` · `cannot select from a type variable` · `Object cannot be safely cast to T`·`… to List<String>` · `name clash … same erasure` · `unexpected type`(참조만) · `non-static type variable T …`.
- ★★★ **돌아가는 두 칸도 지워져 있다** — `getClass()` 비교 **`true`**, 정적 카운터 **`2`**(하나를 나눠 썼다). C# 은 **`False`** · **각각 1**.
- ★★ **C# 쪽 `[1]`\~`[10]`** — ``List`1`` · `System.String[]` · `String` · `True False` · `True False` · `si` · `System.Int32` · `1 b` · `False` · `1`·`1`.

### 4. ★★★ **참조 타입끼리만 코드가 같다** — 타입 핸들은 **다르다**

**출력**

```text
===== 소스: cs24b-canon.cs =====
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
===== csc -out:ex.dll cs24b-canon.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] System.__Canon 이 있나 : True
[2] 코드 주소  List<string>.Add == List<object>.Add : True
[3] 코드 주소  List<string>.Add == List<int>.Add    : False
[4] 코드 주소  List<int>.Add    == List<long>.Add   : False
[5] 메서드 핸들 List<string>.Add == List<object>.Add : True
[6] 메서드 핸들 List<int>.Add    == List<long>.Add   : False
[7] 코드 주소  Box<string>.Size == Box<Uri>.Size    : True
[8] 코드 주소  Box<string>.Size == Box<int>.Size    : False
[9] 타입 핸들  Box<string> == Box<Uri>              : False
===== csc -optimize -out:exo.dll cs24b-canon.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] System.__Canon 이 있나 : True
[2] 코드 주소  List<string>.Add == List<object>.Add : True
[3] 코드 주소  List<string>.Add == List<int>.Add    : False
[4] 코드 주소  List<int>.Add    == List<long>.Add   : False
[5] 메서드 핸들 List<string>.Add == List<object>.Add : True
[6] 메서드 핸들 List<int>.Add    == List<long>.Add   : False
[7] 코드 주소  Box<string>.Size == Box<Uri>.Size    : True
[8] 코드 주소  Box<string>.Size == Box<int>.Size    : False
[9] 타입 핸들  Box<string> == Box<Uri>              : False
```

**왜 그런가**

- ★★★ **`[2]` `True` · `[3]` `False` · `[4]` `False`** — 인자가 **둘 다 참조 타입일 때만** JIT 코드가 같다. 값 타입은 `int`·`long` 끼리도 따로다.
- ★★★ **`[5]` 메서드 핸들까지 같다(`True`)** · `[6]` 값 타입은 `False` · `[7]` `Box<string>`·`Box<Uri>` 코드 `True` · `[8]` `Box<int>` 와 `False`.
- ★★★ **`[9]` `Box<string>` 과 `Box<Uri>` 의 타입 핸들은 `False`** — **`[7]` 과 같은 두 타입인데 답이 반대다.** 코드는 하나, 타입은 둘.
- ★ **`[1]` `System.__Canon` 이 있다(`True`)** · **두 판(기본 / `-optimize`+`TC=0`)이 아홉 줄 다 같다.**

### 5. ★★ **`CS0452` · `CS0453` ×2 · `CS0310` · `CS8377` · `CS8714`(경고)**

**출력**

```text
===== 소스: cs24b-cons.cs =====
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
===== csc -nullable:enable -out:ex.dll cs24b-cons.cs 2>&1 | sort (cc exit=1) =====
cs24b-cons.cs(12,11): error CS0452: The type 'int' must be a reference type in order to use it as parameter 'T' in the generic type or method 'C.Ref<T>()'
cs24b-cons.cs(13,11): error CS0453: The type 'string' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'C.Val<T>()'
cs24b-cons.cs(14,11): error CS0453: The type 'int?' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'C.Val<T>()'
cs24b-cons.cs(15,11): error CS0310: 'NoCtor' must be a non-abstract type with a public parameterless constructor in order to use it as parameter 'T' in the generic type or method 'C.New<T>()'
cs24b-cons.cs(16,11): error CS8377: The type 'string' must be a non-nullable value type, along with all fields at any level of nesting, in order to use it as parameter 'T' in the generic type or method 'C.Unm<T>()'
cs24b-cons.cs(18,9): warning CS8714: The type 'string?' cannot be used as type parameter 'T' in the generic type or method 'C.Nn<T>(T)'. Nullability of type argument 'string?' doesn't match 'notnull' constraint.
```

**왜 그런가**

- ★★ **다섯은 에러, `notnull` 의 `CS8714` 만 경고** — `notnull` 은 **널 허용 분석**의 일부다([06번](../06-nullable-reference-types/)).
- ★ **`int?` 는 `CS0453`** — `struct` 제약은 **널 불가** 값 타입만 받는다. `Nullable<int>` 는 구조체지만 제외된다.

### 6. ★★ **24000 · 0 · 48000 · 0** — 갈린 줄 **0 / 4**

**출력**

```text
===== 소스: cs24b-alloc.cs =====
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
===== csc -out:ex.dll cs24b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== csc -out:ex.dll cs24b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs24b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs24b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] ArrayList.Add(i)         1000번 : 24000 바이트
[2] List<int>.Add(i)         1000번 : 0 바이트
[3] SumObj(i, i) object 인자 1000번 : 48000 바이트
[4] Pick<int>(i, i)          1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 4
```

**왜 그런가**

- ★★★ **`ArrayList.Add` 24000 · `SumObj` 48000**(인자 둘을 박싱) 대 **`List<int>.Add` 0 · `Pick<int>` 0**.
- ★★★ **네 판에서 갈린 줄 0 / 4** — [20번](../20-enum-and-flags/)의 `HasFlag` 는 **IL 에 `box` 가 있고 JIT 최적화가 지웠다 말았다** 했다. 여기는 **값 타입 인자마다 따로 JIT** 되므로 **박싱이 IL 에 애초에 없다** — 그래서 판을 안 탄다.

### 7. ★★★ **남는 것은 ECMA-335**, **나눠 쓰는 것은 CoreCLR** — 문서에 있어도 구현은 구현이다

- ★★★ **「구성된 타입이 런타임의 진짜 타입」은 CLI 명세(ECMA-335)** 가 보장한다 — 그래서 `typeof(T)`·`is List<string>`·인자마다의 정적 필드가 **어느 .NET 런타임에서나** 된다.
- ★★★ **코드를 몇 벌 만들지는 명세가 정하지 않는다** — `__Canon` 공유는 **CoreCLR 의 선택**이다. Learn 「런타임의 제네릭」 글이 설명하지만, 그것이 **명세가 되지는 않는다.**
- ★ **4번 `[7]` 과 `[9]`** — 같은 두 타입(`Box<string>`·`Box<Uri>`)이 **코드 주소는 같고 타입 핸들은 다르다.** 「타입은 따로, 코드는 하나」가 한 쌍의 줄로 보인다.

### 8. ★★ 뿌리는 **「Java 런타임은 `T` 를 모른다」** — Kotlin 은 **`inline` + `reified`**

- ★★ 소거 뒤 `T` 는 **`Object`(또는 상한)** 가 되어 런타임에 없다 — 그래서 **런타임에 `T` 를 써야 하는 것**(생성·배열·클래스 토큰·검사·오버로드 구별·정적 필드)이 전부 막힌다([Java 19번](../../../java/syntax/19-type-erasure/)).
- ★★ **Kotlin** 은 `inline fun <reified T>` 로 **부르는 자리에 실제 타입을 박아 넣어** `x is T` 를 연다. 없이 쓰면 **`cannot check for instance of erased type`**([Kotlin 12번](../../../kotlin/syntax/12-reified-type-parameters/) 실측).

### 9. ★★ 정적 필드는 **타입에** 붙고, 타입은 **인자마다 따로**다

- ★★ 코드 공유는 **메서드 본문**의 이야기이고, 정적 필드는 **구성된 타입(`Holder<string>` 과 `Holder<object>` 는 다른 타입 — 4번 `[9]`)** 에 붙는다. 그래서 공유 코드가 **「이 호출의 타입」의 정적 필드**를 찾아간다.
- ★ **쓸모** — 타입마다 하나인 캐시(`static class Cache<T>`)가 사전·자물쇠 없이 된다. **함정** — 전역 하나여야 할 카운터를 제네릭 클래스에 두면 **인자마다 쪼개진다.**

### 10. ★ Rust 는 **인자마다 전부 따로**(단형화) — Go 는 **이 판에서 확인 안 했다**

- ★ **Rust** — 타입 인자마다 코드를 **따로 찍는다**([Rust 31번](../../../rust/syntax/31-generics-trait-bounds-where-and-monomorphization/)). .NET 은 **값 타입만** 따로이고 참조 타입은 공유한다.
- ★ **Go** — 메모리 모양(GC shape)이 같은 인자끼리 코드를 나눈다고 **알려져 있다** — .NET 과 같은 계열의 절충이다. **이 판에서 던지지 않았고**, Go 갈래 목록의 **37번**은 아직 폴더가 없다.

### 11. 잇기

- ★★ **박싱과 `List<int>` 대 `ArrayList`(한 판)** — [03번](../03-boxing-and-unboxing/) (4).
- ★★ **제약 선택 기준 · `default(T)`** — 목록의 **25번 주제**.
- ★ **Java 소거의 결과** — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **19번**([`19-type-erasure/`](../../../java/syntax/19-type-erasure/)).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs24b-refl.cs` 리플렉션 | csc 1회 · 실행 1회 | ★★★ 타입 인자까지 구별 · `new T[n]` 은 진짜 배열 · 정적 필드 인자마다 |
| `cs24b-il.cs` IL | csc 1회 · 실행 1회 | ★★ `ldtoken`·`newarr`·`initobj`·`isinst T` · `Activator::CreateInstance` |
| `cs24b-grid.cs` + `G1`\~`G8.java` + `Ex24.java` | csc 2회 · javac 9회(+격자 8회) · java 2회 | ★★★ **Java 에서 막히거나 소거되는 칸 10 / 10** |
| `cs24b-canon.cs` 코드 공유 | csc 2회 · 실행 2회(기본 · `-optimize`+`TC=0`) | ★★★ 참조 타입끼리 코드·핸들 같음 · 값 타입 다름 · 타입 핸들 다름 |
| `cs24b-cons.cs` 제약 위반 | csc 1회 | `CS0452`·`CS0453`×2·`CS0310`·`CS8377`·`CS8714` |
| `cs24b-alloc.cs` | **2×2 판 격자** | ★★★ 24000 · 0 · 48000 · 0 · **갈린 줄 0 / 4** |
| `cs24b-form.cs` 형태 | csc 1회 · 실행 1회 | `2 · 1 · 7 · banana` · ``List`1<Int32>`` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12 · javac 21.0.5)에서만** 그렇다.

- ★★★ **`__Canon` 공유 · 값 타입 따로 JIT** — CoreCLR 구현. 다른 런타임(NativeAOT 등)은 안 던졌다.
- ★★ **`new T()` 가 `Activator::CreateInstance`** — Roslyn · **할당 바이트 값**.

**언어·CLI 가 보장하는 것**(구현이 바뀌어도 같다)

- **구성된 타입은 런타임의 진짜 타입**(ECMA-335) · **정적 필드는 구성된 타입마다** · **제약 위반은 컴파일 에러**(`notnull` 제외).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **제네릭 메서드의 코드 공유**(인스턴스화 스텁) · ★ **NativeAOT** · ★ **공유 코드가 `T` 를 찾는 사전** · ★ **Kotlin·Rust·Go 를 이 판에서 직접**.
- **못 잰 것** — ★★ **JIT 코드의 내용** — 주소가 같은지만 봤지 어셈블리를 찍지 않았다. ★★★ **시간** — 한 줄도 안 쟀다.
- **잴 것이 없는 것** — 없다. 네 창을 다 썼다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **4번** — 공유 정책은 구현이다. **참조 타입 공유가 바뀌면 `[2]`·`[5]`·`[7]` 이 움직인다.**
- ★★ **6번 판 격자** — 값은 판을 안 탔지만 다시 2×2 로.
- ★ **1·2·3번** — 명세가 정한 것이라 바뀔 일이 없다. Java 쪽은 **원시 타입을 타입 인자로 받게 되면 7행이 바뀔 수 있다** — 그때 다시 던져라.
