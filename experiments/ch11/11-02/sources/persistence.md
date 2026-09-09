> ## Documentation Index
> Fetch the complete documentation index at: https://docs.e2b.dev/llms.txt
> Use this file to discover all available pages before exploring further.

# Sandbox persistence

> Pause a sandbox and resume it later from the exact state it was in, including the filesystem and the memory, so running processes and loaded variables survive. A paused sandbox is kept indefinitely with no automatic deletion.

The sandbox persistence allows you to pause your sandbox and resume it later from the same state it was in when you paused it.

This includes not only state of the sandbox's filesystem but also the sandbox's memory. This means all running processes, loaded variables, data, etc.

A paused sandbox is kept **indefinitely**. There is no time-to-live and no automatic deletion, and E2B never kills a paused sandbox on its own. It is removed only when you explicitly kill it. See [How long does a sandbox live?](/faq/sandbox-lifetime).

## Sandbox state transitions

Understanding how sandboxes transition between different states is crucial for managing their lifecycle effectively. Here's a diagram showing the possible state transitions:

```mermaid actions={false} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
flowchart TD
    start(( )) -->|Sandbox.create| Running

    Running["<b>Running</b><br/>• Active execution<br/>• Consumes resources"]
    Paused["<b>Paused</b><br/>• Preserves memory and files<br/>• Cannot execute code"]
    Snapshotting["<b>Snapshotting</b><br/>• Creates persistent snapshot<br/>• Briefly pauses execution"]
    Killed["<b>Killed</b><br/>• Resources released<br/>• Cannot be resumed"]

    Running -->|pause| Paused
    Running -->|createSnapshot| Snapshotting
    Paused -->|connect| Running
    Snapshotting -->|snapshot complete| Running
    Running -->|kill| Killed
    Paused -->|kill| Killed
```

### State descriptions

* **Running**: The sandbox is actively running and can execute code. This is the initial state after creation.
* **Paused**: The sandbox execution is suspended but its state is preserved.
* **Snapshotting**: The sandbox is briefly paused while a persistent snapshot is being created. It automatically returns to Running. See [Snapshots](/sandbox/snapshots).
* **Killed**: The sandbox is terminated and all resources are released. This is a terminal state.

### Changing sandbox's state

<CodeGroup>
  ```js JavaScript & TypeScript theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox } from 'e2b'

  const sandbox = await Sandbox.create() // Starts in Running state

  // Pause the sandbox
  await sandbox.pause() // Running → Paused

  // Resume the sandbox
  await sandbox.connect() // Running/Paused → Running

  // Kill the sandbox (from any state)
  await sandbox.kill() // Running/Paused → Killed
  ```

  ```python Python theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  from e2b import Sandbox

  sandbox = Sandbox.create()  # Starts in Running state

  # Pause the sandbox
  sandbox.pause()  # Running → Paused

  # Resume the sandbox
  sandbox.connect()  # Running/Paused → Running

  # Kill the sandbox (from any state)
  sandbox.kill()  # Running/Paused → Killed
  ```
</CodeGroup>

## Pausing sandbox

When you pause a sandbox, both the sandbox's filesystem and memory state will be saved. This includes all the files in the sandbox's filesystem and all the running processes, loaded variables, data, etc.

<CodeGroup>
  ```js JavaScript & TypeScript highlight={8-9} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox } from 'e2b'

  const sbx = await Sandbox.create()
  console.log('Sandbox created', sbx.sandboxId)

  // Pause the sandbox
  // You can save the sandbox ID in your database to resume the sandbox later
  await sbx.pause()
  console.log('Sandbox paused', sbx.sandboxId)
  ```

  ```python Python highlight={8-9} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  from e2b import Sandbox

  sbx = Sandbox.create()
  print('Sandbox created', sbx.sandbox_id)

  # Pause the sandbox
  # You can save the sandbox ID in your database to resume the sandbox later
  sbx.pause()
  print('Sandbox paused', sbx.sandbox_id) 
  ```
</CodeGroup>

By default a pause saves **both** the filesystem and the memory. To save only the filesystem — a lighter snapshot that cold-boots (reboots) on resume — pass `keepMemory: false` (JavaScript) / `keep_memory=False` (Python). See [Filesystem-only snapshots](/sandbox/filesystem-only-snapshots).

### When a pause is refused

<Info>
  Rolling out. The refusal behavior below is being enabled region by region. Until it reaches your region, a pause in this situation fails with a `500` error instead. `ServiceBusyError` and `ServiceBusyException` ship in the next minor release of the JavaScript and Python SDKs.
</Info>

