# Data Contract

## Required dimensions
- state_ut
- snapshot_date
- reporting_period

## Required measures
- received
- disposed
- pending_0_60
- pending_61_180
- pending_181_365
- pending_over_365

## Derived measures
pending_total = sum(ageing buckets)
disposal_rate = disposed / received * 100
pending_share = pending_total / received * 100
pressure_index = (received + pending_total) / max(disposed, 1)

## Data rules
- Preserve source values.
- Never silently replace missing values with zero.
- Keep source URL and source retrieval date.
- Validate non-negative numeric fields.
- Validate ageing total against pending total where the source exposes both.
