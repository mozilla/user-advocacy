REPLACE INTO daily_mobile_stats (
        `date`,
        days_since_epoch,
        version,
        channel,
        input_average, 
        input_average_7_days,
        input_volume, 
        sumo_posts, 
        sumo_unanswered_3_days,
        sumo_in_product_views,
        adis, 
        play_average, 
        play_volume, 
        heartbeat_average, 
        heartbeat_volume
    )
SELECT
    base.`date`                                 AS `date`,
    base.days_since_epoch                       AS days_since_epoch,
    base.version                                AS version,
    base.channel                                AS channel,
    COALESCE(input.input_average,0)             AS input_average,
    Null                                        AS input_average_7_days,
    COALESCE(input.input_volume,0)              AS input_volume,
    COALESCE(sumo.num_posts,0)                  AS sumo_posts,
    COALESCE(sumo.num_unanswered_72,0)          AS sumo_unanswered_3_days,
    COALESCE(visits.visits,0)                   AS sumo_in_product_views,
    COALESCE(adis.num_adis,0)                   AS adis,
    COALESCE(play.play_average,0)               AS play_average, 
    COALESCE(play.play_volume,0)                AS play_volume, 
    Null                                        AS heartbeat_average,
    Null                                        AS heartbeat_volume
FROM
    tmp_base base
    LEFT JOIN tmp_input input           
            ON(base.version = input.version     AND base.`date` = input.`date`  AND base.is_desktop = input.is_desktop)
    LEFT JOIN tmp_sumo sumo             
            ON(base.version = sumo.version      AND base.`date` = sumo.`date`   AND base.is_desktop = sumo.is_desktop)
    LEFT JOIN tmp_adis adis             
            ON(base.version = adis.version      AND base.`date` = adis.`date`   AND base.is_desktop = adis.is_desktop)
    LEFT JOIN tmp_sumo_visits visits 
            ON(base.version = visits.version    AND base.`date` = visits.`date` AND base.is_desktop = visits.is_desktop)
    LEFT JOIN tmp_play play             
            ON(base.version = play.version      AND base.`date` = play.`date`)
WHERE
        NOT   base.is_desktop
    AND NOT  input.is_desktop
    AND NOT   sumo.is_desktop
    AND NOT   adis.is_desktop
    AND NOT visits.is_desktop
HAVING -- Make sure that the row is necessary
    input_average
    OR input_average_7_days
    OR input_volume
    OR sumo_posts
    OR sumo_unanswered_3_days
    OR sumo_in_product_views
    OR adis
    OR play_average
    OR play_volume
    OR heartbeat_average
    OR heartbeat_volume
;