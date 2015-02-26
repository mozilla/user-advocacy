
CREATE TABLE IF NOT EXISTS daily_desktop_stats (
  id                       INT  NOT NULL AUTO_INCREMENT,
  `date`                   DATE NOT NULL,
  days_since_epoch         INT  NOT NULL,
  version                  INT  NOT NULL,
  channel                  ENUM('Release','Beta','Aurora','Nightly'),
  input_average            FLOAT,
  input_average_7_days     FLOAT,
  input_volume             INT,
  sumo_posts               INT,
  sumo_unanswered_3_days   INT,
  sumo_in_product_views    INT,
  adis                     INT,
  heartbeat_average        FLOAT,
  heartbeat_responses_rate FLOAT,
  heartbeat_volume         INT,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_stat` (`date`,`version`)
);

-- Get Input data
DROP TABLE IF EXISTS tmp_desktop_input_base;
CREATE TABLE tmp_desktop_input_base AS 
SELECT
    DATE(created) AS `date`,
    CAST(SUBSTRING_INDEX(version, '.', 1) AS UNSIGNED) AS version,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 0 AS d0,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 1 AS d1,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 2 AS d2,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 3 AS d3,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 4 AS d4,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 5 AS d5,
    TIMESTAMPDIFF(DAY,'1970-1-01',DATE(created)) - 6 AS d6,
    AVG(happy) AS input_average,
    COUNT(*) AS input_volume
FROM input.remote_feedback_response
WHERE
    product = 'Firefox'
    AND DATE(created) >= DATE_SUB(:start_date, INTERVAL 7 DAY)
    AND DATE(created) <= :end_date
GROUP BY
    1,2,3,4,5,6,7,8,9
HAVING version IN (SELECT version FROM release_info)
;

CREATE TEMPORARY TABLE tmp_desktop_heartbeat AS 
SELECT 
    DATE(FROM_UNIXTIME(updated_ts/1000)) AS `date`,
    CAST(SUBSTRING_INDEX(version, '.', 1) AS UNSIGNED) AS version,
    AVG(score) AS average,
    COUNT(score)/COUNT(*) AS responses_rate,
    COUNT(*) AS volume
FROM input.remote_heartbeat_answer
WHERE
    survey_id = 'heartbeat-by-user-first-impression'
    AND NOT is_test
    AND updated_ts >= 1000*UNIX_TIMESTAMP(:start_date)
    AND updated_ts <= 1000*UNIX_TIMESTAMP(:end_date)
GROUP BY 1,2
HAVING version IN (SELECT version FROM release_info)
;

-- Get 7 day info
CREATE TEMPORARY TABLE tmp_desktop_input AS 
SELECT
    t0.`date`,
    t0.version,
    t0.input_average,
    t0.input_volume,
    (
        COALESCE(t0.input_average*t0.input_volume,0) +
        COALESCE(t1.input_average*t1.input_volume,0) +
        COALESCE(t2.input_average*t2.input_volume,0) +
        COALESCE(t3.input_average*t3.input_volume,0) +
        COALESCE(t4.input_average*t4.input_volume,0) +
        COALESCE(t5.input_average*t5.input_volume,0) +
        COALESCE(t6.input_average*t6.input_volume,0)
    ) / COALESCE(
        (
            COALESCE(t0.input_volume,0) +
            COALESCE(t1.input_volume,0) +
            COALESCE(t2.input_volume,0) +
            COALESCE(t3.input_volume,0) +
            COALESCE(t4.input_volume,0) +
            COALESCE(t5.input_volume,0) +
            COALESCE(t6.input_volume,0)
        ),
        0
    ) AS input_average_7_days
FROM
    tmp_desktop_input_base t0
    LEFT JOIN tmp_desktop_input_base t1 ON(t0.d1 = t1.d0 AND t0.version = t1.version )
    LEFT JOIN tmp_desktop_input_base t2 ON(t0.d2 = t2.d0 AND t0.version = t2.version )
    LEFT JOIN tmp_desktop_input_base t3 ON(t0.d3 = t3.d0 AND t0.version = t3.version )
    LEFT JOIN tmp_desktop_input_base t4 ON(t0.d4 = t4.d0 AND t0.version = t4.version )
    LEFT JOIN tmp_desktop_input_base t5 ON(t0.d5 = t5.d0 AND t0.version = t5.version )
    LEFT JOIN tmp_desktop_input_base t6 ON(t0.d6 = t6.d0 AND t0.version = t6.version )
HAVING
    version IN (SELECT version FROM release_info)
    AND `date` >= :start_date
;
DROP TABLE IF EXISTS tmp_desktop_input_base;

-- Get SUMO data
CREATE TEMPORARY TABLE tmp_desktop_sumo AS 
SELECT
    DATE(question.created) AS `date`,
    metadata.version       AS version,
    SUM(answer.created IS NULL 
            OR TIMESTAMPDIFF(HOUR, question.created, answer.created) >= 72
        )                  AS num_unanswered_72,
    COUNT(*)               AS num_posts
FROM
    (
        SELECT id, created 
        FROM sumo.questions_question
        WHERE
            DATE(created) >= :start_date
            AND DATE(created) <= :end_date
            AND product_id = 1
    ) question
    LEFT JOIN (  
            SELECT
                question_id, 
                CAST(SUBSTRING_INDEX(
                        SUBSTRING_INDEX(value, 'Firefox/', -1), 
                        '.', 
                        1) AS UNSIGNED
                    ) AS version 
            FROM sumo.questions_questionmetadata
            WHERE
                name = "useragent"
            GROUP BY 1,2
            HAVING version IN (SELECT version FROM release_info)
        ) metadata ON(question.id = metadata.question_id)
    LEFT JOIN (
            SELECT question_id, min(created) AS created 
            FROM sumo.questions_answer 
            GROUP BY 1
        ) answer ON(question.id = answer.question_id)
GROUP BY 1,2
ORDER BY 1,2
;

-- Get Date/Version basis of stats table, right now it's just based on input
CREATE TEMPORARY TABLE tmp_desktop_base AS 
SELECT
    dates.`date`  AS `date`,
    TIMESTAMPDIFF(DAY,'1970-1-01',dates.`date`) AS days_since_epoch,
    ri.version    AS version,
    CASE 
        WHEN dates.`date` >= ri.release_start_date 
                AND dates.`date` <= ri.release_end_date THEN "Release"
        WHEN dates.`date` >= ri.beta_start_date    
                AND dates.`date` <= ri.beta_end_date    THEN "Beta"
        WHEN dates.`date` >= ri.aurora_start_date  
                AND dates.`date` <= ri.aurora_end_date  THEN "Aurora"
        WHEN dates.`date` >= ri.nightly_start_date 
                AND dates.`date` <= ri.nightly_end_date THEN "Nightly"
        ELSE NULL
    END AS channel
FROM
    release_info ri
    JOIN (SELECT `date` FROM tmp_desktop_input input GROUP BY 1) dates
GROUP BY 1,2,3
;


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
        heartbeat_responses_rate,
        heartbeat_volume
    )
SELECT
    base.`date`                                 AS `date`,
    base.days_since_epoch                       AS days_since_epoch,
    base.version                                AS version,
    base.channel                                AS channel,
    COALESCE(input.input_average,0)             AS input_average,
    COALESCE(input.input_average_7_days,0)      AS input_average_7_days,
    COALESCE(input.input_volume,0)              AS input_volume,
    COALESCE(sumo.num_posts,0)                  AS sumo_posts,
    COALESCE(sumo.num_unanswered_72,0)          AS sumo_unanswered_3_days,
    COALESCE(visits.visits,0)                   AS sumo_in_product_views,
    COALESCE(adis.num_adis,0)                   AS adis,
    COALESCE(heartbeat.average,0)               AS heartbeat_average,
    COALESCE(heartbeat.responses_rate,0)        AS heartbeat_responses_rate,
    COALESCE(heartbeat.volume,0)                AS heartbeat_volume
FROM
    tmp_desktop_base base
    LEFT JOIN tmp_desktop_input input           
            ON(base.version = input.version     AND base.`date` = input.`date`)
    LEFT JOIN tmp_desktop_sumo sumo             
            ON(base.version = sumo.version      AND base.`date` = sumo.`date`)
    LEFT JOIN tmp_desktop_adis adis             
            ON(base.version = adis.version      AND base.`date` = adis.`date`)
    LEFT JOIN tmp_desktop_sumo_visits visits 
            ON(base.version = visits.version AND base.`date` = visits.`date`)
    LEFT JOIN tmp_desktop_heartbeat heartbeat 
            ON(base.version = heartbeat.version AND base.`date` = heartbeat.`date`)
HAVING -- Make sure that the row is necessary
    input_average
    OR input_average_7_days
    OR input_volume
    OR sumo_posts
    OR sumo_unanswered_3_days
    OR sumo_in_product_views
    OR adis
    OR heartbeat_average
    OR heartbeat_responses_rate
    OR heartbeat_volume
;