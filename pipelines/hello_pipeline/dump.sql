#Data dump for a given time-frame
SELECT
    created,
    id,
    happy,
    category,
    platform,
    browser,
    browser_version,
    channel,
    version,
    user_agent,
    description,
    url
FROM
    input.remote_feedback_response
WHERE
    product = 'Loop'
    AND DATE(created) >= :last_run_date
    AND DATE(created) <= :end_date
GROUP BY 1,2
ORDER BY 1
;