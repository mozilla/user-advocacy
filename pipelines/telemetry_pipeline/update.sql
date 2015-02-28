REPLACE INTO weekly_telemetry_stats (
        version,
        week,
        os,
        channel,
        measure_id,
        measure_name,
        measure_value,
        measure_average,
        measure_nonzero_average,
        users,
        active_users,
        potential_users
    )
SELECT
    :version                      AS version,
    :week                         AS week,
    tmp.os                        AS os,
    :channel                      AS channel,
    measures.id                   AS measure_id,
    tmp.measure                   AS measure_name,
    tmp.measure_value             AS measure_value,
    if(tmp.measure_average = '',         Null, tmp.measure_average)         AS measure_average,
    if(tmp.measure_nonzero_average = '', Null, tmp.measure_nonzero_average) AS measure_nonzero_average,
    tmp.users                     AS users,
    tmp.active_users              AS active_users,
    tmp.potential_users           AS potential_users
FROM
    tmp_weekly_stats        tmp
    LEFT JOIN telemetry_measures measures ON(tmp.measure = measures.name)
;