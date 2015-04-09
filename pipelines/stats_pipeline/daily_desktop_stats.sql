REPLACE INTO daily_desktop_stats (
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
        heartbeat_average,
        heartbeat_surveyed_users,
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
    COALESCE(input.heartbeat_average,0)         AS heartbeat_average,
    COALESCE(input.heartbeat_surveyed_users,0)  AS heartbeat_surveyed_users,
    COALESCE(input.heartbeat_volume,0)          AS heartbeat_volume
FROM
    tmp_base base
    LEFT JOIN tmp_input input           
            ON(base.version = input.version  AND base.`date` = input.`date`)
    LEFT JOIN tmp_sumo sumo             
            ON(base.version = sumo.version   AND base.`date` = sumo.`date`)
    LEFT JOIN tmp_adis adis             
            ON(base.version = adis.version   AND base.`date` = adis.`date`)
    LEFT JOIN tmp_sumo_visits visits 
            ON(base.version = visits.version AND base.`date` = visits.`date`)
WHERE
        (  base.is_desktop IS Null OR   base.is_desktop)
    AND ( input.is_desktop IS Null OR  input.is_desktop)
    AND (  sumo.is_desktop IS Null OR   sumo.is_desktop)
    AND (  adis.is_desktop IS Null OR   adis.is_desktop)
    AND (visits.is_desktop IS Null OR visits.is_desktop)
HAVING -- Make sure that the row is necessary
       input_average
    OR input_average_7_days
    OR input_volume
    OR sumo_posts
    OR sumo_unanswered_3_days
    OR sumo_in_product_views
    OR adis
    OR heartbeat_average
    OR heartbeat_surveyed_users
    OR heartbeat_volume
;
