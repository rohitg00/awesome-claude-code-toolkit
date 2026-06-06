---
name: frontend-excellence
description: Modern frontend patterns for React Server Components, performance optimization, and Core Web Vitals
---

# Frontend Excellence

## React Server Components

Server Components run on the server and send rendered HTML to the client. They can directly access databases, filesystems, and internal APIs without exposing them to the browser.

```tsx
// app/products/page.tsx (Server Component by default)
async function ProductsPage() {
  const products = await db.query("SELECT * FROM products WHERE active = true");
  return (
    <main>
      <h1>Products</h1>
      <ProductList products={products} />
      <AddToCartButton />  {/* Client Component */}
    </main>
  );
}
```

Rules:
- Server Components cannot use `useState`, `useEffect`, or browser APIs
- Mark interactive components with `'use client'` at the top of the file
- Pass serializable props from Server to Client Components (no functions, no classes)
- Keep `'use client'` boundary as deep in the tree as possible

## Streaming SSR

```tsx
import { Suspense } from 'react';

export default function Dashboard() {
  return (
    <div>
      <Header />  {/* renders immediately */}
      <Suspense fallback={<ChartSkeleton />}>
        <AnalyticsChart />  {/* streams when ready */}
      </Suspense>
      <Suspense fallback={<TableSkeleton />}>
        <RecentOrders />  {/* streams independently */}
      </Suspense>
    </div>
  );
}
```

Each `Suspense` boundary streams independently. Place boundaries around data-fetching components to avoid blocking the entire page.

## Code Splitting

```tsx
import dynamic from 'next/dynamic';

const HeavyEditor = dynamic(() => import('@/components/Editor'), {
  loading: () => <EditorSkeleton />,
  ssr: false,
});

const AdminPanel = dynamic(() => import('@/components/AdminPanel'));
```

Split on:
- Route boundaries (automatic in Next.js App Router)
- Conditionally rendered components (modals, drawers, admin panels)
- Heavy libraries (chart libraries, rich text editors, maps)
- Below-the-fold content

## Bundle Optimization

```javascript
// next.config.js
module.exports = {
  experimental: {
    optimizePackageImports: ['lucide-react', '@heroicons/react', 'lodash-es'],
  },
};
```

Checklist:
- Run `npx next build` and review the output size per route
- Use `@next/bundle-analyzer` to identify large dependencies
- Replace `moment` with `date-fns` or `dayjs` (save ~200KB)
- Import specific functions: `import { debounce } from 'lodash-es/debounce'`
- Prefer CSS over JS for animations (no runtime cost)
- Tree-shake icon libraries: `import { Search } from 'lucide-react'`

## Core Web Vitals Targets

| Metric | Good | Needs Work | Poor |
|--------|------|------------|------|
| LCP (Largest Contentful Paint) | <2.5s | 2.5-4.0s | >4.0s |
| INP (Interaction to Next Paint) | <200ms | 200-500ms | >500ms |
| CLS (Cumulative Layout Shift) | <0.1 | 0.1-0.25 | >0.25 |

## LCP Optimization

- Preload hero images: `<link rel="preload" as="image" href="..." />`
- Use `priority` prop on above-the-fold `<Image>` components
- Inline critical CSS, defer non-critical stylesheets
- Avoid client-side rendering for above-the-fold content
- Set explicit `width`/`height` on images to prevent layout shifts

## Image Optimization

```tsx
import Image from 'next/image';

<Image
  src="/hero.jpg"
  alt="Descriptive alt text"
  width={1200}
  height={630}
  priority              // preload for LCP images
  sizes="(max-width: 768px) 100vw, 50vw"
  placeholder="blur"
  blurDataURL={base64}  // inline tiny placeholder
/>
```

- Use `next/image` or equivalent (automatic WebP/AVIF, responsive srcset)
- Set `sizes` attribute to avoid downloading oversized images
- Use `placeholder="blur"` with a base64 data URL for perceived performance
- Lazy load below-the-fold images (default behavior)

## Font Loading Strategy

```tsx
// app/layout.tsx
import { Inter } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',       // show fallback font immediately
  preload: true,
  variable: '--font-inter',
});

export default function RootLayout({ children }) {
  return (
    <html className={inter.variable}>
      <body>{children}</body>
    </html>
  );
}
```

- Use `next/font` for zero-CLS font loading with automatic subsetting
- Set `display: 'swap'` to avoid invisible text during load
- Self-host fonts instead of loading from Google CDN (saves DNS lookup)
- Limit to 2 font families maximum

## CLS Prevention

- Always set `width` and `height` on images and videos
- Use `aspect-ratio` CSS for responsive media containers
- Reserve space for dynamic content (ads, embeds) with `min-height`
- Avoid inserting content above existing content after load
- Use CSS `contain: layout` for components that change size

## Performance Monitoring

```typescript
import { onCLS, onINP, onLCP } from 'web-vitals';

onCLS(console.log);
onINP(console.log);
onLCP(console.log);
```

Measure real user metrics (RUM), not just lab scores. Vercel Analytics and Google Search Console provide field data.
