CREATE TEMPORARY TABLE tmp_base AS 
SELECT
    dates.`date`                                AS `date`,
    ri.version                                  AS version,
    dates.is_desktop                            AS is_desktop,
    TIMESTAMPDIFF(DAY,'1970-1-01',dates.`date`) AS days_since_epoch,
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
    END                                         AS channel
FROM
    release_info ri
    JOIN (SELECT `date`, is_desktop FROM tmp_input GROUP BY 1,2) dates
GROUP BY 1,2,3,4,5
;