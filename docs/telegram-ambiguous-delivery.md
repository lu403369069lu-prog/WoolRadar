# W1 Telegram ambiguous-delivery containment (isolated candidate)

Default: telegram_delivery_mode = quarantine (also applied when key is omitted). After an uncertain transport outcome the SQLite row remains UNCERTAIN; an abandoned/exhausted CLAIMED row is retained. Subsequent flush() calls count them in held but never silently replay them. A callback returning generic FAILED is also ambiguous and held. An authoritative Telegram rate-limit/429 is eligible for bounded retry.

Trade-off: delivery may never occur if a worker crashed before sending, or if an ACK was lost after Telegram accepted it. No Telegram sendMessage idempotency key, provider lookup, or durable provider receipt is present; therefore **end-to-end exactly-once is NOT established**. Do not set SENT without external evidence; do not automatically clear either status. Require a separate authorized reconciliation process with a retained human decision and supporting external evidence before retry/discard. Retries explicitly requested with telegram_delivery_mode = at_least_once restore old availability-oriented behavior but may duplicate.

This patch changes default behavior only in the proposed draft, not a running instance. All tests use synthetic callbacks, isolated temporary SQLite databases, and no actual Telegram token or send.
