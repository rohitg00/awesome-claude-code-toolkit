---
name: golang-idioms
description: Idiomatic Go patterns for error handling, interfaces, concurrency, testing, and module management
---

# Go Idioms

## Error Handling

```go
// Return errors, never panic in library code
func LoadConfig(path string) (Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return Config{}, fmt.Errorf("reading config %s: %w", path, err)
    }

    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return Config{}, fmt.Errorf("parsing config: %w", err)
    }

    return cfg, nil
}
```

Rules:
- Always wrap errors with context using `fmt.Errorf("context: %w", err)`
- Use `%w` to allow callers to use `errors.Is` and `errors.As`
- Handle errors at the appropriate level; do not log and return the same error
- Define sentinel errors for expected conditions

```go
var (
    ErrNotFound    = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
)

func GetUser(id string) (User, error) {
    user, ok := store[id]
    if !ok {
        return User{}, fmt.Errorf("user %s: %w", id, ErrNotFound)
    }
    return user, nil
}

// Caller
user, err := GetUser(id)
if errors.Is(err, ErrNotFound) {
    http.Error(w, "user not found", http.StatusNotFound)
    return
}
```

## Interface Design

```go
// Keep interfaces small (1-3 methods)
type Reader interface {
    Read(p []byte) (n int, err error)
}

type UserStore interface {
    GetUser(ctx context.Context, id string) (User, error)
    CreateUser(ctx context.Context, u User) error
}

// Accept interfaces, return structs
func NewService(store UserStore, logger *slog.Logger) *Service {
    return &Service{store: store, logger: logger}
}
```

Rules:
- Define interfaces where they are used (consumer side), not where they are implemented
- Prefer small, composable interfaces over large ones
- Use `io.Reader`, `io.Writer`, `fmt.Stringer` from the standard library
- An interface with one method should be named after the method + `er` suffix

## Goroutine and Channel Patterns

### Worker Pool
```go
func process(ctx context.Context, jobs <-chan Job, workers int) <-chan Result {
    results := make(chan Result, workers)
    var wg sync.WaitGroup

    for range workers {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                case results <- job.Execute():
                }
            }
        }()
    }

    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}
```

### Fan-out/Fan-in
```go
func fanOut[T, R any](ctx context.Context, items []T, fn func(T) R, concurrency int) []R {
    sem := make(chan struct{}, concurrency)
    results := make([]R, len(items))
    var wg sync.WaitGroup

    for i, item := range items {
        wg.Add(1)
        sem <- struct{}{}
        go func() {
            defer func() { <-sem; wg.Done() }()
            results[i] = fn(item)
        }()
    }

    wg.Wait()
    return results
}
```

Rules:
- Always pass `context.Context` as the first parameter
- Always ensure goroutines can be stopped (via context cancellation or channel close)
- Use `sync.WaitGroup` to wait for goroutine completion
- Use buffered channels when producer and consumer run at different speeds
- Never start a goroutine without knowing how it will stop

## Context Propagation

```go
func (s *Service) HandleRequest(ctx context.Context, req Request) (Response, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    user, err := s.store.GetUser(ctx, req.UserID)
    if err != nil {
        return Response{}, fmt.Errorf("getting user: %w", err)
    }

    ctx = context.WithValue(ctx, userKey, user)
    return s.processRequest(ctx, req)
}
```

Rules:
- Pass context as the first parameter of every function that does I/O
- Use `context.WithTimeout` or `context.WithDeadline` for all external calls
- Always `defer cancel()` after creating a cancellable context
- Use `context.WithValue` sparingly (request-scoped values only: trace IDs, auth info)
- Never store context in a struct

## Table-Driven Tests

```go
func TestValidateEmail(t *testing.T) {
    tests := []struct {
        name  string
        email string
        want  bool
    }{
        {"valid email", "user@example.com", true},
        {"missing @", "userexample.com", false},
        {"empty string", "", false},
        {"multiple @", "user@@example.com", false},
        {"valid with subdomain", "user@mail.example.com", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := ValidateEmail(tt.email)
            if got != tt.want {
                t.Errorf("ValidateEmail(%q) = %v, want %v", tt.email, got, tt.want)
            }
        })
    }
}
```

### Test Helpers
```go
func newTestServer(t *testing.T) *httptest.Server {
    t.Helper()
    handler := setupRoutes()
    srv := httptest.NewServer(handler)
    t.Cleanup(srv.Close)
    return srv
}

func assertEqual[T comparable](t *testing.T, got, want T) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}
```

Use `t.Helper()` in all test utility functions. Use `t.Cleanup()` instead of `defer` for test resource cleanup. Use `testdata/` directory for test fixtures.

## Module Management

```
go.mod structure:
module github.com/org/project

go 1.23

require (
    github.com/lib/pq v1.10.9
    golang.org/x/sync v0.7.0
)
```

Commands:
```bash
go mod tidy          # remove unused, add missing
go mod verify        # verify checksums
go list -m -u all    # check for updates
go get -u ./...      # update all dependencies
go mod vendor        # vendor dependencies (optional)
```

Use `go mod tidy` before every commit. Pin major versions. Review changelogs before updating.

## Zero-Value Design

Design types so their zero value is useful:

```go
// sync.Mutex zero value is an unlocked mutex (ready to use)
var mu sync.Mutex

// bytes.Buffer zero value is an empty buffer (ready to use)
var buf bytes.Buffer
buf.WriteString("hello")

// Custom types: make zero value meaningful
type Server struct {
    Addr    string        // defaults to ""
    Handler http.Handler  // defaults to nil
    Timeout time.Duration // defaults to 0 (no timeout)
}

func (s *Server) ListenAndServe() error {
    addr := s.Addr
    if addr == "" {
        addr = ":8080" // useful default
    }
    handler := s.Handler
    if handler == nil {
        handler = http.DefaultServeMux
    }
    // ...
}
```

Rules:
- Prefer structs with meaningful zero values over constructors
- Use pointer receivers when the method modifies the receiver
- Use value receivers when the method only reads
- Never export fields that users should not set directly; use constructor functions

## Structured Logging

```go
import "log/slog"

logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))

logger.Info("request handled",
    slog.String("method", r.Method),
    slog.String("path", r.URL.Path),
    slog.Int("status", status),
    slog.Duration("latency", time.Since(start)),
)
```

Use `log/slog` (standard library, Go 1.21+). Use structured fields, never string interpolation. Include request ID, user ID, and operation name in every log entry.

## Common Anti-Patterns

- Returning `interface{}` / `any` instead of concrete types
- Using `init()` for complex setup (makes testing hard)
- Ignoring errors with `_` without comment
- Using goroutines without lifecycle management
- Mutex contention from overly broad lock scope
- Channel misuse: prefer mutexes for simple shared state
- Naked returns in functions longer than a few lines
