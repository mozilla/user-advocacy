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
    LEFT(created,10) = LEFT(@end_date,10)
    AND product = 'Loop'
GROUP BY 1,2
ORDER BY 1
;