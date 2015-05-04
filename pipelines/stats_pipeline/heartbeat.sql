SELECT
    survey_id,
    question_id,
    question_text,
    DATE(FROM_UNIXTIME(updated_ts/1000)) AS `date`,
    channel,
    version,
    platform,
    max_score,
    (score IS NOT Null) AS is_response,
    score,
    COUNT(*) AS volume
FROM
    heartbeat_answer
WHERE 
    NOT is_test
    AND updated_ts >= 1000*UNIX_TIMESTAMP(:start_date)
    AND updated_ts <= 1000*(UNIX_TIMESTAMP(:end_date)+24*60*60)
GROUP BY
    1,2,3,4,5,6,7,8,9,10
;