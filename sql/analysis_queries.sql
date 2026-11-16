-- PostgreSQL starter queries for an Order-to-Cash event log.
-- Assumed table: event_log(case_id, activity, timestamp, customer_id, region, order_value)

-- 1. Event count and distinct cases by activity.
SELECT activity, COUNT(*) AS event_count, COUNT(DISTINCT case_id) AS cases
FROM event_log
GROUP BY activity
ORDER BY event_count DESC;

-- 2. Reconstruct each case's activity sequence.
SELECT case_id,
       STRING_AGG(activity, ' -> ' ORDER BY timestamp) AS process_variant
FROM event_log
GROUP BY case_id;

-- 3. Calculate time between consecutive activities within each case.
WITH ordered_events AS (
    SELECT case_id, activity, timestamp,
           LEAD(activity) OVER (PARTITION BY case_id ORDER BY timestamp) AS next_activity,
           LEAD(timestamp) OVER (PARTITION BY case_id ORDER BY timestamp) AS next_timestamp
    FROM event_log
), transitions AS (
    SELECT *, EXTRACT(EPOCH FROM (next_timestamp - timestamp)) / 3600.0 AS wait_hours
    FROM ordered_events
    WHERE next_timestamp IS NOT NULL
)
SELECT activity, next_activity, COUNT(*) AS transition_count,
       ROUND(AVG(wait_hours)::numeric, 2) AS avg_wait_hours
FROM transitions
GROUP BY activity, next_activity
ORDER BY avg_wait_hours DESC;

-- 4. Calculate case cycle time and final activity.
WITH ranked AS (
    SELECT case_id, activity, timestamp,
           ROW_NUMBER() OVER (PARTITION BY case_id ORDER BY timestamp DESC) AS rn,
           MIN(timestamp) OVER (PARTITION BY case_id) AS start_time,
           MAX(timestamp) OVER (PARTITION BY case_id) AS end_time
    FROM event_log
)
SELECT case_id, activity AS final_activity,
       ROUND((EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0)::numeric, 2) AS cycle_time_hours
FROM ranked
WHERE rn = 1;

-- 5. Identify repeated activities (potential rework; validate business meaning).
SELECT case_id, activity, COUNT(*) AS occurrences
FROM event_log
GROUP BY case_id, activity
HAVING COUNT(*) > 1
ORDER BY occurrences DESC, case_id;

-- 6. Illustrative delivered orders exceeding a 72-hour cycle-time threshold.
WITH case_times AS (
    SELECT case_id, MIN(timestamp) AS start_time, MAX(timestamp) AS end_time,
           (ARRAY_AGG(activity ORDER BY timestamp DESC))[1] AS final_activity
    FROM event_log
    GROUP BY case_id
)
SELECT case_id,
       ROUND((EXTRACT(EPOCH FROM (end_time - start_time)) / 3600.0)::numeric, 2) AS cycle_time_hours
FROM case_times
WHERE final_activity = 'Delivered'
  AND end_time - start_time > INTERVAL '72 hours'
ORDER BY cycle_time_hours DESC;
