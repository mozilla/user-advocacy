#!/usr/local/bin/python
from crontab import CronTab
import os

_JOBLIST = [
        #[cron_time_fmt, command, tag]
        #['13 * * * *','echo "this is a new test: $CODE_PATH" >/tmp/test.txt', 'test']
        #[,,],
    ]


def main(user = 'root'):
    cron = CronTab(user=os.environ['USER'])

    for entry in _JOBLIST:
        time    = entry[0]
        command = entry[1].replace('$CODE_PATH', os.environ['CODE_PATH'])
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