(SELECT 'date' AS d, 'version' AS version, 'adis' AS adis)
UNION 
(SELECT
    bl_date::VARCHAR(10) AS d,
    (
            CASE 
                WHEN REGEXP_SUBSTR(v_prod_major,'^[0-9]*')='' THEN 0
                ELSE REGEXP_SUBSTR(v_prod_major,'^[0-9]*')::INTEGER
            END
        )::VARCHAR(6) AS version,
    SUM(tot_requests_on_date)::VARCHAR(12) AS adis
FROM adi_dimensional_by_date 
WHERE
    product = '%s'
    AND bl_date >= '%s'
    AND bl_date <= '%s'
GROUP BY 1,2
HAVING SUM(tot_requests_on_date) > 0
)
ORDER BY 1 DESC,3 DESC
;