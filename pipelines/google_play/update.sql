
USE sentiment;

# create the table if not exists
CREATE TABLE IF NOT EXISTS google_play_reviews (
    created               BIGINT NOT NULL, 
    `date`                DATE, 
    version               INT, 
    language              TEXT, 
    model                 TEXT, 
    rating                INT, 
    title                 TEXT, 
    description           TEXT, 
    PRIMARY KEY (created)
);

# load data
LOAD DATA LOCAL INFILE '/home/shared/code/pipelines/google_play/data/google_play_latest.csv'
    REPLACE INTO TABLE google_play_reviews
    CHARACTER SET utf8
    FIELDS TERMINATED BY ','
    OPTIONALLY ENCLOSED BY '\"'
    LINES TERMINATED BY '\n'
    IGNORE 1 LINES
    (
        @package,        #Package Name
        @dummy,          #App Version [Not the same as our versioning!]
        language,        #Reviewer Language
        model,           #Reviewer Hardware Model
        @dummy,          #Review Submit Date and Time
        created,         #Review Submit Millis Since Epoch
        @dummy,          #Review Last Update Date and Time
        @updated_millis, #Review Last Update Millis Since Epoch
        rating,          #Star Rating
        title,           #Review Title
        description,     #Review Text
        @dummy,          #Developer Reply Date and Time
        @dummy,          #Developer Reply Millis Since Epoch
        @dummy,          #Developer Reply Text
        @dummy           #URL [undocumented]
    )
    SET `date` = DATE((FROM_UNIXTIME(@updated_millis/1000 + 7*3600,'%Y-%m-%d'))),
        version = (SELECT version
                FROM sentiment.release_info 
                WHERE 
                    (   # if the package isn't beta then it's release
                        @package NOT LIKE '%beta%' 
                        AND @updated_millis/1000 >= UNIX_TIMESTAMP(release_start_date) 
                        AND @updated_millis/1000 <= UNIX_TIMESTAMP(release_end_date)
                    ) OR (
                        @package LIKE '%beta%' 
                        AND @updated_millis/1000 >= UNIX_TIMESTAMP(beta_start_date) 
                        AND @updated_millis/1000 <= UNIX_TIMESTAMP(beta_end_date)
                    )
                GROUP BY 1)
;