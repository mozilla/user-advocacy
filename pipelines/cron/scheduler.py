#!/usr/local/bin/python
from crontab import CronTab
import os

_JOBLIST = [
        #[cron_time_fmt, command, UNIQUE tag that must not be changed]
        #['13 * * * *','echo "this is a new test: $CODE_PATH" >/tmp/test.txt', 'test']
        #[,,],
        [   '0 3 * * *', 
            'python $CODE_PATH/pipelines/google_play/google_play_manager.py >/tmp/google_play_cron 2>&1', 
            'Play Pipeline'],
        ['0 4 * * *', 
            'python $CODE_PATH/pipelines/stats_pipeline/pipeline.py >/tmp/stats_cron 2>&1', 
            'Stats Pipeline'],
        ['0 5 * * *', 
            'python $CODE_PATH/pipelines/hello_pipeline/pipeline.py >/tmp/hello_cron 2>&1 && sudo chmod -R 775 /var/server/server', 
            'Hello Pipeline'],
        ['0 */6 * * *',
            'python $CODE_PATH/pipelines/alert_pipelines/word_alert.py >/tmp/alert_cron 2>&1',
            'Alert Pipeline']
    ]


def main(user = 'root'):
    cron = CronTab(user=os.environ['USER'])

    for entry in _JOBLIST:
        time    = entry[0]
        #TODO(rrayborn): Should we parse out all envars instead of just CODE_PATH?
        command = entry[1] \
            .replace('$CODE_PATH', os.environ['CODE_PATH']) \
            .replace('python ', '~/.virtualenvs/uabackend/bin/python ')
        tag     = entry[2]
        
        # remove old jobs
        for job in cron.find_comment(tag):
            print 'Deleting job: "%s"' % str(job)
            cron.remove(job)
        
        # create new jobs
        job = cron.new(command=command)
        job.setall(time)
        job.set_comment(tag)

        # output
        if not job.is_valid():
            raise Exception('Job "%s" is not valid' % job)
        cron.write()


if __name__ == '__main__':
    main()