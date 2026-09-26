# csharp/syntax/36 — `IQueryable` 과 식 트리 맛보기 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> **기준 소스** — ★ **SDK 참조 팩의 XML 문서**(로컬에서 열어 확인) — `System.Linq.Expressions.xml`: `Expression<TDelegate>` 「강하게 타입이 붙은 람다 식을 **식 트리 형태의 자료 구조**로 나타낸다」 · `Compile` 「식 트리가 묘사하는 람다 식을 **실행 가능한 코드로 컴파일**해 델리게이트를 만든다」 · `IQueryable.Expression` 「이 인스턴스에 딸린 식 트리를 얻는다」 · `IQueryProvider` 「`IQueryable` 이 묘사하는 쿼리를 **만들고 실행하는** 메서드를 정의한다」 · `CreateQuery<T>` 「식 트리가 나타내는 쿼리를 **평가할 수 있는** `IQueryable<T>` 를 만든다」 · `Execute<TResult>` 「식 트리가 나타내는 쿼리를 **실행한다**」 ·\
> `System.Linq.Queryable.xml`: `EnumerableQuery<T>` 「`IEnumerable<T>` 컬렉션을 `IQueryable<T>` 데이터 원본으로 나타낸다」.
> ★★★ **ORM 은 설치하지 않았다**(NuGet 없음 · 외부 네트워크 없음). EF Core 의 문서도 **열지 않았다.** 그래서 이 문서의 「ORM 에서 쿼리가 나가는 지점」은 **직접 짠 장난감 공급자**로 보인 **모양**이다((3)) — EF Core 가 그 지점에서 무엇을 하는지는 **재지도 인용하지도 않는다.**
> **실행 검증** — 이 문서의 모든 출력·진단·IL 은 아래 「이 판」의 도구로 **실제로 돌려 얻은 것**이다(2026-09-26). 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣었다.
> **버전** — 식 트리로 바꿀 **람다 자체가 C# 3** 이다([33번](../33-linq-method-syntax-and-deferred-execution/) (6) — `-langversion:2` 의 람다 `CS8023`). ★ 식 트리 변환만 따로 판 경계를 재지는 않았다 · 라이브러리 쪽 판은 참조 팩이 10.0.12 하나뿐이라 **확인 못 함.**
> **경계** — ★★★ **`Enumerable` 쪽 연산자가 즉시냐 지연이냐는 [33번](../33-linq-method-syntax-and-deferred-execution/)** 이 정본이다. 여기는 **같은 모양의 쿼리가 `Queryable` 쪽에 도착하면 무엇이 다른가** 하나다.\
> ★★ 람다가 **델리게이트**가 되는 IL(`ldftn` · `newobj Func`)은 [27번](../27-delegates-and-func-action/) · [28번](../28-lambdas-and-closure-capture/) (1)이 정본이다 — 여기서는 **같은 람다가 식 트리가 되면 IL 이 어떻게 달라지나**만 본다.\
> ★ 「`OrderBy(…).First()` 가 정렬을 건너뛴다」([33번](../33-linq-method-syntax-and-deferred-execution/) (1-b))처럼 **연산자가 뒤에 붙은 것을 알아보는** 일을, `IQueryable` 은 **식 트리 전체를 공급자에게 넘기는** 방식으로 일반화한다 — (3)이 그 모양이다.
> ★★★ **본체 창은 둘이다 — ① IL(「같은 람다가 무엇으로 컴파일되나」)과 ⑤ 장난감 공급자의 로그(「번역·실행은 언제 불리나」).**
>
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | IL **오프셋** · 컴파일러가 지은 이름(`<>9__0_0` · `<AsFunc>b__0_0`) · 진단 **문구** · 진단 **순서**(배너에 `sort`) | ★★★ **옵코드와 호출 대상**(`ldftn` · `newobj Func` 대 `call Expression::Parameter` · `Expression::GreaterThan` · `Expression::Lambda` · `Enumerable::Where` 대 `Queryable::Where`) · **진단 코드** |
> | 식 트리 노드의 **내부 클래스 이름**(찍지 않았다 — `NodeType` 만 찍었다) | ★★★ **`NodeType`**(`Lambda` · `GreaterThan` · `Call` · `Quote` …) · `ToString()` · **공급자 로그의 `CreateQuery`/`Execute` 수 · 「Execute 가 불린 단계 N / M」 · 「막힌 칸 N / M」** |

## 이 판

