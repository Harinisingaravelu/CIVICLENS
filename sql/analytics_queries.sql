-- CIVICLENS analytical queries
SELECT state_ut, received, disposed, pending_total,
       ROUND(100.0 * disposed / NULLIF(received,0), 2) AS disposal_rate
FROM cpgrams_snapshot
ORDER BY pending_total DESC;

SELECT state_ut, pending_0_60, pending_61_180, pending_181_365, pending_over_365
FROM cpgrams_snapshot
ORDER BY pending_181_365 + pending_over_365 DESC;

-- Do not interpret disposal rate as an independent performance score.
