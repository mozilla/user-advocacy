SELECT
    LEFT(t0.`date`,10) AS `date`,
    t0.version,
    t0.is_desktop,
    t0.input_average,
    t0.input_volume,
    t1.heartbeat_average,
    t1.heartbeat_surveyed_users,
    t1.heartbeat_volume
FROM
    (
        SELECT
            DATE(created)                                      AS `date`,
            CAST(SUBSTRING_INDEX(version, '.', 1) AS UNSIGNED) AS version,
            (product = 'Firefox' )                             AS is_desktop,
            AVG(happy)                                         AS input_average,
            COUNT(*)                                           AS input_volume
        FROM feedback_response
        WHERE
            product IN('Firefox for Android','Firefox')
            AND (source   IS Null OR source   = '')
            AND (campaign IS Null OR campaign = '')
            AND DATE(created) >= :start_date
            AND DATE(created) <= :end_date
        GROUP BY
            1,2,3
    ) t0
    LEFT JOIN
    (
        SELECT
            DATE(FROM_UNIXTIME(updated_ts/1000))               AS `date`,
            CAST(SUBSTRING_INDEX(version, '.', 1) AS UNSIGNED) AS version,
            AVG(score)                                         AS heartbeat_average,
            COUNT(*)                                           AS heartbeat_surveyed_users,
            COUNT(score)                                       AS heartbeat_volume
        FROM heartbeat_answer
        WHERE
            survey_id = 'heartbeat-by-user-first-impression'
            AND NOT is_test
            AND updated_ts >= 1000*UNIX_TIMESTAMP(:start_date)
            AND updated_ts <= 1000*(UNIX_TIMESTAMP(:end_date)+24*60*60)
        GROUP BY 1,2
    ) t1
    ON(t0.`date` = t1.`date` AND t0.version = t1.version)
;