# Supplemental local subprocess transport check

This supplement tests whether the actual `BindingGate` supplied request bytes
cross a host/process boundary as intended. It uses an authored standard-library
fixture, not an external MCP SDK or a product interoperability test. It is kept
separate from the frozen designed-scenario and finite-enumeration results.

`integration/stdio_sink.py` is an inert child program. It accepts newline-delimited
JSON-RPC 2.0 `tools/call` requests for a fixed `read_file` fixture with object
arguments and returns a content item plus structured receipt. This is the narrow
tools/call message shape used for the 2025 protocol study; it omits protocol
initialization, capability negotiation, discovery, notifications, cancellation and
concurrent request management. It is not a complete MCP server or certification.
The named fixture never reads a file, runs code, or performs a network operation.
All supplied names and argument values remain inert data.

The parent launches two distinct trusted local processes per case with an isolated
Python interpreter. It assigns server/connection identities to these process
handles. The gate's writer chooses the handle by the supplied host identities,
writes exactly the supplied request bytes followed by one framing newline, and
reads one response. The child reports the exact received payload in base64, its
parsed request object and its PID. The parent checks the PID against the trusted
process handle rather than adopting a child-asserted server identity. PID checking
is local fixture instrumentation, not remote identity attestation.

At stdin EOF the child writes an independent audit record to stderr containing
received frame counts and ordered payload hashes. This allows revocation cases
to establish zero actual child frames, rather than infer non-dispatch solely from
a gate return value. Stdout contains only tool-call responses. The parent preserves
exact raw response lines, exact sent/echoed bytes, EOF audit bytes, child counts,
gate decisions, intended requests and each assertion in JSON output. One trailing
newline is transport framing and is excluded from the echoed payload hash.

Six checks run:

| Check | Intended observation |
|---|---|
| Normal and caller-mutated arguments | Two successful calls reach the selected child with identical originally approved bytes; post-prepare nested mutation does not alter the second call |
| Same name on distinct servers | Identical request bytes reach two different selected child processes, once each |
| Descriptor replacement | The stale permit is denied; both children independently report zero received frames |
| Connection replacement | The stale permit is denied after replacement with a second real process connection; neither child receives a frame |
| Single use | One permit emits one frame; its second use emits none |
| Legitimate reapproval | After descriptor and connection replacement, the stale permit is denied; fresh approval sends the newly authorized request only to the new child |

The gate uses its default structural admission callback in this supplement.
Semantic scanning is outside this transport check. Positive expectations are
recorded independently from gate return values. A missing/invalid response,
missing EOF audit, unexpected frame, unknown transport outcome, timeout or failed
child is a failed check; it is never credited as safe rejection.

Pipe writes and reads use nonblocking descriptors and POSIX selectors with a
shared request deadline (three seconds by default). Cleanup closes stdin, waits
for the EOF audit and reaps the child. A child that misses its cleanup deadline is
terminated and, if necessary, killed; only handles created by the fixture are
affected. Tests also exercise a silent child timeout and premature child exit.
The fixture is intended for this macOS/POSIX environment, not Windows pipe APIs.

The writer waits for the local receipt while inside the gate's serialized execute
call. This deliberately simple synchronous fixture does not establish the ideal
production lock scope, asynchronous transport correctness, remote authentication,
process isolation against a hostile operating system, or behavior of a remote tool
after delivery. No latency, throughput, memory or SDK performance measurement is
made here.

Run from the package root:

```sh
python3 -m unittest discover -s tests -p test_transport.py -v
python3 -m integration.check_transport
```

The second command emits the complete evidence object to stdout and exits nonzero
on any failure. A coordinator may capture stdout into a new supplemental artifact.
It includes interpreter version and hashes of the two transport fixture sources
and the actual gate source. Retain it alongside, rather than merge it into, the
previous frozen experiment's denominators or timing tables.
