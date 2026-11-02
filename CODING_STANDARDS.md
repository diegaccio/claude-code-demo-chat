# Coding standards

The patterns the Demo app's code follows today. `bdg:review-changes` checks a change against them. Each rule names the code it comes from; when the code and a rule disagree, fix whichever is wrong in the same change.

## Structure

- **One package, one module per concern.** `src/demo_app/` holds `app.py` (the terminal UI), `chat.py` (the conversation), `openai_client.py` (the model server adapter), `settings.py` (configuration) and `theme.py` (the Notte theme). A new concern gets its own module; do not grow an existing one with unrelated code.
- **Dependencies point one way.** `app.py` depends on `chat.py` and `settings.py`; `openai_client.py` depends on `chat.py` and `settings.py`; `chat.py` depends on neither the UI nor the adapter. Do not import `app.py` or `openai_client.py` from `chat.py`.
- **Wire up at the edge only.** `main()` in `src/demo_app/__init__.py` is the one place that builds the real objects (`Settings`, the model client from `client_for`, `Chat`, `DemoApp`) and connects them. Everything else receives its collaborators as constructor arguments.
- **Every module opens with a one-line docstring** saying what it is for, and every public class and public method carries a short docstring (`chat.py`, `settings.py`). Private helpers need none.
- **Fully typed.** Annotate every parameter and return value, including `-> None`; code passes pyright in `standard` mode. Use `collections.abc` types (`AsyncIterator`, `Sequence`) in signatures, `Literal` for closed sets of values (`ProfileName`, `Message.role`) and `TypedDict` for plain data crossing a seam (`Message`).
- **Value objects are frozen dataclasses** (`ModelProfile`). Collaborators are plain classes with private attributes prefixed `_` and set in `__init__`.
- **Keyword-only for what is easy to swap.** Parameters of the same type, or that name a setting, are keyword-only: `Chat(client, *, model=...)`, `ModelClient.stream(*, model, messages)`.
- **Constants that explain a choice carry a comment saying why** (`_UNUSED_API_KEY`, `max_retries=0` in `openai_client.py`). Module-private names start with `_`.
- **Style is enforced by tools, not by hand.** ruff with its default rules plus import sorting; imports grouped standard library, third party, then `demo_app`. Do not silence a rule inline without a comment saying why.

## The chat seam

`chat.py` is the seam between the conversation and the model server.

- **`ModelClient` is a `Protocol`**: `stream(*, model, messages)` returns an `AsyncIterator[str]` of text chunks. `Chat` knows nothing about HTTP or any SDK's response types.
- **`Chat` owns the conversation history.** Callers send text with `Chat.send(text)` and never see or edit the message list; `Chat.load` hands back only the user/assistant `Turn`s (frozen question and answer) for the UI to replay.
- **Answers stream.** `send` is an async generator that yields each chunk as it arrives; the UI shows chunks as they come.
- **A turn is all or nothing.** The question and the full answer join the history only after the stream finishes; a failed turn leaves the history unchanged (`test_after_a_failed_turn_the_chat_goes_on_without_it`).
- **The next request carries the whole conversation so far**, in order, ending with the new question.

## The model client adapter

`openai_client.py` is the only module that imports the model SDK for requests.

- **It adapts the SDK to `ModelClient`**: it yields only non-empty text deltas and converts `Message` to the SDK's message type in a private function (`_to_openai`), with an exhaustive `match` on the role.
- **It reads its server from a `ModelProfile`** and accepts an optional `http_client`, so tests can inject a fake HTTP transport instead of patching.
- **No retries.** A failure is reported at once, in the chat.

## The UI seam

`app.py` is a Textual `App` that receives a `Chat` and a `ModelProfile`.

