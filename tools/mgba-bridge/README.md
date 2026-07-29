# mGBA loopback bridge (Phase 3A)

This directory contains the Phase 3A bridge spike. It proves that mGBA can
exchange a bounded, local request/response with a deterministic responder. It
is **not an AI service**. The responder always chooses legal-action index `0`.
The Phase 3A ROM deliberately ignores `READY`, so Calvin continues to use the
existing vanilla trainer AI.

## Safety boundary

- The Lua listener host is fixed to `127.0.0.1`; do not change it to a LAN or
  public address. Its default port is `57621` and may be changed only in
  `bridge_settings.lua`; start the responder with the matching `--port` value.
- `generated/mailbox_address.lua` is derived from the current ELF, is ignored
  by Git, and must never be committed or reused after rebuilding the ROM.
- The Lua script reads only the documented mailbox header fields and writes
  only response sequence, action index, then `READY`.
- One Lua process accepts one responder client. After that client disconnects,
  restart mGBA and reload the script before starting another responder.

## Validated emulator

Manual bridge checks used Windows 64-bit **mGBA 0.10.5** (the version shown in
the mGBA title bar). For any repeat verification, record the hash of the
executable actually run, not an archive hash:

```powershell
Get-FileHash -Algorithm SHA256 'C:\path\to\mGBA.exe'
& 'C:\path\to\mGBA.exe' --version
```

The exact executable path and SHA-256 belong in the evidence review. On the
validated Windows build, the `--version` invocation returned no console output;
record the mGBA title-bar version instead. Do not treat a download/archive
checksum as proof of the executable that ran the Lua script.

## Launch a valid round trip

1. Build and generate the mailbox address in WSL, from the repository root:

   ```bash
   make -j16
   python3 tools/mgba-bridge/generate_mailbox_config.py --elf pokeemerald.elf
   ```

2. In Windows PowerShell, start the deterministic responder and leave the
   window open. It stays quiet while waiting for requests:

   ```powershell
   cd C:\Users\jerem\Documents\Github\pokeemerald-expansion
   py -3 tools\mgba-bridge\test_responder.py
   ```

3. Open the newly built `pokeemerald.gba` in Windows mGBA. Select **Tools →
   Scripting…**, then load `tools\mgba-bridge\mgba_bridge.lua`.

4. Expected scripting-console startup lines:

   ```text
   BAGB listener ready 127.0.0.1:57621
   BAGB client connected
   ```

5. Fight Youngster Calvin. On each eligible trainer decision, expect matching
   lines such as:

   ```text
   BAGB request forwarded: 1
   BAGB response written: 1
   ```

   The battle must remain interactive and Calvin must still act through
   vanilla trainer AI. A response write demonstrates only the bridge transport;
   it does not control the move in Phase 3A.

## Safe failure behavior

With no responder, only the listener startup line is expected; the battle must
remain playable and no response is written. If a connected responder exits,
Lua logs a bounded `BAGB client disconnected: ...` reason and writes no later
response. Stale sequences, an index outside the legal count, malformed lines,
and a non-`BAGB/1` protocol line are rejected without a response write.

To stop, close mGBA first, then stop the responder with `Ctrl+C`. Start a
fresh mGBA/script pair for a new client session.

## Manual rejection matrix

Use a **fresh mGBA/script session for every case** below: the Lua listener
accepts only one client. Do **not** start `test_responder.py`. Load the script,
start the listed local PowerShell client, then fight Calvin. Each case must
leave the battle playable and produce no `BAGB response written` line.
The examples use the default `$port=57621`; change that value if
`bridge_settings.lua` uses a different port.

The stale reply intentionally does not use the current request sequence:

```powershell
$port=57621;$c=[Net.Sockets.TcpClient]::new('127.0.0.1',$port);$s=$c.GetStream();$r=[IO.StreamReader]::new($s,[Text.Encoding]::ASCII);$w=[IO.StreamWriter]::new($s,[Text.Encoding]::ASCII);$w.AutoFlush=$true;$null=$r.ReadLine();$w.Write("BAGB/1 RESPONSE 999 0`n");Start-Sleep 2;$c.Dispose()
```

For an out-of-range action index, use the current sequence with index `4`:

```powershell
$port=57621;$c=[Net.Sockets.TcpClient]::new('127.0.0.1',$port);$s=$c.GetStream();$r=[IO.StreamReader]::new($s,[Text.Encoding]::ASCII);$w=[IO.StreamWriter]::new($s,[Text.Encoding]::ASCII);$w.AutoFlush=$true;$q=$r.ReadLine();$n=($q -split ' ')[2];$w.Write("BAGB/1 RESPONSE $n 4`n");Start-Sleep 2;$c.Dispose()
```

For a malformed sequence token:

```powershell
$port=57621;$c=[Net.Sockets.TcpClient]::new('127.0.0.1',$port);$s=$c.GetStream();$r=[IO.StreamReader]::new($s,[Text.Encoding]::ASCII);$w=[IO.StreamWriter]::new($s,[Text.Encoding]::ASCII);$w.AutoFlush=$true;$null=$r.ReadLine();$w.Write("BAGB/1 RESPONSE nope 0`n");Start-Sleep 2;$c.Dispose()
```

For a wrong protocol version, use the current sequence with `BAGB/2`:

```powershell
$port=57621;$c=[Net.Sockets.TcpClient]::new('127.0.0.1',$port);$s=$c.GetStream();$r=[IO.StreamReader]::new($s,[Text.Encoding]::ASCII);$w=[IO.StreamWriter]::new($s,[Text.Encoding]::ASCII);$w.AutoFlush=$true;$q=$r.ReadLine();$n=($q -split ' ')[2];$w.Write("BAGB/2 RESPONSE $n 0`n");Start-Sleep 2;$c.Dispose()
```

Expected console results are a rejected response or malformed-client
disconnect. In every case, the valid fallback is unchanged gameplay with no
mailbox response write.

## Automated checks

Run the bridge parser and generator tests in Windows PowerShell:

```powershell
py -3 -B tools\mgba-bridge\tests\test_bridge_protocol.py -v
py -3 -B tools\mgba-bridge\tests\test_generate_mailbox_config.py -v
py -3 -B tools\mgba-bridge\tests\test_mgba_bridge_source.py -v
```

Run the ROM regression checks in WSL:

```bash
make -j16 check TESTS='External AI'
make -j16
```

Phase 3A verification is recorded in the [evidence
review](../../docs/openai-battle-agent/reviews/2026-07-29-phase-3a-mgba-loopback-bridge-evidence.md).
The next phase requires a separately reviewed full-snapshot local-service
protocol and ROM-side response acceptance; this deterministic responder is not
that service.
