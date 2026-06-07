# Virtual memory / paging (OS concept)

The OS trick where a program sees one big continuous address space, but the OS splits it into fixed-size **pages** mapped to scattered physical RAM **frames** via a **page table**. This is exactly the idea vLLM borrows.
