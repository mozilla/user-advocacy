(SELECT 'date' AS d, 'version' AS version, 'is_desktop' AS is_desktop, 'adis' AS adis)
UNION 
(SELECT
    bl_date::VARCHAR(10)                   AS d,
    (
            CASE 
                WHEN REGEXP_SUBSTR(v_prod_major,'^[0-9]*')='' THEN 0
                ELSE REGEXP_SUBSTR(v_prod_major,'^[0-9]*')::INTEGER
            END
        )::VARCHAR(6)                      AS version,
    (
            CASE 
                WHEN product = 'Firefox' THEN '1'
                ELSE '0'
            END
        )::VARCHAR(10)                     AS is_desktop,
    SUM(tot_requests_on_date)::VARCHAR(12) AS adis
FROM adi_dimensional_by_date 
WHERE
    product IN('Firefox', 'Fennec')
    AND bl_date >= '%s'
    AND bl_date <= '%s'
GROUP BY 1,2,3
HAVING SUM(tot_requests_on_date) > 0
)
ORDER BY 1 DESC,4 DESC
;