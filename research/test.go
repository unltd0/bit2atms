package taskqueue

import (
    "context"
    "fmt"
    "sync"
    "time"
)

type Priority int

const (
    Low    Priority = 1
    Medium Priority = 2
    High   Priority = 3
)

type Task struct {
    ID       string
    Fn       func(ctx context.Context) error
    Priority Priority
    MaxRetry int
    Timeout  time.Duration
}

type taskEntry struct {
    task    Task
    attempt int
}

type result struct {
    taskID string
    err    error
}

type Queue struct {
    high    chan taskEntry
    medium  chan taskEntry
    low     chan taskEntry
    results chan result
    workers int
    wg      sync.WaitGroup
    mu      sync.Mutex
    closed  bool
    done    chan struct{}
}

func NewQueue(workers, bufSize int) *Queue {
    q := &Queue{
        high:    make(chan taskEntry, bufSize),
        medium:  make(chan taskEntry, bufSize),
        low:     make(chan taskEntry, bufSize),
        results: make(chan result, bufSize),
        workers: workers,
        done:    make(chan struct{}),
    }
    q.start()
    return q
}

func (q *Queue) start() {
    for i := 0; i < q.workers; i++ {
        q.wg.Add(1)
        go q.worker()
    }
}

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

func (q *Queue) process(entry taskEntry) {
    ctx, cancel := context.WithTimeout(context.Background(), entry.task.Timeout)
    defer cancel()

    err := entry.task.Fn(ctx)
    if err != nil && entry.attempt < entry.task.MaxRetry {
        entry.attempt++
        q.requeue(entry)
        return
    }
    q.results <- result{taskID: entry.task.ID, err: err}
}

func (q *Queue) requeue(entry taskEntry) {
    switch entry.task.Priority {
    case High:
        q.high <- entry
    case Medium:
        q.medium <- entry
    case Low:
        q.low <- entry
    }
}

// Submit adds a task to the queue based on its priority.
func (q *Queue) Submit(task Task) error {
    q.mu.Lock()
    defer q.mu.Unlock()

    if q.closed {
        return fmt.Errorf("queue is closed")
    }

    entry := taskEntry{task: task, attempt: 0}
    switch task.Priority {
    case High:
        q.high <- entry
    case Medium:
        q.medium <- entry
    case Low:
        q.low <- entry
    default:
        return fmt.Errorf("unknown priority: %d", task.Priority)
    }
    return nil
}

// Results returns the results channel for consuming task outcomes.
func (q *Queue) Results() <-chan result {
    return q.results
}

// Shutdown stops accepting new tasks and waits for workers to finish.
func (q *Queue) Shutdown() {
    q.mu.Lock()
    q.closed = true
    q.mu.Unlock()

    close(q.done)
    q.wg.Wait()
    close(q.results)
}

// Len returns the total number of pending tasks across all queues.
func (q *Queue) Len() int {
    return len(q.high) + len(q.medium) + len(q.low)
}