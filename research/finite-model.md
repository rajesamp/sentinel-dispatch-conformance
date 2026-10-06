# Finite enumeration contract

This separate model enumerates every word of length zero through three over six
events after one approval: publish the original descriptor on c1; publish a changed
descriptor on c1; withdraw the tool; publish the original on c2; refresh an unrelated
server; and mutate the caller's argument dictionary. Thus 1+6+36+216=259 traces.
Each trace starts from one original descriptor and one request. A final execute
occurs after the trace. This is exhaustive within the declared alphabet and bound,
not exhaustive MCP concurrency or an independently sampled attack corpus.

An observed selected-binding descriptor/connection change or withdrawal revokes
the approval. Restoration cannot undo this revocation. Unrelated updates and
unpublished argument mutation preserve the original approved operation. A safe
completion must send the original frozen request; simply blocking all 259 traces
fails the expected-completion contract on the preserving traces.

The generator is independent of implementation decisions and imports no gate,
adapter or receipt oracle. It and its expectations were authored with knowledge of
the mechanism. The model is specification-driven conformance testing, not blind
holdout evaluation or public preregistration. The earlier 36 scenarios supply
complementary request replay, recovery, refresh-order, extension-field and source
alias checks outside this six-event alphabet. Report the two suites separately.

Limitations: serial event words; one tool and one intended call; two connection
labels; two descriptor values; no timed network failure, autonomous model, remote
code inspection, complete schema validator, unbounded concurrency or real secrets.
Thread-barrier tests separately examine selected validation/enqueue orderings.
