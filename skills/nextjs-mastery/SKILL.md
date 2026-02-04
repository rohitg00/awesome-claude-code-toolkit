---
name: nextjs-mastery
description: Next.js 14+ App Router patterns including RSC, ISR, middleware, parallel routes, and data fetching
---

# Next.js Mastery

## App Router Structure

```
app/
  layout.tsx              # Root layout (wraps all pages)
  page.tsx                # Home route /
  loading.tsx             # Route-level Suspense fallback
  error.tsx               # Route-level error boundary
  not-found.tsx           # Custom 404
  (marketing)/
    about/page.tsx        # /about (grouped without URL segment)
  dashboard/
    layout.tsx            # Nested layout for /dashboard/*
    page.tsx              # /dashboard
    @analytics/page.tsx   # Parallel route slot
    @activity/page.tsx    # Parallel route slot
    settings/
      page.tsx            # /dashboard/settings
  api/
    webhooks/route.ts     # Route handler (POST /api/webhooks)
```

Route groups `(name)` organize code without affecting URLs. Parallel routes `@slot` render multiple pages simultaneously.

## Server Components and Data Fetching

```tsx
async function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const product = await db.product.findUnique({ where: { id } });

  if (!product) notFound();

  return (
    <div>
      <h1>{product.name}</h1>
      <p>{product.description}</p>
      <Suspense fallback={<ReviewsSkeleton />}>
        <Reviews productId={id} />
      </Suspense>
    </div>
  );
}

async function Reviews({ productId }: { productId: string }) {
  const reviews = await db.review.findMany({ where: { productId } });
  return (
    <ul>
      {reviews.map(r => <li key={r.id}>{r.text} - {r.rating}/5</li>)}
    </ul>
  );
}
```

Server Components are the default. They run on the server, can access databases directly, and send zero JavaScript to the client.

## ISR and Caching

```tsx
export const revalidate = 3600;

async function BlogPage() {
  const posts = await fetch("https://api.example.com/posts", {
    next: { revalidate: 3600, tags: ["posts"] },
  }).then(r => r.json());

  return <PostList posts={posts} />;
}
```

```tsx
import { revalidateTag, revalidatePath } from "next/cache";

export async function createPost(formData: FormData) {
  "use server";
  await db.post.create({ data: { title: formData.get("title") as string } });
  revalidateTag("posts");
  revalidatePath("/blog");
}
```

## Middleware

```typescript
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("session")?.value;

  if (request.nextUrl.pathname.startsWith("/dashboard") && !token) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  const response = NextResponse.next();
  response.headers.set("x-request-id", crypto.randomUUID());
  return response;
}

export const config = {
  matcher: ["/dashboard/:path*", "/api/:path*"],
};
```

Middleware runs at the edge before every matched request. Keep it lightweight.

## Server Actions

```tsx
"use server";

import { z } from "zod";
import { revalidatePath } from "next/cache";

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(2).max(100),
});

export async function updateProfile(prevState: any, formData: FormData) {
  const parsed = schema.safeParse(Object.fromEntries(formData));
  if (!parsed.success) {
    return { errors: parsed.error.flatten().fieldErrors };
  }

  await db.user.update({
    where: { email: parsed.data.email },
    data: { name: parsed.data.name },
  });

  revalidatePath("/profile");
  return { success: true };
}
```

## Anti-Patterns

- Adding `'use client'` to top-level layout or page components
- Fetching data on the client when it can be done in a Server Component
- Using `useEffect` for data fetching instead of Server Components or `use()`
- Not wrapping slow async components with `<Suspense>`
- Putting heavy logic in middleware (it runs on every matched request)
- Ignoring `loading.tsx` and `error.tsx` conventions

## Checklist

- [ ] Server Components used by default; `'use client'` only on interactive leaves
- [ ] Data fetching happens in Server Components with proper caching
- [ ] `<Suspense>` boundaries wrap independent async sections
- [ ] `loading.tsx` and `error.tsx` exist for key routes
- [ ] Middleware is lightweight and only handles auth/redirects/headers
- [ ] Server Actions validate input with Zod before database writes
- [ ] `revalidateTag` or `revalidatePath` called after mutations
- [ ] Route groups and parallel routes used to organize complex layouts
