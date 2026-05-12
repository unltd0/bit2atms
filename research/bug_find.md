# Bug analysis: `test.go`

Focus question: **Can a `send on closed channel` panic occur on `q.results` after `Shutdown` closes it at line 144?**

---

## The proposed panic scenario

The hypothesis was:

> A worker picks up a task → `Shutdown` fires → `close(q.done)` → worker finishes `process` → sends to `q.results` → panic: send on closed channel.
>
> `wg.Wait()` doesn't help because `wg.Done()` is called in `worker()` only in the `done` case, but an in-flight `process` call hasn't returned yet when `done` is received.

Code under examination:

```go
// worker (lines 68–82)
func (q *Queue) worker() {
    for {
        select {
        case entry := <-q.high:
            q.process(entry)
        case entry := <-q.medium:
            q.process(entry)
        case entry := <-q.low:
            q.process(entry)
        case <-q.done:
            q.wg.Done()
            return
        }
    }
}

// process (line 94)
q.results <- result{taskID: entry.task.ID, err: err}

// Shutdown (lines 137–145)
func (q *Queue) Shutdown() {
    q.mu.Lock()
    q.closed = true
    q.mu.Unlock()

    close(q.done)
    q.wg.Wait()
    close(q.results)
}
```

---

## Verdict: **The panic does not occur. The bug described is not present.**

To be precise: line 144 itself runs normally — `Shutdown` reaches `close(q.results)` and completes. What cannot happen is a `q.results <- ...` send racing with that close. The `wg.Wait()` on line 143 enforces the ordering that prevents the panic.

### Why

`wg.Done()` is called exclusively inside the `<-q.done` branch of the worker's `select`. The `select` only evaluates a new case after the current case body finishes. Therefore:

- While a worker is inside `process(entry)`, it has **not** yet returned to the `select`, has **not** yet observed `q.done`, and has **not** yet called `wg.Done()`.
- `wg.Wait()` in `Shutdown` blocks until **every** worker has called `wg.Done()`.
- Consequently, `close(q.results)` at line 144 cannot execute until every worker has fully exited any in-flight `process(...)` call — including the `q.results <- ...` send on line 94.

### Trace that confirms safety

```
T1 (worker A):   select fires → case entry := <-q.high
T1 (worker A):   enters process(entry)
T1 (worker A):   running entry.task.Fn(ctx)  ← slow user code
T2 (caller):     Shutdown() → close(q.done)
T2 (caller):     wg.Wait()  ← blocks; T1 has not called wg.Done()
T1 (worker A):   Fn returns
T1 (worker A):   q.results <- result{...}   ← SAFE: results not closed yet
T1 (worker A):   process returns
T1 (worker A):   back to for-loop, select picks <-q.done
T1 (worker A):   wg.Done(); return
T2 (caller):     wg.Wait() unblocks once all workers have Done'd
T2 (caller):     close(q.results)            ← runs only after all sends finished
```

The `sync.WaitGroup` ordering is sufficient: as long as `wg.Done()` is called only **after** any possible `q.results <- ...` send on the same goroutine, `close(q.results)` is guaranteed to run after the last send.

In this code, that ordering holds because:

1. The only sender to `q.results` is `process`.
2. `process` is only ever called synchronously from the worker's `select` body.
3. `wg.Done()` is only ever called from the `<-q.done` branch, which is mutually exclusive with the `process` branches in the same iteration.

So the panic-on-send scenario described above **cannot occur** with the current code.

---

## Other bugs

These are unrelated to the panic question, but worth noting.

### 1. In-flight retries can livelock past shutdown (minor)

After `process` fails and calls `requeue`, the worker returns to its `select`. With `q.done` already closed, both `q.done` and the requeued item's channel (e.g. `q.high`) are ready. Go's `select` picks **uniformly at random** — so a failing task may be retried 0–N more times after shutdown is requested, depending on dice. Surprising, but not a panic.

### 2. Buffered tasks are silently dropped on shutdown

Tasks sitting in `q.high` / `q.medium` / `q.low` buffers when `close(q.done)` fires may never be processed. As workers loop, the `select` probabilistically picks `<-q.done` and the worker exits. No result is ever emitted for those tasks, and `Results()` consumers have no way to detect the loss.

### 3. `Submit` can block forever past `Shutdown`

`Submit` checks `q.closed` under the mutex, then sends to a buffered channel. If a caller is mid-send on a full channel when `Shutdown` runs, the caller has already passed the closed-check; meanwhile workers exit and the buffer is never drained. The send blocks forever. (Consequence: caller goroutine leak, not a panic.)

### 4. `requeue` can deadlock `Shutdown` — **the real shutdown hazard**

`requeue` (line 97) unconditionally sends to `q.high` / `q.medium` / `q.low`:

```go
func (q *Queue) requeue(entry taskEntry) {
    switch entry.task.Priority {
    case High:
        q.high <- entry
    ...
    }
}
```

After `close(q.done)`, those channels have no guaranteed readers. If the relevant buffer is **full** at the moment `requeue` is called from inside `process`:

- The send blocks indefinitely.
- The worker never returns from `process`, never reaches the `<-q.done` case, never calls `wg.Done()`.
- `Shutdown`'s `wg.Wait()` blocks forever.

This is a genuine deadlock, not a panic, but it's the most serious correctness issue in `Shutdown`.

### 5. `result` and related types are unexported but `Results()` returns them

`Results() <-chan result` returns a channel of an unexported type. External callers can receive but cannot name the type without reflection or type inference quirks. Likely an oversight — `result` should be exported (or replaced with an exported struct).
