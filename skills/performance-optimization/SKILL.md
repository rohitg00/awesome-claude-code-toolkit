---
name: performance-optimization
description: Web performance optimization including bundle analysis, lazy loading, caching strategies, and Core Web Vitals
---

# Performance Optimization

## Bundle Analysis and Code Splitting

```typescript
// Dynamic import for route-level code splitting
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Settings = lazy(() => import("./pages/Settings"));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

```javascript
// vite.config.ts - manual chunk splitting
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          charts: ["recharts", "d3"],
          editor: ["@monaco-editor/react"],
        },
      },
    },
  },
});
```

```bash
# Analyze bundle composition
npx vite-bundle-visualizer
npx source-map-explorer dist/assets/*.js
```

## Image Optimization

```tsx
import Image from "next/image";

function ProductImage({ src, alt }: { src: string; alt: string }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={800}
      height={600}
      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      placeholder="blur"
      blurDataURL={generateBlurHash(src)}
      loading="lazy"
    />
  );
}
```

```html
<!-- Native lazy loading with aspect ratio -->
<img
  src="product.webp"
  alt="Product photo"
  width="800"
  height="600"
  loading="lazy"
  decoding="async"
  fetchpriority="low"
/>

<!-- Preload LCP image -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high" />
```

## Caching Headers

```typescript
function setCacheHeaders(res: Response, options: CacheOptions) {
  if (options.immutable) {
    res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
    return;
  }

  if (options.revalidate) {
    res.setHeader("Cache-Control", `public, max-age=0, s-maxage=${options.revalidate}, stale-while-revalidate=${options.staleWhileRevalidate ?? 86400}`);
    return;
  }

  res.setHeader("Cache-Control", "no-cache, no-store, must-revalidate");
}

app.use("/assets", (req, res, next) => {
  setCacheHeaders(res, { immutable: true });
  next();
});

app.use("/api", (req, res, next) => {
  setCacheHeaders(res, { revalidate: 60, staleWhileRevalidate: 3600 });
  next();
});
```

## Virtual Lists for Large Data

```tsx
import { useVirtualizer } from "@tanstack/react-virtual";

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
    overscan: 5,
  });

  return (
    <div ref={parentRef} style={{ height: "600px", overflow: "auto" }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px`, position: "relative" }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: "absolute",
              top: 0,
              transform: `translateY(${virtualRow.start}px)`,
              height: `${virtualRow.size}px`,
              width: "100%",
            }}
          >
            <ItemRow item={items[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Core Web Vitals Monitoring

```typescript
import { onCLS, onINP, onLCP } from "web-vitals";

function sendMetric(metric: { name: string; value: number; id: string }) {
  navigator.sendBeacon("/api/vitals", JSON.stringify(metric));
}

onCLS(sendMetric);
onINP(sendMetric);
onLCP(sendMetric);
```

- **LCP** (Largest Contentful Paint): < 2.5s. Preload hero images, optimize server response time.
- **INP** (Interaction to Next Paint): < 200ms. Avoid long tasks, use `requestIdleCallback`.
- **CLS** (Cumulative Layout Shift): < 0.1. Set explicit dimensions on images and embeds.

## Anti-Patterns

- Loading all JavaScript upfront instead of code-splitting by route
- Serving unoptimized images (no WebP/AVIF, no responsive sizes)
- Missing `width` and `height` on images (causes layout shift)
- Using `Cache-Control: no-cache` on static assets with content hashes
- Rendering thousands of DOM nodes instead of virtualizing lists
- Blocking the main thread with synchronous computation

## Checklist

- [ ] Routes lazy-loaded with dynamic `import()` and Suspense
- [ ] Bundle analyzed and vendor chunks separated
- [ ] Images served in WebP/AVIF with responsive `sizes` attribute
- [ ] LCP image preloaded with `fetchpriority="high"`
- [ ] Static assets cached with immutable headers and content hashes
- [ ] Lists with 100+ items use virtualization
- [ ] Core Web Vitals monitored in production (LCP, INP, CLS)
- [ ] No render-blocking resources in the critical path
