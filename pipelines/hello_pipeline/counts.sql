SELECT
    DATE_SUB(DATE(created), INTERVAL ((7 + DAYOFWEEK(DATE(created)) - DAYOFWEEK(@start_date)) % 7) DAY ) AS `date`,
    IF(category = '', IF(happy,'happy','other'),category)                                                AS category,
    COUNT(*)                                                                                             AS cnt
FROM
    input.remote_feedback_response
WHERE
    product = 'Loop'
    AND DATE(created) >= :start_date
    AND DATE(created) <= :end_date
GROUP BY 1,2
ORDER BY 1
;