```text
===== dotnet --version && dotnet --list-runtimes | grep NETCore (exit=0) =====
10.0.401
Microsoft.NETCore.App 10.0.12 [/home/jun/.local/opt/dotnet/shared/Microsoft.NETCore.App]
===== javac -version (exit=0) =====
javac 21.0.5
===== java -version (exit=0) =====
openjdk version "21.0.5" 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

## 이 갈래가 쓰는 세 층

| 층 | 뜻 | 이 주제에서 근거로 쓰는 것 |
|---|---|---|
| **언어 명세(ECMA-334)** | ★★★ C# 언어가 약속한 것 | ★★★ **람다는 목표 타입이 델리게이트면 델리게이트로, `Expression<TDelegate>` 면 식 트리로 변환된다** · 식 트리로 못 바꾸는 람다(문 본문 등)는 **컴파일 에러** · `s.Where(…)` 가 **정적 타입**에 따라 `Enumerable` / `Queryable` 로 갈리는 것(오버로드 해석 — [30번](../30-extension-methods-and-extension-members/)) |
| **컴파일러 구현(Roslyn)** | ★★ 그것을 **어떻게 적나** | ★★ 식 트리 람다가 **`Expression.Parameter`·`Constant`·`GreaterThan`·`Lambda` 호출 사슬**이 되는 것 · 그 사슬에 **캐시 필드가 없는 것**(부를 때마다 새 트리) · 진단 코드 배정 |
| **BCL 계약(XML 문서)** | ★★ 문서가 약속한 것 | ★★ `IQueryProvider` = **만들기(`CreateQuery`)와 실행(`Execute`)** · `Expression<T>` = 자료 구조 · `Compile` = 실행 가능한 코드로 |
| **이 판의 관찰 · 장난감** | .NET 10.0.12 · linux-x64 | ★★★ **`Execute` 가 불리는 단계**(장난감 공급자 — ★ **내가 짠 것**이라 「ORM 이 그렇다」의 근거가 아니다 · 「`IQueryable` 계약이 그 지점을 준다」의 근거다) |

★★★ **이 주제의 층 구분이 급소다 —**\
**「번역이 언제 일어나나」는 두 층이 나눠 가진다.** `Where` 를 이을 때 **`CreateQuery` 가 불린다**는 것은 `Queryable.Where` 의 구현이 정하고(★ 문서 요약은 「평가할 수 있는 `IQueryable` 을 만든다」까지), **`Execute` 에서 무엇을 하나**(SQL 로 번역 · 거부 · 메모리 실행)는 **공급자마다 다르다.** 장난감은 뒤쪽을 **내가** 정했다 — 그러니 (3)이 증명하는 것은 **「연산자를 잇는 동안 공급자에게 오는 것은 `CreateQuery`(새 쿼리를 만들어라)뿐이고, 결과를 달라는 요청은 결과를 요구하는 연산에서만 온다」** 쪽이지, 「어떤 ORM 이 거기서 SQL 을 보낸다」가 아니다. ★ `CreateQuery` 도 공급자의 코드이니 **거기서 무언가를 할 수는 있다** — 다만 결과를 내라는 요청이 아니다.

## 한눈에 — 쉽게 말하면

**`IEnumerable` 에 넘긴 람다는 「실행 파일」이고, `IQueryable` 에 넘긴 람다는 「설계도」다 — 실행 파일은 내 컴퓨터에서 돌 뿐이지만, 설계도는 받은 쪽(공급자)이 읽고 자기 공장(DB)의 언어로 다시 짤 수 있다.**

- **실행 파일(`Func<int,bool>`)** — 컴파일러가 람다 몸을 **메서드**로 만들고 그 주소를 델리게이트에 담는다. 받는 쪽은 **부를 수만** 있고 **안을 못 읽는다**((1)).
- **설계도(`Expression<Func<int,bool>>`)** — 컴파일러가 람다를 **「매개변수 x · 상수 2 · 둘을 `>` 로」라는 노드 조립 코드**로 바꾼다. 받는 쪽은 그 노드를 **읽을 수 있다**((1)(2)).
- **설계도를 쌓기만(`Where` 잇기)** — `IQueryable` 에 `Where` 를 이으면 설계도에 **노드가 붙을 뿐** — 공장에는 「새 설계도를 받아 둬라」(`CreateQuery`)만 가고 **「만들어 달라」(`Execute`)는 안 간다**((3)).
- **주문 넣기(`ToList`·`Count`·`First`·`foreach`)** — 그제서야 공급자가 설계도 **전체**를 받아 번역하고 실행한다(`Execute` 1)((3)).
- **공장에 없는 부품(내 C# 메서드)** — 설계도에 `IsOdd(x)` 가 들어 있으면 공장이 **번역을 못 한다.** 그런데 그걸 아는 것도 **주문을 넣을 때**다((3)).
- **설계도에 못 그리는 것** — 문 본문 람다 · 대입 · `?.` · `switch` 식 … 은 **컴파일러가 설계도를 거부**한다((4)).

| 비유 | 실체 | 어디서 보나 |
|---|---|---|
| 실행 파일 | ★★★ `AsFunc` IL — **`ldftn <AsFunc>b__0_0` · `newobj Func<Int32,Boolean>`** · 캐시 필드 | (1) |
| 설계도 | ★★★ `AsTree` IL — **`Expression::Parameter` → `Constant` → `GreaterThan` → `Lambda<Func<Int32,Boolean>>`** · 람다 메서드가 **없다** | (1) |
| 같은 글자, 다른 목적지 | ★★★ `s.Where(x => x > 2)` — `IEnumerable<int>` 면 **`Enumerable::Where`**, `IQueryable<int>` 면 **설계도를 만든 뒤 `Queryable::Where`** | (1) |
| 설계도를 읽는다 | ★★ `Lambda` → `Parameter` · `GreaterThan` → `Parameter` · `Constant` · `q.Expression` 에 **`Call · Queryable.Where`** | (2) |
| 쌓기만 | ★★★ `Where` 두 번 → **`CreateQuery` 1 · `Execute` 0** 씩 | (3) |
| 주문 넣기 | ★★★ `ToList`·`Count()`·`First()`·`foreach` → **`Execute` 1** — **Execute 가 불린 단계 9 / 12** | (3) |
| 없는 부품 | ★★★ `Where(x => IsOdd(x))` → **만들 때 통과** · `ToList()` 때 **`NotSupportedException — 번역 못 함: 메서드 Program.IsOdd`** | (3) |
| 설계도에 못 그림 | ★★★ **막힌 칸 8 / 20** — `Func` 열은 전부 `ok`, `Expression` 열 여덟이 막힌다(`CS0834` …) | (4) |

★★★ **이 주제의 본체 그림 — 같은 람다, 두 목적지.**

```text
   소스:  s.Where(x => x > 2)

   s 의 정적 타입이 IEnumerable<int>                    s 의 정적 타입이 IQueryable<int>
   ─────────────────────────────────────                ────────────────────────────────────────────────
   람다 → 메서드 <…>b__N_0 (컴파일된 코드)                람다 → 노드를 만드는 코드 (메서드 없음)
          ldftn · newobj Func<int,bool>                        Expression.Parameter(typeof(int), "x")
   call Enumerable.Where(s, func)                              Expression.Constant(2, typeof(int))
          │                                                    Expression.GreaterThan(x, 2)
          ▼                                                    Expression.Lambda<Func<int,bool>>(…, x)
   WhereIterator — 열거할 때 func 를 부른다               call Queryable.Where(s, tree)
   (33편의 세계)                                                 │
                                                                ▼
                                                         s.Provider.CreateQuery(  Call(Where, s.Expression, Quote(tree))  )
                                                         — 새 IQueryable: 식 트리가 한 겹 두꺼워졌을 뿐, 실행 없음
                                                                │  ToList · Count · First · foreach
                                                                ▼
                                                         s.Provider.Execute( 식 트리 전체 )   ← 여기서만 번역·실행 (3)

   ★★★ 두 갈래를 가르는 것은 람다가 아니라 「s 의 정적 타입」 이다 — (3) [8] 에서 IEnumerable<int> 로 받자 WHERE 가 사라졌다.
