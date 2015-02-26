#!/usr/local/bin/python

'''
Manages our crontabs.
'''
#TODO(rrayborn): figure out why it's adding whitespace to the crontab

__author__     = 'Rob Rayborn'
__copyright__  = 'Copyright 2014, The Mozilla Foundation'
__license__    = 'MPLv2'
__maintainer__ = 'Rob Rayborn'
__email__      = 'rrayborn@mozilla.com'
__status__     = 'Production'


from crontab import CronTab
import os

#TODO(rrayborn): this might need a csv or even a front end later
_JOBLIST = [
        #[cron_time_fmt, command, UNIQUE tag that must not be changed]
        #['13 * * * *','echo "this is a new test: $CODE_PATH" >/tmp/test.txt', 'test']
        #[,,],
        [   '0 3 * * *', 
            'python pipelines/google_play/google_play_manager.py >/tmp/google_play_cron 2>&1', 
            'Play Pipeline'],
        ['0 4 * * *', 
            'python pipelines/stats_pipeline/pipeline.py         >/tmp/stats_cron       2>&1', 
            'Stats Pipeline'],
        ['0 5 * * *', 
            'python pipelines/hello_pipeline/pipeline.py         >/tmp/hello_cron       2>&1',
            'Hello Pipeline'],
        ['10 * * * *', 
            'python pipelines/alert_pipeline/pull_input_alert.py >>/tmp/alert_pipe_cron       2>&1',
            'Fetch alerts'],
        ['0 */6 * * *',
            'python pipelines/alert_pipeline/word_alert.py       >/tmp/alert_cron       2>&1',
            'Alert Pipeline']
    ]

#TODO(rrayborn): this might need a csv or even a front end later
_IGNORELIST = [
            #tags
        ]


def update_cron(user = None):
    """
    Updates the user's crontab

    Args:
        user (string): The word that needs stemming (default = $USER)

    Examples:
        >>> update_cron("rrayborn")
    """
    if not user:
        if os.environ['USER']:
            user = os.environ['USER']
        else:
            raise Exception('$USER not populated or overridden.')
    if not os.environ['CODE_PATH']:
        raise Exception('$CODE_PATH not populated. \
                        You should use the uabackend virtualenv.')
    
    cron = CronTab(user=user)

    invalid_jobs = []

    # Create/Replace jobs
    for entry in _JOBLIST:
        time     = entry[0]
        command  = entry[1] \
            .replace('python ', '$CODE_PATH/pipelines/cron/python_backend_wrapper.sh ') \
            .replace('$CODE_PATH', os.environ['CODE_PATH'])
        tag      = entry[2]
        auto_tag = 'AUTOGENERATE: ' + tag
        
        # find existing jobs
        existing_jobs = cron.find_comment(auto_tag)
        is_empty = True
        
        # remove old jobs
        for job in existing_jobs:
            cron.remove(job)
            is_empty = False

        # print operation
        if is_empty:
            print 'Creating job with tag: "%s"' % str(tag)
        else:
            print 'Replacing job(s) with tag: "%s"' % str(tag)
        
        # create new jobs
        job = cron.new(command=command)
        job.setall(time)
        job.set_comment(auto_tag)

        # check validity
        if not job.is_valid(): #TODO(rrayborn): this never seems to be false.
            invalid_jobs.append(job)
    
    # Update ignored jobs
    for tag in _IGNORELIST:
        auto_tag = 'AUTOGENERATE: ' + tag
        for job in cron.find_comment(auto_tag):
            print 'Ignoring job: "%s"' % str(tag)
            job.enable(False)

    if invalid_jobs:
        raise Exception('The following jobs are invalid:\n%s' % \
                        '\n'.join(invalid_jobs))

    cron.write()


if __name__ == '__main__':
    update_cron()
