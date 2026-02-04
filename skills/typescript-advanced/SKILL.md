---
name: typescript-advanced
description: Advanced TypeScript patterns including generics, conditional types, mapped types, template literals, and type guards
---

# TypeScript Advanced

## Generics with Constraints

```typescript
interface HasId {
  id: string;
}

function findById<T extends HasId>(items: T[], id: string): T | undefined {
  return items.find(item => item.id === id);
}

function groupBy<T, K extends string | number>(
  items: T[],
  keyFn: (item: T) => K
): Record<K, T[]> {
  return items.reduce((acc, item) => {
    const key = keyFn(item);
    (acc[key] ??= []).push(item);
    return acc;
  }, {} as Record<K, T[]>);
}

type ApiResponse<T> = {
  data: T;
  meta: { page: number; total: number };
};

async function fetchApi<T>(url: string): Promise<ApiResponse<T>> {
  const res = await fetch(url);
  return res.json();
}
```

## Conditional Types

```typescript
type IsString<T> = T extends string ? true : false;

type Flatten<T> = T extends Array<infer U> ? U : T;

type UnwrapPromise<T> = T extends Promise<infer U> ? UnwrapPromise<U> : T;

type FunctionReturn<T> = T extends (...args: any[]) => infer R ? R : never;

type ExtractRouteParams<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<Rest>
    : T extends `${string}:${infer Param}`
      ? Param
      : never;

type Params = ExtractRouteParams<"/users/:userId/posts/:postId">;
```

## Mapped Types

```typescript
type Readonly<T> = { readonly [K in keyof T]: T[K] };

type Optional<T> = { [K in keyof T]?: T[K] };

type Nullable<T> = { [K in keyof T]: T[K] | null };

type PickByType<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

interface User {
  id: string;
  name: string;
  age: number;
  active: boolean;
}

type StringFields = PickByType<User, string>;

type EventMap<T> = {
  [K in keyof T as `on${Capitalize<string & K>}`]: (value: T[K]) => void;
};

type UserEvents = EventMap<{ login: User; logout: string }>;
```

## Discriminated Unions

```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function divide(a: number, b: number): Result<number, string> {
  if (b === 0) return { ok: false, error: "Division by zero" };
  return { ok: true, value: a / b };
}

const result = divide(10, 2);
if (result.ok) {
  console.log(result.value);
} else {
  console.error(result.error);
}

type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2;
    case "rect": return shape.width * shape.height;
    case "triangle": return 0.5 * shape.base * shape.height;
  }
}
```

## Type Guards

```typescript
function isNonNull<T>(value: T | null | undefined): value is T {
  return value != null;
}

function hasProperty<K extends string>(
  obj: unknown,
  key: K
): obj is Record<K, unknown> {
  return typeof obj === "object" && obj !== null && key in obj;
}

const values = [1, null, 2, undefined, 3].filter(isNonNull);

function assertNever(value: never): never {
  throw new Error(`Unexpected value: ${value}`);
}
```

## Utility Type Combinations

```typescript
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

type StrictOmit<T, K extends keyof T> = Pick<T, Exclude<keyof T, K>>;

type RequireAtLeastOne<T, Keys extends keyof T = keyof T> = Pick<T, Exclude<keyof T, Keys>> &
  { [K in Keys]-?: Required<Pick<T, K>> & Partial<Pick<T, Exclude<Keys, K>>> }[Keys];

type UpdateUserInput = RequireAtLeastOne<{ name: string; email: string; age: number }>;
```

## Anti-Patterns

- Using `any` instead of `unknown` for values of uncertain type
- Type assertions (`as`) when a type guard would be safer
- Overly complex generic signatures that reduce readability
- Not using discriminated unions for state machines or result types
- Using `enum` when a union of string literals suffices
- Ignoring `strictNullChecks` in tsconfig

## Checklist

- [ ] `strict: true` enabled in tsconfig
- [ ] `unknown` used instead of `any` for external data
- [ ] Type guards validate runtime types safely
- [ ] Discriminated unions model state with exhaustive switches
- [ ] Generic constraints (`extends`) prevent misuse
- [ ] Mapped types used to derive related types from a source
- [ ] Utility types (`Pick`, `Omit`, `Partial`) preferred over manual retyping
- [ ] Template literal types used for string pattern enforcement