```

## 이 주제가 답하려는 질문

1. **같은 람다가 `Func` 과 `Expression` 에서 무엇으로 컴파일되나 — `Where` 는 어디로 가나**((1)).
2. **식 트리는 어떤 자료인가 — `IQueryable` 에 `Where` 를 이으면 무엇이 쌓이나**((2)).
3. **공급자는 언제 불리나 — 번역·실행·거부가 일어나는 지점은**((3)) · **`AsEnumerable` 로 끊으면**((3)).
4. **어떤 람다는 식 트리가 될 수 없나**((4)).

## 동작 방식

### (0) 이 주제가 쓰는 창

★★★ **본체 창은 ① IL + ⑤ 장난감 공급자 로그다.**

| 창 | 무엇을 보여 주나 | 이 주제에서 |
|---|---|---|
| ★★★ **① IL 덤프** | ★★★ 델리게이트 생성(`ldftn`·`newobj`) 대 **`Expression` 팩토리 호출 사슬** · `Enumerable::Where` 대 `Queryable::Where` | (1) |
| ★★★ **⑤ 장난감 공급자 로그** | ★★★ 단계마다 **`CreateQuery` 수 · `Execute` 수 · 공급자가 만든 번역 문자열** · 거부 예외 · **「Execute 가 불린 단계 N / M」** | (3) |
| ★★ **③ 리플렉션(식 트리 순회)** | ★★ 노드의 `NodeType`·`Type`·`ToString()` · `Call` 노드의 **어느 클래스의 어느 메서드**인가 | (2) |
| ★★★ **② 진단 격자** | ★★★ 같은 본문 열 가지 × `Func`/`Expression` — **막힌 칸 N / M** | (4) |
| **④ 할당 바이트 · 시간** | ★★★ **안 쟀다** — 「`IQueryable` 이 DB 에서 빠르다」는 **이 문서가 잰 것이 아니다.** 잰 것은 **「어디서 걸러지나」**((3) `[8]` 의 `WHERE` 유무)다. 거기서 오가는 행 수의 차이가 곧 시간 차이인지는 **DB 가 있어야** 잰다 — 못 잰 것 | — |
| **부적용인 창** | 없다 | — |

### (1) ★★★ 본체 — 같은 람다를 `Func` 과 `Expression` 에 · `Where` 는 어디로 가나

**언제 쓰나** — 「`Func<T,bool>` 을 받는 저장소 메서드를 만들었더니 **DB 에서 안 거르고 전부 가져온다**」 · 「`Expression<…>` 은 **무엇이 다르길래** 번역되나」.

```text
===== 소스: cs36b-il.cs =====
using System;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;
public static class L {
    public static Func<int, bool> AsFunc() => x => x > 2;
    public static Expression<Func<int, bool>> AsTree() => x => x > 2;
    public static IEnumerable<int> OnEnumerable(IEnumerable<int> s) => s.Where(x => x > 2);
    public static IQueryable<int> OnQueryable(IQueryable<int> s) => s.Where(x => x > 2);
}
class Program {
    static void Main() {
        Il.Dump(typeof(L), "AsFunc");
        Il.Dump(typeof(L), "AsTree");
        Il.Dump(typeof(L), "OnEnumerable");
        Il.Dump(typeof(L), "OnQueryable");
    }
}
===== csc -optimize -r:il.dll -out:exo.dll cs36b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- L.AsFunc ---
  IL_0000: ldsfld L+<>c::<>9__0_0
  IL_0005: dup
  IL_0006: brtrue.s IL_001f
  IL_0008: pop
  IL_0009: ldsfld L+<>c::<>9
  IL_000e: ldftn L+<>c::<AsFunc>b__0_0
  IL_0014: newobj System.Func<System.Int32,System.Boolean>::.ctor
  IL_0019: dup
  IL_001a: stsfld L+<>c::<>9__0_0
  IL_001f: ret
--- L.AsTree ---
  .locals [0] System.Linq.Expressions.ParameterExpression
  IL_0000: ldtoken System.Int32
  IL_0005: call System.Type::GetTypeFromHandle
  IL_000a: ldstr "x"
  IL_000f: call System.Linq.Expressions.Expression::Parameter
  IL_0014: stloc.0
  IL_0015: ldloc.0
  IL_0016: ldc.i4.2
  IL_0017: box System.Int32
  IL_001c: ldtoken System.Int32
  IL_0021: call System.Type::GetTypeFromHandle
  IL_0026: call System.Linq.Expressions.Expression::Constant
  IL_002b: call System.Linq.Expressions.Expression::GreaterThan
  IL_0030: ldc.i4.1
  IL_0031: newarr System.Linq.Expressions.ParameterExpression
  IL_0036: dup
  IL_0037: ldc.i4.0
  IL_0038: ldloc.0
  IL_0039: stelem.ref
  IL_003a: call System.Linq.Expressions.Expression::Lambda<System.Func<System.Int32,System.Boolean>>
  IL_003f: ret
--- L.OnEnumerable ---
  IL_0000: ldarg.0
  IL_0001: ldsfld L+<>c::<>9__2_0
  IL_0006: dup
  IL_0007: brtrue.s IL_0020
  IL_0009: pop
  IL_000a: ldsfld L+<>c::<>9
  IL_000f: ldftn L+<>c::<OnEnumerable>b__2_0
  IL_0015: newobj System.Func<System.Int32,System.Boolean>::.ctor
  IL_001a: dup
  IL_001b: stsfld L+<>c::<>9__2_0
  IL_0020: call System.Linq.Enumerable::Where<System.Int32>
  IL_0025: ret
--- L.OnQueryable ---
  .locals [0] System.Linq.Expressions.ParameterExpression
  IL_0000: ldarg.0
  IL_0001: ldtoken System.Int32
  IL_0006: call System.Type::GetTypeFromHandle
  IL_000b: ldstr "x"
  IL_0010: call System.Linq.Expressions.Expression::Parameter
  IL_0015: stloc.0
  IL_0016: ldloc.0
  IL_0017: ldc.i4.2
  IL_0018: box System.Int32
  IL_001d: ldtoken System.Int32
  IL_0022: call System.Type::GetTypeFromHandle
  IL_0027: call System.Linq.Expressions.Expression::Constant
  IL_002c: call System.Linq.Expressions.Expression::GreaterThan
  IL_0031: ldc.i4.1
  IL_0032: newarr System.Linq.Expressions.ParameterExpression
  IL_0037: dup
  IL_0038: ldc.i4.0
  IL_0039: ldloc.0
  IL_003a: stelem.ref
  IL_003b: call System.Linq.Expressions.Expression::Lambda<System.Func<System.Int32,System.Boolean>>
  IL_0040: call System.Linq.Queryable::Where<System.Int32>
  IL_0045: ret
