SELECT
    DATE_SUB(DATE(created), INTERVAL ((7 + DAYOFWEEK(DATE(created)) - DAYOFWEEK(@start_date)) % 7) DAY ) AS `date`,
    description                                       AS description,
    COUNT(*)                                          AS cnt
FROM
    input.remote_feedback_response
WHERE
    DATE(created) >= @start_date
    AND DATE(created) <= @end_date
    AND product = 'Loop'
    AND category = 'other'
GROUP BY 1,2
ORDER BY 1
;