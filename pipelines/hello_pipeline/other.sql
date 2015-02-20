#Generates the "other" verbatims for each week
SELECT
    DATE_SUB(#round to week
            DATE(created), 
            INTERVAL ((7 + DAYOFWEEK(DATE(created)) - DAYOFWEEK(:start_date)) % 7) DAY 
        ) AS `date`,
    description AS description,
    COUNT(*)    AS cnt
FROM
    remote_feedback_response
WHERE
    product = 'Loop'
    AND category = 'other'
    AND DATE(created) >= :start_date
    AND DATE(created) <= :end_date
GROUP BY 1,2
ORDER BY 1
;