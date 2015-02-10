
-- Usage:  
-- REPLACE @csv manually; 
-- REPLACE @week manually; 
-- REPLACE @channel manually; 

use telemetry;

#week,feature,os,valuename,measure_average,value,total

CREATE TEMPORARY TABLE tmp_weekly_stats (
  os                       ENUM('Windows','Mac','Linux'),
  measure                  VARCHAR(200),
  measure_value            VARCHAR(200),
  users                    INT,
  measure_average          FLOAT,
  measure_nonzero_average  FLOAT,
  active_users             FLOAT,
  potential_users          INT         
);

# load data
LOAD DATA LOCAL INFILE '@csv'
    INTO TABLE tmp_weekly_stats
    CHARACTER SET utf8
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '\"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (measure, os, @measure_average, @measure_nonzero_average, active_users, potential_users, measure_value, users)
    SET measure_average = if(@measure_average='',Null,@measure_average),
        measure_nonzero_average = if(@measure_nonzero_average='',Null,@measure_nonzero_average)
;

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
    @version                      AS version,
    '@week'                       AS week,
    tmp.os                        AS os,
    '@channel'                    AS channel,
    measures.id                   AS measure_id,
    tmp.measure                   AS measure_name,
    tmp.measure_value             AS measure_value,
    tmp.measure_average           AS measure_average,
    tmp.measure_nonzero_average   AS measure_nonzero_average,
    tmp.users                     AS users,
    tmp.active_users              AS active_users,
    tmp.potential_users           AS potential_users
FROM
    tmp_weekly_stats        tmp
    LEFT JOIN telemetry_measures measures ON(tmp.measure = measures.name)
;