A pause can be refused when the node running the sandbox is still finishing the previous snapshot of the same sandbox. Instead of failing the sandbox, the API answers with HTTP `503` and the sandbox **keeps running with its state intact**. Nothing was paused and nothing was lost. The SDKs surface this as `ServiceBusyError` (JavaScript) / `ServiceBusyException` (Python), the same error every other 503 from the API raises, for example when there is no capacity to place a new sandbox.

The right reaction is to retry the pause after a short wait, or simply to keep using the sandbox and pause it later:

<CodeGroup>
  ```js JavaScript & TypeScript highlight={7-12} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox, ServiceBusyError } from 'e2b'

  const sbx = await Sandbox.create()

  try {
    await sbx.pause()
  } catch (error) {
    if (error instanceof ServiceBusyError) {
      // The sandbox is still running; try again in a few seconds
      await new Promise((resolve) => setTimeout(resolve, 5_000))
      await sbx.pause()
    } else {
      throw error
    }
  }
  ```

  ```python Python highlight={8-11} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import time
  from e2b import Sandbox, ServiceBusyException

  sbx = Sandbox.create()

  try:
      sbx.pause()
  except ServiceBusyException:
      # The sandbox is still running; try again in a few seconds
      time.sleep(5)
      sbx.pause()
  ```
</CodeGroup>

`ServiceBusyError` / `ServiceBusyException` is not a `SandboxError` / `SandboxException`, so catch it explicitly. Every SDK error raised from an API response also carries the HTTP status as `statusCode` (JavaScript) / `status_code` (Python) if you prefer to branch on the status. SDK versions that predate `ServiceBusyError` raise a generic `SandboxError` / `SandboxException` whose message starts with `503:`.

## Resuming sandbox

When you resume a sandbox, it will be in the same state it was in when you paused it.
This means that all the files in the sandbox's filesystem will be restored and all the running processes, loaded variables, data, etc. will be restored.

<CodeGroup>
  ```js JavaScript & TypeScript highlight={12-13} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox } from 'e2b'

  const sbx = await Sandbox.create()
  console.log('Sandbox created', sbx.sandboxId)

  // Pause the sandbox
  // You can save the sandbox ID in your database to resume the sandbox later
  await sbx.pause()
  console.log('Sandbox paused', sbx.sandboxId)

  // Connect to the sandbox (it will automatically resume the sandbox, if paused)
  const sameSbx = await sbx.connect()
  console.log('Connected to the sandbox', sameSbx.sandboxId)
  ```

  ```python Python highlight={12-13} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  from e2b import Sandbox

  sbx = Sandbox.create()
  print('Sandbox created', sbx.sandbox_id)

  # Pause the sandbox
  # You can save the sandbox ID in your database to resume the sandbox later
  sbx.pause()
  print('Sandbox paused', sbx.sandbox_id)

  # Connect to the sandbox (it will automatically resume the sandbox, if paused)
  same_sbx = sbx.connect()
  print('Connected to the sandbox', same_sbx.sandbox_id)
  ```
</CodeGroup>

## Listing paused sandboxes

You can list all paused sandboxes by calling the `Sandbox.list` method and supplying the `state` query parameter.
More information about using the method can be found in [List Sandboxes](/sandbox/list).

<CodeGroup>
  ```js JavaScript & TypeScript highlight={4,7} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox, SandboxInfo } from 'e2b'

  // List all paused sandboxes
  const paginator = Sandbox.list({ query: { state: ['paused'] } })

  // Get the first page of paused sandboxes
  const sandboxes = await paginator.nextItems()

  // Get all paused sandboxes
  while (paginator.hasNext) {
    const items = await paginator.nextItems()
    sandboxes.push(...items)
  }
  ```

  ```python Python highlight={4,7} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  # List all paused sandboxes
  from e2b import Sandbox, SandboxQuery, SandboxState

  paginator = Sandbox.list(SandboxQuery(state=[SandboxState.PAUSED]))

  # Get the first page of paused sandboxes
  sandboxes = paginator.next_items()

  # Get all paused sandboxes
  while paginator.has_next:
    items = paginator.next_items()
    sandboxes.extend(items)
  ```
</CodeGroup>

## Removing paused sandboxes

You can remove paused sandboxes by calling the `kill` method on the Sandbox instance.

<CodeGroup>
  ```js JavaScript & TypeScript highlight={11,14} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox } from 'e2b'

  const sbx = await Sandbox.create()
  console.log('Sandbox created', sbx.sandboxId)

  // Pause the sandbox
  // You can save the sandbox ID in your database to resume the sandbox later
  await sbx.pause()

  // Remove the sandbox
  await sbx.kill()

  // Remove sandbox by id
  await Sandbox.kill(sbx.sandboxId)
  ```

  ```python Python highlight={9,12} theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  from e2b import Sandbox

  sbx = Sandbox.create()

  # Pause the sandbox
  sbx.pause()

  # Remove the sandbox
  sbx.kill()

  # Remove sandbox by id
  Sandbox.kill(sbx.sandbox_id)
  ```