```

- ★★★ **`AsFunc` — `ldsfld <>9__0_0` · `ldftn <AsFunc>b__0_0` · `newobj Func<Int32,Boolean>::.ctor`** — 람다 몸 `x > 2` 는 **`<AsFunc>b__0_0` 이라는 메서드**로 따로 컴파일됐고, IL 은 그 **주소**로 델리게이트를 만들 뿐이다. 캐시 필드에 담아 두 번째부터는 재사용한다([28번](../28-lambdas-and-closure-capture/) (1)).
- ★★★ **`AsTree` — `ldtoken Int32` · `ldstr "x"` · `call Expression::Parameter` · `ldc.i4.2` · `box Int32` · `call Expression::Constant` · `call Expression::GreaterThan` · `newarr ParameterExpression` · `call Expression::Lambda<Func<Int32,Boolean>>`** — `x > 2` 가 **코드가 아니라 「노드를 조립하는 호출」** 이 됐다. `ldftn` 이 **없다** — 몸을 컴파일한 메서드가 없다. 받는 쪽이 갖는 것은 **부를 수 있는 함수가 아니라 읽을 수 있는 자료**다(XML 의 「자료 구조」).
- ★★ **`AsTree` 에는 캐시 필드(`ldsfld`/`stsfld`)가 없다** — 부를 때마다 **노드를 새로** 만든다(이 판 Roslyn · 할당은 안 쟀다).
- ★★★ **`OnEnumerable` 과 `OnQueryable` 은 소스 글자가 `s.Where(x => x > 2)` 로 같다** — 그런데 앞쪽은 델리게이트를 만들어 **`call Enumerable::Where<Int32>`**, 뒤쪽은 `AsTree` 와 **똑같은 조립 사슬**을 돈 뒤 **`call Queryable::Where<Int32>`** 다. **람다가 무엇이 될지는 람다가 아니라 받는 쪽의 매개변수 타입**(`Func` 대 `Expression<Func>`)이 정하고, 어느 `Where` 가 불릴지는 **`s` 의 정적 타입**이 정한다.

### (2) ★★ 식 트리는 데이터다 — 노드 덤프 · `AsQueryable` 에 `Where` 를 이으면

```text
===== 소스: cs36b-tree.cs =====
using System;
using System.Linq;
using System.Linq.Expressions;
class Program {
    static void Walk(Expression e, int d) {
        string extra = e is MethodCallExpression m ? $" · {m.Method.DeclaringType!.Name}.{m.Method.Name}" : "";
        Console.WriteLine($"{new string(' ', d * 2)}{e.NodeType} ({e.Type.Name}){extra} : {e}");
        switch (e) {
            case LambdaExpression l: foreach (var p in l.Parameters) Walk(p, d + 1); Walk(l.Body, d + 1); break;
            case BinaryExpression b: Walk(b.Left, d + 1); Walk(b.Right, d + 1); break;
            case MethodCallExpression c: foreach (var a in c.Arguments) Walk(a, d + 1); break;
            case UnaryExpression u: Walk(u.Operand, d + 1); break;
        }
    }
    static void Main() {
        Expression<Func<int, bool>> t = x => x > 2;
        Console.WriteLine($"[1] t.ToString() = {t}");
        Walk(t, 1);
        Func<int, bool> f = t.Compile();
        Console.WriteLine($"[2] t.Compile()(5) = {f(5)} · t.Compile()(1) = {f(1)}");
        var q = new[] { 1, 2, 3, 4 }.AsQueryable().Where(x => x > 2).Select(x => x * 10);
        Console.WriteLine($"[3] q 의 타입 {q.GetType().Name} · Provider {q.Provider.GetType().Name}");
        Console.WriteLine($"[4] q.Expression = {q.Expression}");
        Walk(q.Expression, 1);
        Console.WriteLine($"[5] q 를 돌리면 [{string.Join(", ", q)}]");
    }
}
===== csc -out:ex.dll cs36b-tree.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] t.ToString() = x => (x > 2)
  Lambda (Func`2) : x => (x > 2)
    Parameter (Int32) : x
    GreaterThan (Boolean) : (x > 2)
      Parameter (Int32) : x
      Constant (Int32) : 2
[2] t.Compile()(5) = True · t.Compile()(1) = False
[3] q 의 타입 EnumerableQuery`1 · Provider EnumerableQuery`1
[4] q.Expression = System.Int32[].Where(x => (x > 2)).Select(x => (x * 10))
  Call (IQueryable`1) · Queryable.Select : System.Int32[].Where(x => (x > 2)).Select(x => (x * 10))
    Call (IQueryable`1) · Queryable.Where : System.Int32[].Where(x => (x > 2))
      Constant (EnumerableQuery`1) : System.Int32[]
      Quote (Expression`1) : x => (x > 2)
        Lambda (Func`2) : x => (x > 2)
          Parameter (Int32) : x
          GreaterThan (Boolean) : (x > 2)
            Parameter (Int32) : x
            Constant (Int32) : 2
    Quote (Expression`1) : x => (x * 10)
      Lambda (Func`2) : x => (x * 10)
        Parameter (Int32) : x
        Multiply (Int32) : (x * 10)
          Parameter (Int32) : x
          Constant (Int32) : 10