- **The UI never talks to the model client directly**; it consumes `Chat.send`.
- **Widgets are found by id** (`#wordmark`, `#status-bar`, `#prompt`, `#conversation`) and styled by class (`.turn`, `.user`, `.answer`, `.error`). Layout and colours live in the app's `CSS`, using theme variables (`$primary`, `$accent`, `$panel`, `$error`), never hard-coded colours.
- **Colours come from the theme.** `theme.py` defines the Notte theme once as a `Theme` constant; the app registers it and selects it on mount.
- **User and model text is shown literally**: turn widgets are created with `markup=False`, so text a user or a model writes is never read as markup.
- **A reply runs in a worker** (`run_worker(..., exclusive=True)`), so the UI stays responsive while the answer streams. The prompt is disabled while a reply is pending and re-enabled and re-focused in a `finally`, whatever happened.
- **Handlers return early on empty input** (`on_input_submitted`).

## Settings

`settings.py` reads configuration.

- **Settings are a pydantic-settings `Settings` class**, read from the environment and a local `.env`. `extra="ignore"` lets `.env` hold entries the current code does not use yet.
- **Names match `.env.example`.** A new setting is added to `Settings` and to `.env.example` in the same change, with its default and a comment.
- **Environment variable names are the public names** (`MODEL_PROFILE`, `LOCAL_BASE_URL`, `LOCAL_MODEL`); map them to Python field names with `validation_alias` when they differ.
- **Consumers get a `ModelProfile`**, built by `Settings.model_profile()`, not the settings object itself.
- **Defaults make the local setup work with no `.env`.** `.env` is never committed; secrets and server addresses that are not public go only in `.env`.

## Error handling

- **Errors that reach the user are `ChatError`.** `Chat.send` translates SDK errors into it, most specific first: connection failure, missing model, then any other API error, chaining the original with `from error`. A profile without a server URL gets `UnconfiguredModelClient`, which raises `ChatError` itself.
- **A `ChatError`'s text is ready to show the user**; the UI displays `str(error)` as it is, in an `.error` turn, and the app keeps running.
- **Catch specific exceptions** at the seam where they can be translated; do not use a bare `except` or swallow errors.
- **Cleanup that must always happen goes in `finally`** (`_reply` in `app.py`).

## Testing

Tests run with `uv run pytest`; `asyncio_mode = "auto"`, so async tests are plain `async def test_...` with no marker. No test needs a model server: tests pass with neither Ollama nor SRH reachable.

- **Test behaviour through public interfaces at a seam**, not private members. There are four seams, each with its test file:
  - the chat seam, `Chat` with a fake model client (`tests/test_chat.py`);
  - the UI seam, `DemoApp` driven with Textual's pilot (`tests/test_app.py`);
  - the model client adapter, against a fake HTTP server (`tests/test_openai_client.py`);
  - settings, with a controlled environment (`tests/test_settings.py`).
- **Use the fake model client** (`tests/fakes.py`, `FakeModelClient`) in place of the model server for the chat and UI seams. Give it `chunks` to stream and an optional `error` to raise after them; read `requests` to assert what the chat sent. Shared doubles live in `tests/fakes.py`.
- **Drive the UI with the pilot**: `async with app.run_test() as pilot`, click `#prompt`, press the keys, then `await app.workers.wait_for_complete()` and `await pilot.pause()` before asserting. Assert on what the user sees (the widgets' rendered text, focus, disabled state).
- **Fake the HTTP layer with `httpx2.MockTransport`** for the adapter, answering with server-sent events (`sse(...)` in `tests/test_openai_client.py`), and assert on the JSON request body as well as the result.
- **Keep the environment out of settings tests**: an autouse fixture changes to a temporary directory and removes the setting variables, so a developer's own `.env` or environment never changes the result.
- **Name a test after the behaviour it proves**, as a sentence (`test_next_turn_sends_the_whole_conversation_so_far`). Arrange, act, assert, with a blank line between the parts.
- **Test failures as well as the happy path**: unreachable server, missing model, other server errors, and the chat carrying on after a failed turn.
- **Tests are typed** like the source, and pass pyright and ruff.

## Validation

A change is done when these pass, in order (`docs/agents/validation.md`): `uv sync --locked`, `uv run pyright`, `uv run ruff check`, `uv run pytest`. Commit `uv.lock` with any dependency change.