</CodeGroup>

## Sandbox's timeout

When connecting to a sandbox, the timeout is not reset. `Sandbox.connect()` only ever extends the sandbox's lifetime - the new expiry is the later of the current expiry and now plus the timeout you pass (default 5 minutes). So a sandbox with 20 minutes left stays at 20 minutes even if you connect with the default timeout, while a sandbox with only 1 minute left is bumped up to 5. To set an exact timeout that can also shorten the remaining lifetime, use `setTimeout()` / `set_timeout()` instead.

<CodeGroup>
  ```js JavaScript & TypeScript theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox } from 'e2b'

  const sbx = await Sandbox.connect(sandboxId, { timeoutMs: 60 * 1000 }) // 60 seconds
  ```

  ```python Python theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  from e2b import Sandbox

  sbx = Sandbox.connect(sandbox_id, timeout=60) # 60 seconds
  ```
</CodeGroup>

### Auto-pause

Auto-pause is configured in the sandbox lifecycle on create. `onTimeout`/`on_timeout` defaults to `"kill"`, meaning the sandbox is terminated when its timeout expires. Set it to `"pause"` to auto-pause on timeout instead.

<CodeGroup>
  ```js JavaScript & TypeScript theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  import { Sandbox } from 'e2b'

  const sandbox = await Sandbox.create({
    timeoutMs: 10 * 60 * 1000, // Optional: change default timeout (10 minutes)
    lifecycle: {
      onTimeout: 'pause', // Defaults to 'kill'; set to 'pause' to auto-pause on timeout
      autoResume: false, // Optional (default is false)
    },
  })
  ```

  ```python Python theme={"theme":{"light":"github-light","dark":"github-dark-default"}}
  from e2b import Sandbox

  sandbox = Sandbox.create(
      timeout=10 * 60,  # Optional: change default timeout (10 minutes)
      lifecycle={
          "on_timeout": "pause",  # Defaults to "kill"; set to "pause" to auto-pause on timeout
          "auto_resume": False,   # Optional (default is False)
      },
  )
  ```
</CodeGroup>

Auto-pause is persistent, meaning if your sandbox resumes and later times out again, it will pause again.

If the node refuses a memory auto-pause because it is still finishing the sandbox's previous snapshot, E2B keeps the sandbox running and retries the pause for up to about two minutes past its timeout. Only if the node keeps refusing for that whole window is the sandbox paused **filesystem-only**: the disk is preserved and the next resume reboots the sandbox, so the memory state is lost. Under normal conditions this never happens. It protects your sandbox during snapshot backlogs on a node, where the alternative would be losing the sandbox entirely. This behavior is rolling out region by region together with the refusal handling above.

To make the auto-pause filesystem-only — dropping memory so resume cold-boots — use the object form `onTimeout: { action: 'pause', keepMemory: false }` (JavaScript) / `"on_timeout": {"action": "pause", "keep_memory": False}` (Python). See [Filesystem-only snapshots](/sandbox/filesystem-only-snapshots).

If you call `.kill()`, the sandbox is permanently deleted and cannot be resumed.

For auto-resume behavior, see [AutoResume](/sandbox/auto-resume).

## Network

If you have a service (for example a server) running inside your sandbox and you pause the sandbox, the service won't be accessible from the outside and all the clients will be disconnected.
If you resume the sandbox, the service will be accessible again but you need to connect clients again.

## Limitations

### Pause and resume performance

* Pausing a sandbox takes approximately **4 seconds per 1 GiB of RAM**
* Resuming a sandbox takes approximately **1 second**

### Paused sandbox retention

* Paused sandboxes are kept **indefinitely**; there is no automatic deletion or time-to-live limit
* There is currently **no configurable "auto-kill after N days" option**; a paused sandbox will not expire on its own
* You can resume a paused sandbox at any time
* To remove a paused sandbox, you must kill it explicitly with an API call (`sandbox.kill()` / `Sandbox.kill(sandboxId)`), as shown in [Removing paused sandboxes](#removing-paused-sandboxes)

### Continuous runtime limits

* A sandbox can remain running (without being paused) for:
  * **24 hours** on the **Pro tier**
  * **1 hour** on the **Hobby tier**
* After a sandbox is paused and resumed, the continuous runtime limit is **reset**