[5] q 를 돌리면 [30, 40]
```

- ★★★ **`[1]` `t.ToString()` = `x => (x > 2)`** · 노드 — **``Lambda (Func`2)`` 아래 `Parameter (Int32) x` 와 `GreaterThan (Boolean)`, 그 아래 `Parameter` · `Constant (Int32) 2`.** (1)의 IL 이 조립한 것이 **이 나무**다.
- ★★ **`[2]` `t.Compile()`** — 설계도를 **실행 파일로** 바꾼다(XML 「실행 가능한 코드로 컴파일」). `5 → True` · `1 → False`.
- ★★★ **`[3]` `AsQueryable()` 의 결과는 ``EnumerableQuery`1`` · 공급자도 ``EnumerableQuery`1``** — 메모리 컬렉션을 `IQueryable` 로 **포장**한 것이다(XML 「`IEnumerable<T>` 를 `IQueryable<T>` 데이터 원본으로」).
- ★★★ **`[4]` `q.Expression` = `System.Int32[].Where(x => (x > 2)).Select(x => (x * 10))`** — `Where`·`Select` 를 이은 것이 **실행이 아니라 나무**로 쌓였다. 뿌리가 **`Call · Queryable.Select`**, 그 첫 인자가 **`Call · Queryable.Where`**, 그 첫 인자가 **``Constant (EnumerableQuery`1)``**(원본). 람다는 **`Quote`** 에 싸여 **나무째** 들어 있다.
- ★★ **`[5]` 돌리면 `[30, 40]`** — `EnumerableQuery` 공급자는 이 나무를 **`Enumerable` 쪽으로 바꿔 메모리에서** 돌린다(★ 그렇게 읽힌다 — 공급자 내부는 열어 보지 않았다).

### (3) ★★★ 본체 — 장난감 공급자: 번역은 어느 단계에서 불리나

**언제 쓰나** — 「ORM 쿼리를 **어디까지 쌓아도** DB 에 안 가나」 · 「번역 못 하는 메서드를 넣으면 **어디서** 터지나」 · 「`IEnumerable` 로 받는 순간 무엇이 바뀌나」.

★ **장난감의 규칙**(`cs36b-toy.cs` 의 `ToyProvider`) — `CreateQuery` 는 로그만 남기고 새 `ToyQuery` 를 돌려준다. `Execute` 는 로그를 남기고 **식 트리를 SQL 비슷한 문자열로 번역**한 뒤, 번역한 조건으로만 메모리 표 `{1,2,3,4,5}` 를 거른다. 번역할 줄 아는 것은 **`Where`(`>` · `<` · 상수 · 캡처된 변수) · `Count` · `First`** 뿐이고, 나머지는 **`NotSupportedException`** 이다. **이 규칙은 내가 정한 것**이다 — 실제 ORM 의 규칙이 아니다.

```text
===== 소스: cs36b-toy.cs =====
using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Linq.Expressions;

// 장난감 공급자 — 식 트리를 SQL 비슷한 문자열로 번역하고, 번역한 조건으로만 메모리 표를 거른다.
class ToyProvider : IQueryProvider {
    public static readonly List<string> log = new();
    readonly int[] table;
    public ToyProvider(int[] table) { this.table = table; }
    public IQueryable CreateQuery(Expression e) => throw new NotSupportedException("비제네릭 CreateQuery");
    public IQueryable<T> CreateQuery<T>(Expression e) { log.Add("CreateQuery"); return new ToyQuery<T>(this, e); }
    public object Execute(Expression e) => throw new NotSupportedException("비제네릭 Execute");
    public TResult Execute<TResult>(Expression e) {
        log.Add("Execute");
        var (sql, preds, tail) = Translate(e);
        log.Add($"번역: {sql}");
        var rows = table.Where(x => preds.All(p => p(x)));
        object r = tail switch { "Count" => rows.Count(), "First" => rows.First(), _ => rows.ToList() };
        return (TResult)r;
    }
    static (string, List<Func<int, bool>>, string) Translate(Expression e) {
        var conds = new List<string>(); var preds = new List<Func<int, bool>>(); string tail = "";
        while (e is MethodCallExpression m) {
            switch (m.Method.Name) {
                case "Where":
                    var lam = (LambdaExpression)((UnaryExpression)m.Arguments[1]).Operand;
                    conds.Insert(0, Cond(lam.Body));
                    preds.Insert(0, (Func<int, bool>)lam.Compile());
                    break;
                case "Count": case "First": tail = m.Method.Name; break;
                default: throw new NotSupportedException($"번역 못 함: 연산자 {m.Method.Name}");
            }
            e = m.Arguments[0];
        }
        string select = tail == "Count" ? "COUNT(*)" : tail == "First" ? "TOP 1 x" : "x";
        string where = conds.Count == 0 ? "" : " WHERE " + string.Join(" AND ", conds);
        return ($"SELECT {select} FROM t{where}", preds, tail);
    }
    static string Cond(Expression b) => b switch {
        BinaryExpression { NodeType: ExpressionType.GreaterThan } g => $"{Cond(g.Left)} > {Cond(g.Right)}",
        BinaryExpression { NodeType: ExpressionType.LessThan } g => $"{Cond(g.Left)} < {Cond(g.Right)}",
        ParameterExpression => "x",
        ConstantExpression c => $"{c.Value}",
        MemberExpression { Expression: ConstantExpression } mm => $"{Expression.Lambda(mm).Compile().DynamicInvoke()}",
        MethodCallExpression mc => throw new NotSupportedException($"번역 못 함: 메서드 {mc.Method.DeclaringType!.Name}.{mc.Method.Name}"),
        _ => throw new NotSupportedException($"번역 못 함: 노드 {b.NodeType}"),
    };
}
class ToyQuery<T> : IQueryable<T> {
    readonly ToyProvider p;
    public ToyQuery(ToyProvider p, Expression? e = null) { this.p = p; Expression = e ?? Expression.Constant(this); }
    public Type ElementType => typeof(T);
    public Expression Expression { get; }
    public IQueryProvider Provider => p;
    public IEnumerator<T> GetEnumerator() => p.Execute<List<T>>(Expression).GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
    public override string ToString() => "t";
}
class Program {
    static bool IsOdd(int x) => x % 2 == 1;
    static int steps, executed;
    static void Step(string label, Func<object?> f) {
        ToyProvider.log.Clear();
        string r;
        try {
            var v = f();
            r = v is IQueryable ? "(IQueryable)" : v is IEnumerable e ? "[" + string.Join(",", e.Cast<object>()) + "]" : $"{v}";
        }
        catch (Exception e) { r = $"{e.GetType().Name} — {e.Message}"; }
        int c = ToyProvider.log.Count(l => l == "CreateQuery"), x = ToyProvider.log.Count(l => l == "Execute");
        steps++; if (x > 0) executed++;
        string[] cells = { label, c.ToString(), x.ToString(), r, string.Join(" / ", ToyProvider.log.Where(l => l.StartsWith("번역"))) };
        if (cells.Length != 5) throw new Exception("칸 수 어긋남");
        Console.WriteLine(string.Join("\t", cells));
    }
    static void Main() {
        var db = new ToyQuery<int>(new ToyProvider(new[] { 1, 2, 3, 4, 5 }));
        IQueryable<int> q = null!;
        int min = 1;
        Console.WriteLine(string.Join("\t", "단계", "CreateQuery", "Execute", "결과", "공급자가 만든 번역"));
        Step("[1] q = db.Where(x => x > min)", () => q = db.Where(x => x > min));
        Step("[2] q = q.Where(x => x < 5)", () => q = q.Where(x => x < 5));
        Step("[3] q.ToList()", () => q.ToList());
        Step("[4] q.Count()", () => q.Count());
        Step("[5] q.First()", () => q.First());
        Step("[6] foreach (var x in q)", () => { var s = new List<int>(); foreach (var x in q) s.Add(x); return s; });
        Step("[7] min = 3; q.ToList()", () => { min = 3; return q.ToList(); });
        Step("[8] IEnumerable<int> e = db; e.Where(x => x > 1).ToList()", () => { IEnumerable<int> e = db; return e.Where(x => x > 1).ToList(); });
        Step("[9] q = db.Where(x => IsOdd(x))", () => q = db.Where(x => IsOdd(x)));
        Step("[10] q.ToList()", () => q.ToList());
        Step("[11] db.Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList()", () => db.Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList());
        Step("[12] db.Select(x => x * 10).ToList()", () => db.Select(x => x * 10).ToList());
        Console.WriteLine($"Execute 가 불린 단계 {executed} / {steps}");
    }
}
===== csc -nullable:enable -out:ex.dll cs36b-toy.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
단계	CreateQuery	Execute	결과	공급자가 만든 번역
[1] q = db.Where(x => x > min)	1	0	(IQueryable)	
[2] q = q.Where(x => x < 5)	1	0	(IQueryable)	
[3] q.ToList()	0	1	[2,3,4]	번역: SELECT x FROM t WHERE x > 1 AND x < 5
[4] q.Count()	0	1	3	번역: SELECT COUNT(*) FROM t WHERE x > 1 AND x < 5
[5] q.First()	0	1	2	번역: SELECT TOP 1 x FROM t WHERE x > 1 AND x < 5
[6] foreach (var x in q)	0	1	[2,3,4]	번역: SELECT x FROM t WHERE x > 1 AND x < 5
[7] min = 3; q.ToList()	0	1	[4]	번역: SELECT x FROM t WHERE x > 3 AND x < 5
[8] IEnumerable<int> e = db; e.Where(x => x > 1).ToList()	0	1	[2,3,4,5]	번역: SELECT x FROM t
[9] q = db.Where(x => IsOdd(x))	1	0	(IQueryable)	
[10] q.ToList()	0	1	NotSupportedException — 번역 못 함: 메서드 Program.IsOdd	
[11] db.Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList()	1	1	[3,5]	번역: SELECT x FROM t WHERE x > 1
[12] db.Select(x => x * 10).ToList()	1	1	NotSupportedException — 번역 못 함: 연산자 Select	
Execute 가 불린 단계 9 / 12
```

- ★★★ **Execute 가 불린 단계 9 / 12** — 스크립트가 셌다. 안 불린 셋은 **`[1]`·`[2]`·`[9]` — 전부 `Where` 를 잇기만 한 단계**다(`CreateQuery` 1 · `Execute` 0 · 결과 `(IQueryable)`).
- ★★★ **`[3]` `ToList()` · `[4]` `Count()` · `[5]` `First()` · `[6]` `foreach` → `Execute` 1** — 공급자는 **이 순간에야** 식 트리 **전체**를 받는다. 두 `Where` 가 **`WHERE x > 1 AND x < 5` 하나로** 합쳐졌고, `Count`·`First` 는 **`COUNT(*)`·`TOP 1`** 로 번역됐다 — 「전부 가져와서 센다」가 아니라 **세기까지 공급자에게 넘어갔다.**
- ★★★ **`[7]` `min = 3` 뒤 `ToList()` → `WHERE x > 3`** — 식 트리에는 `min` 의 **값이 아니라 변수(캡처된 필드에 대한 `MemberExpression`)** 가 들어 있고, 장난감은 그것을 **번역할 때** 읽었다. [33번](../33-linq-method-syntax-and-deferred-execution/) (3)의 캡처 함정이 **번역문**에 그대로 나타난다.
- ★★★ **`[8]` `IEnumerable<int> e = db; e.Where(x => x > 1).ToList()` → 번역 `SELECT x FROM t`(`WHERE` 가 없다) · 결과 `[2,3,4,5]`** — 같은 `db` 인데 **정적 타입이 `IEnumerable<int>`** 라서 `Enumerable.Where` 가 골라졌다((1)). 공급자는 `GetEnumerator` 로 **표 전체**를 받았고, 거르기는 **메모리에서** 일어났다. 결과 값은 맞으니 **테스트로는 안 잡힌다** — 번역문(로그)으로만 보인다.
- ★★★ **`[9]` `db.Where(x => IsOdd(x))` → `CreateQuery` 1 · 에러 없음 · `[10]` `ToList()` → `NotSupportedException — 번역 못 함: 메서드 Program.IsOdd`** — 식 트리에는 `IsOdd` **호출 노드**가 들어갈 뿐 컴파일도 `Where` 도 통과한다. **번역할 수 없다는 사실은 `Execute` 에서야** 드러난다. `Execute` 로그는 찍혔고(1) 번역 로그는 **없다**(번역 중에 던졌다).
- ★★★ **`[11]` `…Where(x => x > 1).AsEnumerable().Where(IsOdd).ToList()` → 번역 `WHERE x > 1` · 결과 `[3,5]`** — `AsEnumerable` 이 정적 타입을 `IEnumerable<int>` 로 바꿨으니 **그 뒤의 `Where(IsOdd)` 는 `Enumerable.Where`**, 즉 **메모리에서** 돈다. 번역 가능한 앞쪽만 공급자에게 가고, 못 하는 뒤쪽은 받아 온 행에 C# 으로 적용됐다. [33번](../33-linq-method-syntax-and-deferred-execution/) (1)의 **`AsEnumerable` 이 소스 그 자체**였던 것이 여기서 쓸모가 된다.
- ★★ **`[12]` `db.Select(x => x * 10).ToList()` → `CreateQuery` 1 · `Execute` 1 · `NotSupportedException — 번역 못 함: 연산자 Select`** — 장난감이 모르는 **연산자**도 같은 지점(`Execute`)에서 거부된다.

```text
   장난감 공급자가 본 세계 — 무엇이 언제 공급자에게 닿나

   단계                                  CreateQuery   Execute   공급자가 받은 것
   ──────────────────────────────        ───────────   ───────   ─────────────────────────────────────
   db.Where(x > min)                          1           0      (설계도에 노드 한 겹)
     .Where(x < 5)                            1           0      (한 겹 더)
   .ToList() / .Count() / .First() / foreach  0           1      ★ 식 트리 전체 → 번역 → 실행
   min = 3 뒤 .ToList()                       0           1      ★ 번역할 때 min 을 읽는다 → x > 3
   (IEnumerable) db .Where(…) .ToList()       0           1      ★ WHERE 없는 트리 — 거르기는 내 메모리에서
   db.Where(x => IsOdd(x))                    1           0      (IsOdd 호출 노드가 든 설계도 — 아무도 안 막는다)
     .ToList()                                0           1      ★ 번역 중 거부 — 여기서 터진다
   db.Where(x > 1).AsEnumerable()             1           1      ★ 앞쪽만 번역 · 뒤쪽 IsOdd 는 메모리
     .Where(IsOdd).ToList()

   ★★★ 「실제 쿼리가 나가는 지점」 = Execute 가 불리는 지점 = 결과를 요구하는 연산(ToList · Count · First · foreach …).
       Where · Select 를 잇는 동안 공급자에게 오는 것은 CreateQuery 뿐이다 — 결과를 달라는 요청(Execute · GetEnumerator)은 결과를 요구하는 연산만 보낸다.
```

### (4) ★★★ 식 트리로 못 만드는 람다 — 같은 본문을 `Func` 과 `Expression` 에

```text
===== 소스: cs36b-ban.cs =====
using System;
using System.Linq.Expressions;
class P {
    static int n;
    static string? s = null;
    static void M() {
        Func<int, bool> a1 = x => { return x > 2; };                        // cell 문-본문 Func
        Expression<Func<int, bool>> a2 = x => { return x > 2; };            // cell 문-본문 Expression
        Func<int, int> b1 = x => n = x;                                      // cell 대입 Func
        Expression<Func<int, int>> b2 = x => n = x;                          // cell 대입 Expression
        Func<int, int> c1 = x => s?.Length ?? 0;                             // cell 널-조건 Func
        Expression<Func<int, int>> c2 = x => s?.Length ?? 0;                 // cell 널-조건 Expression
        Func<int, int> d1 = x => x switch { 1 => 10, _ => 0 };              // cell switch-식 Func
        Expression<Func<int, int>> d2 = x => x switch { 1 => 10, _ => 0 };  // cell switch-식 Expression
        Func<int, bool> e1 = x => x is > 2;                                  // cell is-패턴 Func
        Expression<Func<int, bool>> e2 = x => x is > 2;                      // cell is-패턴 Expression
        Func<int, int> f1 = x => throw new Exception();                      // cell throw-식 Func
        Expression<Func<int, int>> f2 = x => throw new Exception();          // cell throw-식 Expression
        Func<int, (int, int)> g1 = x => (x, x);                              // cell 튜플 Func
        Expression<Func<int, (int, int)>> g2 = x => (x, x);                  // cell 튜플 Expression
        Func<int, int> h1 = x => Local(x);                                   // cell 지역-함수 Func
        Expression<Func<int, int>> h2 = x => Local(x);                       // cell 지역-함수 Expression
        Func<int, string> i1 = x => $"{x}";                                  // cell 보간-문자열 Func
        Expression<Func<int, string>> i2 = x => $"{x}";                      // cell 보간-문자열 Expression
        Func<int, bool> j1 = x => x > 2 && x < 9;                            // cell 비교-논리 Func
        Expression<Func<int, bool>> j2 = x => x > 2 && x < 9;                // cell 비교-논리 Expression
        static int Local(int v) => v;
    }
    static void Main() { }
}
===== csc -nullable:enable -out:ex.dll cs36b-ban.cs 2>&1 | sort (cc exit=1) =====
cs36b-ban.cs(10,46): error CS0832: An expression tree may not contain an assignment operator
cs36b-ban.cs(12,46): error CS8072: An expression tree lambda may not contain a null propagating operator.
cs36b-ban.cs(14,46): error CS8514: An expression tree may not contain a switch expression.
cs36b-ban.cs(16,47): error CS8122: An expression tree may not contain an 'is' pattern-matching operator.
cs36b-ban.cs(18,46): error CS8188: An expression tree may not contain a throw-expression.
cs36b-ban.cs(20,53): error CS8143: An expression tree may not contain a tuple literal.
cs36b-ban.cs(22,46): error CS8110: An expression tree may not contain a reference to a local function
cs36b-ban.cs(8,42): error CS0834: A lambda expression with a statement body cannot be converted to an expression tree
===== python3 cellgrid.py cs36b-ban.cs <위 진단> — 칸마다 진단 코드 =====
식 \ 자리           Func             Expression
문-본문             ok               CS0834
대입               ok               CS0832
널-조건             ok               CS8072
switch-식         ok               CS8514
is-패턴            ok               CS8122
throw-식          ok               CS8188
튜플               ok               CS8143
지역-함수            ok               CS8110
보간-문자열           ok               ok
비교-논리            ok               ok
막힌 칸 8 / 20
```

- ★★★ **막힌 칸 8 / 20 — 전부 `Expression` 열이고 `Func` 열은 10 / 10 `ok`.** 같은 본문이 **델리게이트로는 되고 식 트리로는 안 된다.**
- ★★★ **`CS0834` — 문 본문 람다**(`x => { return x > 2; }`) · **`CS0832` 대입** · **`CS8072` 널 조건 `?.`** · **`CS8514` `switch` 식** · **`CS8122` `is` 패턴** · **`CS8188` `throw` 식** · **`CS8143` 튜플 리터럴** · **`CS8110` 지역 함수 참조.** 식 트리의 노드로 **나타낼 수 없는** 꼴로 읽힌다(★ 각 문법이 들어온 판과 노드 목록의 변천은 **재지 않았다**).
- ★★ **통과한 두 행 — 보간 문자열 `$"{x}"` 과 `x > 2 && x < 9`** — 식 트리로 **된다.** 보간 문자열은 식 트리 안에서 **다른 호출로 바뀌어** 들어가는 것으로 읽힌다(그 노드는 덤프하지 않았다).
- ★★ **`CS8110` 이 가장 실무적이다** — 식 트리 안에서 **지역 함수를 못 부른다**는 것은, 식 트리가 **「부를 수 있는 코드」가 아니라 「이름 붙은 메서드를 가리키는 자료」** 라는 뜻이다. (3)의 `IsOdd` 는 **정적 메서드라 컴파일은 통과**했고 공급자가 거부했다 — **거부하는 자리가 둘**(컴파일러 · 공급자)이다.

```text
   식 트리를 거부하는 두 관문

   관문 ① 컴파일러 — 「식 트리 노드로 나타낼 수 있나」                   관문 ② 공급자 — 「내가 번역할 수 있나」
   ─────────────────────────────────────────────                       ─────────────────────────────────────────
   문 본문 · 대입 · ?. · switch 식 · is 패턴 · throw 식 · 튜플 ·          IsOdd(x) 같은 임의의 메서드 호출 · 모르는 연산자
   지역 함수   → 컴파일 에러 (CS0834 · CS0832 · CS8072 …) (4)             → 실행 에러 (Execute 에서) (3)
   ★ 언제: 빌드할 때                                                    ★ 언제: 결과를 요구할 때 — 정의·Where 에서는 조용하다
```

## 문법 — 형태와 규칙

### 형태

```text
===== 소스: cs36b-form.cs =====
using System;
using System.Linq;
using System.Linq.Expressions;

Expression<Func<int, int, int>> add = (a, b) => a + b;
Console.WriteLine($"{add} · {add.Body.NodeType} · 매개변수 {add.Parameters.Count}");
Console.WriteLine(add.Compile()(2, 3));

var p = Expression.Parameter(typeof(int), "x");
var built = Expression.Lambda<Func<int, bool>>(Expression.GreaterThan(p, Expression.Constant(2)), p);
Console.WriteLine($"{built} · {built.Compile()(3)}");
Console.WriteLine(string.Join(",", new[] { 1, 2, 3, 4 }.AsQueryable().Where(built)));
===== csc -out:ex.dll cs36b-form.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
(a, b) => (a + b) · Add · 매개변수 2
5
x => (x > 2) · True
3,4
```

- ★★★ **`Expression<Func<…>> e = (a, b) => a + b;`** — 람다를 **식 트리 타입의 변수**에 넣으면 식 트리다. `e.Body.NodeType` 이 **`Add`**, 매개변수 2.
- ★★ **`e.Compile()(2, 3)`** — 설계도를 실행 파일로 바꿔 부른다 → `5`.
- ★★ **`Expression.Parameter` · `Constant` · `GreaterThan` · `Lambda`** — (1)에서 **컴파일러가 대신 쓴 호출**을 손으로 쓰면 같은 나무가 된다(`x => (x > 2)`). 그 나무를 `AsQueryable().Where(built)` 에 넘기면 `3,4`.

### 금지 사례 — 진단이 나는 꼴 · 진단 없이 틀리는 꼴

| 쓴 꼴 | 무엇이 나나 | 어디서 |
|---|---|---|
| 식 트리에 문 본문 람다 | `CS0834` | (4) |
| 식 트리에 대입 · `?.` · `switch` 식 · `is` 패턴 · `throw` 식 · 튜플 · 지역 함수 | `CS0832` · `CS8072` · `CS8514` · `CS8122` · `CS8188` · `CS8143` · `CS8110` | (4) |
| ★★★ 식 트리 안에서 공급자가 모르는 메서드 호출 | ★★★ **컴파일 통과 · `Where` 통과** — 결과를 요구할 때 공급자가 거부(장난감: `NotSupportedException`) | (3) |
| ★★★ `IQueryable` 을 `IEnumerable` 변수·매개변수로 받고 `Where` | ★★★ **진단 없음 · 결과도 맞다** — 거르기가 **메모리로** 옮겨 간다(`WHERE` 가 사라짐) | (3) `[8]` |
| ★★ 쿼리를 정의한 뒤 캡처한 변수 변경 | ★★ **진단 없음** — 번역문이 **나중 값**으로 바뀐다 | (3) `[7]` |

## 어디서 틀리나

1. ★★★ **「`Func<T,bool>` 을 받아도 ORM 이 알아서 번역한다」** — `Func` 은 **컴파일된 메서드의 주소**다. 안을 읽을 수 없다((1)). 번역되려면 **`Expression<Func<T,bool>>`** 이어야 하고, 그러려면 받는 쪽이 **`IQueryable`** 이어야 한다.
2. ★★★ **「`IQueryable` 에 `Where` 를 이으면 그때 쿼리가 나간다」** — **`Execute` 0** 이다. 결과를 요구할 때 **한 번**, 쌓인 것 전체로((3)).
3. ★★★ **「번역 못 하는 메서드는 `Where` 줄에서 터진다」** — **결과를 요구하는 줄**에서 터진다((3) `[9]`·`[10]`).
4. ★★★ **「`IEnumerable` 로 받아도 같은 쿼리다」** — 결과는 같고 **거르는 곳**이 다르다(`WHERE` 없음 · 전부 가져온다)((3) `[8]`).
5. ★★ **「`AsEnumerable()` 은 아무 일도 안 한다」** — 객체는 그대로지만 **그 뒤의 연산자를 `Enumerable` 쪽으로** 고르게 한다 — 앞은 번역, 뒤는 메모리((3) `[11]`).
6. ★★ **「어떤 람다든 식 트리가 된다」** — 여덟 가지가 **컴파일 에러**다(8 / 20)((4)).
7. ★ **「`IQueryable` 이 DB 에서 빠르다」** — **이 문서가 잰 것이 아니다.** 잰 것은 **어디서 걸러지나**다.

## 구현 세부사항 대 언어 보장

| 무엇 | 층 | 근거 |
|---|---|---|
| **람다 → 델리게이트 또는 식 트리(목표 타입이 정한다)** | ★★★ **언어** | (1) |
| **식 트리로 못 바꾸는 람다는 컴파일 에러** | ★★★ **언어**(어느 꼴이 막히나) · 진단 **코드** 배정은 ★ **Roslyn** | (4) |
| **`s.Where` 가 정적 타입으로 `Enumerable`/`Queryable` 을 고른다** | ★★★ **언어**(오버로드 해석) | (1)(3) `[8]` |
| **식 트리 람다가 `Expression.Parameter`·`Constant`·`GreaterThan`·`Lambda` 호출 사슬로 · 캐시 없음** | ★★ **Roslyn 구현** | (1) |
| **`IQueryProvider` 의 두 일 — 만들기(`CreateQuery`)와 실행(`Execute`)** | ★★ **BCL 계약**(XML) | (3) |
| **`Queryable.Where` 가 `CreateQuery` 를, `Queryable.Count`·`First` 가 `Execute` 를 부른다** | ★★ **BCL 구현**(이 판의 로그) | (3) |
| **`ToList`·`foreach` 가 `GetEnumerator` 를 부르고, 거기서 `Execute` 를 부른다** | ★★★ 앞쪽(`GetEnumerator`)은 **BCL** · 뒤쪽(`Execute`)은 **장난감이 그렇게 짰다**(`ToyQuery.GetEnumerator`) | (3) |
| **`Execute` 에서 무엇을 하나(번역 · 거부 · 메모리 실행)** | ★★★ **공급자마다 다르다** — 이 문서는 **장난감**의 것 | (3) |
| **`EnumerableQuery` 가 메모리에서 돈다** | ★★ **BCL**(XML 요약 + 결과 관찰) | (2) |

## 언제 쓰고 언제 안 쓰나

- ★★★ **원격(DB 등)으로 번역될 쿼리를 받는 메서드는 `IQueryable<T>` 와 `Expression<Func<…>>` 로 받아라** — `IEnumerable<T>`·`Func<…>` 로 받으면 거르기가 **내 메모리로** 온다((3) `[8]`).
- ★★★ **번역 못 하는 로직이 있으면 번역 가능한 부분을 앞에 두고 `AsEnumerable()` 로 끊어라** — 앞은 공급자, 뒤는 메모리((3) `[11]`). ★ 끊는 자리 **앞**에서 충분히 걸러야 받아 오는 행이 적다(행 수는 장난감에서 **결과로만** 보였다 — 시간은 안 쟀다).
- ★★ **「쿼리가 언제 나가나」는 결과를 요구하는 연산을 세라** — `ToList`·`Count`·`First`·`foreach` 마다 **한 번씩**((3)). 같은 `IQueryable` 을 두 번 소비하면 **두 번** 나간다(`[3]`\~`[6]` 이 네 번 `Execute`).
- ★★ **식 트리 안에서는 C# 3 시절 문법으로 써라** — `?.`·`switch` 식·패턴·튜플은 막힌다((4)).
- ★ **식 트리를 직접 만들 일은 드물다** — 동적 필터를 조립할 때(`Expression.Parameter`…)쯤이다(형태).

## 핵심 문장

1. ★★★ **같은 람다가 `Func` 이면 컴파일된 메서드의 주소(`ldftn`·`newobj`)가, `Expression` 이면 노드를 조립하는 호출 사슬(`Parameter`·`Constant`·`GreaterThan`·`Lambda`)이 된다**((1)).
2. ★★★ **`Where` 가 `Enumerable` 로 가나 `Queryable` 로 가나는 원본의 정적 타입이 정한다 — `IEnumerable` 로 받는 순간 거르기가 메모리로 온다**((1)(3)).
3. ★★★ **`IQueryable` 에 연산자를 잇는 동안 공급자에게 오는 것은 `CreateQuery` 뿐이다 — 결과를 달라는 요청은 결과를 요구하는 연산이 보낸다(Execute 가 불린 단계 9 / 12)**((3)).
4. ★★★ **번역 실패는 두 관문에서 난다 — 식 트리로 못 그리는 것은 컴파일러가(8 / 20), 공급자가 모르는 것은 `Execute` 가 거부한다**((3)(4)).
5. ★★ **`AsEnumerable()` 은 객체를 바꾸지 않고 뒤쪽 연산자의 목적지를 바꾼다 — 번역과 메모리 실행의 경계선이다**((3)).

## 관련 자료

- [33번 — LINQ 메서드 구문과 지연 실행](../33-linq-method-syntax-and-deferred-execution/) — **경계**: `Enumerable` 쪽의 즉시·지연은 거기. (1)의 `AsEnumerable` 이 소스 그 자체 · (3)의 캡처 함정 · (1-b)의 「뒤에 붙은 것을 알아보는」 지름길.
- [34번 — LINQ 쿼리 구문](../34-linq-query-syntax/) (3) — 번역이 **이름으로** 찾는다는 것. 같은 쿼리 구문이 `IQueryable` 원본이면 `Queryable` 의 메서드에 도착한다.
- [35번 — 그룹·조인·집계](../35-linq-grouping-joins-and-aggregation/) — 같은 연산자가 메모리에서 도는 쪽.
- [30번 — 확장 메서드](../30-extension-methods-and-extension-members/) — `Enumerable.Where` 와 `Queryable.Where` 는 **둘 다 확장 메서드**이고, 수신자의 정적 타입이 고른다.
- [27번 — 델리게이트](../27-delegates-and-func-action/) · [28번 — 람다와 캡처](../28-lambdas-and-closure-capture/) (1) — `Func` 쪽 IL 의 정본.

## 용어 풀이

- **식 트리(expression tree)** — 코드를 **노드의 나무**로 나타낸 자료. `Expression<TDelegate>` 가 람다 하나를 담는다.
- **`IQueryable<T>`** — `Expression`(쌓인 식 트리)과 `Provider`(그것을 실행할 공급자)를 가진 시퀀스.
- **`IQueryProvider`** — `CreateQuery`(식 트리로 새 `IQueryable` 만들기) · `Execute`(식 트리 실행) 두 일을 하는 객체. ORM 이 이것을 구현한다.
- **`Quote`** — 식 트리 안에 **람다를 식 트리째** 넣을 때 싸는 노드((2)).
- **`EnumerableQuery<T>`** — `AsQueryable()` 이 돌려주는 것. 메모리 컬렉션을 `IQueryable` 로 포장하고 식 트리를 메모리에서 돌린다.
- **번역(translation)** — 공급자가 식 트리를 자기 언어(SQL 등)로 바꾸는 일. 이 문서에서는 **장난감**의 것만 보였다.

## 더 들어가면

- ★ **실제 ORM(EF Core)** — 설치하지 않았고 문서도 열지 않았다. 번역 실패를 **어느 지점에서 어떤 예외로** 알리는지, 어떤 메서드를 번역하는지는 **확인할 것**으로 남긴다(★ 「`Execute` 에서 거부한다」는 장난감의 규칙이다).
- ★ **`ExpressionVisitor`** — 식 트리를 **바꿔 쓰는** 표준 도구. 장난감은 손으로 재귀했다.
- ★ **식 트리의 할당·`Compile()` 비용** — (1)에서 캐시가 없는 것을 봤지만 **바이트·시간은 재지 않았다.**
