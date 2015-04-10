SELECT
    LEFT(DATE(question.created),10) AS `date`,
    metadata.version                AS version,
    question.is_desktop             AS is_desktop,
    SUM(answer.created IS NULL 
            OR TIMESTAMPDIFF(HOUR, question.created, answer.created) >= 72
        )                           AS num_unanswered_72,
    COUNT(*)                        AS num_posts
FROM
    (
        SELECT id, created, (product_id = 1) AS is_desktop
        FROM questions_question
        WHERE
            DATE(created) >= :start_date
            AND DATE(created) <= :end_date
            AND product_id IN(1,2)
    ) question
    LEFT JOIN (  
        SELECT
            question_id, 
            CAST(SUBSTRING_INDEX(
                    SUBSTRING_INDEX(value, 'Firefox/', -1), 
                    '.', 
                    1) AS UNSIGNED
                ) AS version 
        FROM questions_questionmetadata
        WHERE name = "useragent"
        GROUP BY 1,2
    ) metadata ON(question.id = metadata.question_id)
    LEFT JOIN (
        SELECT question_id, min(created) AS created 
        FROM questions_answer 
        GROUP BY 1
    ) answer ON(question.id = answer.question_id)
GROUP BY 1,2,3
;