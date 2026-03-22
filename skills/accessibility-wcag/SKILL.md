---
name: accessibility-wcag
description: Web accessibility patterns for WCAG 2.2 compliance including ARIA, keyboard navigation, screen readers, and testing
---

# Accessibility & WCAG

## Semantic HTML

```html
<!-- Use semantic elements instead of generic divs -->
<header>
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="/" aria-current="page">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li><a href="/about">About</a></li>
    </ul>
  </nav>
</header>

<main>
  <article>
    <h1>Product Details</h1>
    <section aria-labelledby="specs-heading">
      <h2 id="specs-heading">Specifications</h2>
      <dl>
        <dt>Weight</dt>
        <dd>1.2 kg</dd>
        <dt>Dimensions</dt>
        <dd>30 x 20 x 10 cm</dd>
      </dl>
    </section>
  </article>
</main>

<footer>
  <p>&copy; 2024 Company Name</p>
</footer>
```

Use `<nav>`, `<main>`, `<article>`, `<section>`, `<aside>` instead of `<div>` for landmarks. Screen readers use these to navigate the page.

## ARIA Patterns

```tsx
function Modal({ isOpen, onClose, title, children }) {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onKeyDown={(e) => e.key === "Escape" && onClose()}
    >
      <h2 id="modal-title">{title}</h2>
      <div>{children}</div>
      <button onClick={onClose} aria-label="Close dialog">
        <XIcon aria-hidden="true" />
      </button>
    </div>
  );
}

function Tabs({ tabs, activeIndex, onChange }) {
  return (
    <div>
      <div role="tablist" aria-label="Settings sections">
        {tabs.map((tab, i) => (
          <button
            key={tab.id}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={i === activeIndex}
            aria-controls={`panel-${tab.id}`}
            tabIndex={i === activeIndex ? 0 : -1}
            onClick={() => onChange(i)}
            onKeyDown={(e) => handleArrowKeys(e, i, tabs.length, onChange)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab, i) => (
        <div
          key={tab.id}
          role="tabpanel"
          id={`panel-${tab.id}`}
          aria-labelledby={`tab-${tab.id}`}
          hidden={i !== activeIndex}
          tabIndex={0}
        >
          {tab.content}
        </div>
      ))}
    </div>
  );
}
```

## Keyboard Navigation

```tsx
function handleArrowKeys(
  event: React.KeyboardEvent,
  currentIndex: number,
  totalItems: number,
  onSelect: (index: number) => void
) {
  let newIndex = currentIndex;

  switch (event.key) {
    case "ArrowRight":
    case "ArrowDown":
      newIndex = (currentIndex + 1) % totalItems;
      break;
    case "ArrowLeft":
    case "ArrowUp":
      newIndex = (currentIndex - 1 + totalItems) % totalItems;
      break;
    case "Home":
      newIndex = 0;
      break;
    case "End":
      newIndex = totalItems - 1;
      break;
    default:
      return;
  }

  event.preventDefault();
  onSelect(newIndex);
}
```

All interactive elements must be reachable via keyboard. Tab for focus navigation, Enter/Space for activation, Arrow keys for within-component navigation.

## Form Accessibility

```tsx
function SignupForm() {
  return (
    <form aria-labelledby="form-title" noValidate>
      <h2 id="form-title">Create Account</h2>

      <div>
        <label htmlFor="email">Email address</label>
        <input
          id="email"
          type="email"
          required
          aria-required="true"
          aria-describedby="email-hint email-error"
          aria-invalid={hasError ? "true" : undefined}
        />
        <p id="email-hint">We will never share your email.</p>
        {hasError && (
          <p id="email-error" role="alert">
            Please enter a valid email address.
          </p>
        )}
      </div>

      <button type="submit">Create Account</button>
    </form>
  );
}
```

## Color and Contrast

```css
:root {
  --text-primary: #1a1a1a;      /* 15.3:1 on white */
  --text-secondary: #595959;    /* 7.0:1 on white */
  --text-on-primary: #ffffff;   /* Ensure 4.5:1 on brand color */
  --border-focus: #0066cc;      /* Visible focus ring */
}

*:focus-visible {
  outline: 3px solid var(--border-focus);
  outline-offset: 2px;
}

.error-message {
  color: #d32f2f;
  /* Don't rely on color alone - add icon or text prefix */
}
.error-message::before {
  content: "Error: ";
  font-weight: bold;
}
```

WCAG AA requires 4.5:1 contrast for normal text, 3:1 for large text (18px bold or 24px regular).

## Anti-Patterns

- Using `div` and `span` for clickable elements instead of `button` or `a`
- Removing focus outlines without providing an alternative indicator
- Relying on color alone to convey information (red for error, green for success)
- Using `aria-label` when visible text already labels the element
- Auto-playing media without a pause mechanism
- Missing skip navigation link for keyboard users

## Checklist

- [ ] All interactive elements keyboard-accessible (Tab, Enter, Escape, Arrows)
- [ ] Semantic HTML landmarks used (`nav`, `main`, `article`, `section`)
- [ ] Images have descriptive `alt` text (or `alt=""` for decorative)
- [ ] Color contrast meets WCAG AA (4.5:1 normal text, 3:1 large text)
- [ ] Focus indicators visible on all interactive elements
- [ ] Form inputs have associated `<label>` elements
- [ ] Error messages announced to screen readers via `role="alert"`
- [ ] Page tested with screen reader (VoiceOver, NVDA) and keyboard only
