
import datetime
import json
import operator
import os
import sys
from collections import Counter
from pprint import pprint
from subprocess import check_output



_total_states    = 0
_total_terminals = 0

_LOG_FILE_RAW    = 'loop-app-json'
_LOG_FILE_PARSED = 'loop-rooms-summary-sorted'


def main():
    tree = parse_csv(limit = 2500)
    pprint({
            'created_room_no_use':    tree.get_created_room_no_use_stats(),
            'created_room_leave':     tree.get_created_room_leave_stats(),
            'standalone_enter_leave': tree.get_standalone_enter_leave_stats(),
            'success':                tree.get_success_stats()
        })
    #tree.print_stats(1)
    print 'Tokens: ' + str(_total_terminals)
    stats, term_stats = tree.get_level_stats(1)
    stats['_non_get_start']       = (tree.get_non_get_start_pct())
    stats['_get_is_terminal'] = (tree.get_get_is_terminal_pct())

    total = 0
    for v in stats.values():
        total += v
    print 'Total: ' + str(total)
    pprint(stats)
    pprint(term_stats)

    total = 0
    stats, term_stats = tree.get_level_stats(2)
    for v in stats.values():
        total += v
    print 'Total: ' + str(total)
    pprint(stats)
    pprint(term_stats)


#    tree.print_tree()



def parse_file(filein = _LOG_FILE_RAW, fileout = _LOG_FILE_PARSED):
    '''Converts the raw log to a more usable form'''
    cmd =  ("grep '/rooms.*request\.summary' <%s | " % filein + # Grep for request.summary table and that we're looking at rooms
            "grep 'token' | " + # Grep for the existance of a token
            "sed -e 's|{\(.*\)\(\"Timestamp\":[^,]*,\)\(.*\)|{\2\1\3|' | " + # Re-order to have a timestamp first
            "sed -e 's|{\(.*\)\(\"token\":[^,]*,\)\(.*\)|{\2\1\3|' | " + # Re-order to have a token first
            "sort >%s" % fileout) # sort (thereby sorting by token then timestamp)
    check_output(cmd, shell=True)

    

def parse_csv(filename = _LOG_FILE_PARSED, limit = 1000000, ignore_errors = True):
    '''
    Parses the log file into a log tree.

    Params:
      filename      - the path/name of the log file (must be already parsed) (Default: "loop-rooms-summary-sorted")
      limit         - the maximum number of rooms to parse (Default: 1000000)
      ignore_errors - whether we throw out things with HTTP errors (Default: True)

    Returns:
      root - the Root of our LogState tree
    '''
    token_rows    = []
    current_token = None

    # Create root node
    root     = LogState('root', 'root', 'root', 0, None, False)

    i = 0
    is_error = False
    with open(filename, 'r') as f:
        for raw_row in f:
            if raw_row:
                row = json.loads(raw_row)
                if 'token' not in row.keys():
                    raise Exception('Row missing token: %s', raw_row)
                new_token = row['token'] 
                new_error = not ('Fields' in row.keys() \
                        and 'code' in row['Fields'].keys() \
                        and row['Fields']['code'] >= 200 \
                        and row['Fields']['code'] <  300
                        ) # TODO(rrayborn):   Should this be an option?
                if new_token == current_token:
                    if new_error:
                        is_error = new_error
                    if (not ignore_errors) or (not is_error):
                        token_rows.append(row)
                        i += 1
                else:
                    if current_token is not None and not is_error: # Not first loop and not error
                        root.parse_rows(current_token, token_rows) # Add to data structure
                    # Reset token data
                    token_rows    = [row]
                    current_token = new_token
                    is_error      = new_error
            if i > limit:
                break
    root.finalize()
    return root


class LogState(object):
    """
    """
    
    def __init__(self, method, code, action, num_participants, parent, is_standalone, key = None):
        num_participants = num_participants if num_participants else 0

        self.method            = method
        self.code              = code
        self.action            = action
        self.num_participants  = num_participants
        self.parent            = parent
        self.is_standalone     = is_standalone
        self.resolved_action   = action if action is not None and action !='' else method

        self.is_error    = code <200 or code >= 300

        self.is_complete = None not in [method, code, action, num_participants, parent]

        if key:
            self.key = key
        else:
            self.key = LogState.compute_key(method, action, code, num_participants)

        self.tokens = []

        self.children          = {} # key -> child
        self.num_substates     = 0 #TODO(rrayborn): this is only direct substates right now!

        self.num_terminals       = 0
        self.num_local_terminals = 0

        self.logs              = {} # key -> Log

    def get_key(self):
        return self.key

    def get_children(self, ret = {}):
        ret[self.key] = self
        for child in self.children.values():
            child.get_children(ret)

    def finalize(self):
        self.pct_terminals       = (100.0*self.num_terminals)/_total_terminals
        self.pct_substates       = (100.0*self.num_substates)/_total_states
        self.pct_local_terminals = (100.0*self.num_local_terminals)/_total_terminals
        for child in self.children.values():
            child.finalize()

    def print_tree(self, depth=0):
        print (depth * '  ') + ' '.join([self.key,str(self.pct_local_terminals), str(self.pct_terminals)])
        if self.children:
            values = self.children.values()
            values.sort(key=operator.attrgetter('num_terminals'), reverse=True)
            for child in values:
                child.print_tree(depth + 1)

    def parse_rows(self, token, rows, log = None):
        if log:
            self.logs[log.get_key()] = log
            prev_timestamp = log.get_timestamp()
        else:
            prev_timestamp = None

        self.num_terminals += 1
        

        if rows: # not terminal
            row = rows.pop(0)
            
            field_dict = row['Fields'] if 'Fields' in row.keys() else None

            # Coalesce values from the rows
            uuid             = row['Uuic']                     if 'Uuic'      in row.keys()                            else None
            timestamp        = row['Timestamp']                if 'Timestamp' in row.keys()                            else None
            method           = field_dict['method']            if field_dict and ('method'       in field_dict.keys()) else None
            code             = field_dict['code']              if field_dict and ('code'         in field_dict.keys()) else None
            action           = field_dict['action']            if field_dict and ('action'       in field_dict.keys()) else None
            num_participants = int(field_dict['participants']) if field_dict and ('participants' in field_dict.keys()) else None
            uid              = field_dict['uid']               if field_dict and ('uid'          in field_dict.keys()) else None


            # compute key
            key = LogState.compute_key(method, action, code, num_participants)

            # create sub-state if not exists
            if key not in self.children.keys():
                child = LogState(method, code, action,
                                               num_participants, self, uid is None, key)
                global _total_states
                self.children[key]    = child
                self.num_substates   += 1
                _total_states        += 1
            # set next child values
            new_log   = Log(token, uuid, uid, timestamp, prev_timestamp)
            self.children[key].parse_rows(token, rows, new_log)
        else:
            global _total_terminals
            _total_terminals         += 1
            self.num_local_terminals += 1

    def print_stats(self, depth_limit = 1, depth = 0):
        if depth > depth_limit:
            return
        
        cnt = 0
        print depth * '\t' + '\t'.join([
                str(self.method),
                str(self.action),
                str(self.is_error),
                str((100.0 * self.num_terminals)/_total_terminals)
                ])
        for child in self.children.values():
            child.print_stats(depth_limit = depth_limit, depth = depth+1)


    def get_non_get_start_pct(self):
        cnt = 0
        for child in self.children.values():
            if child.method != 'get':
                cnt += child.num_terminals

        return (100.0 * cnt) / _total_terminals

    def get_get_is_terminal_pct(self):
        cnt = 0
        for child in self.children.values():
            if child.method == 'get' and not child.children:
                cnt += child.num_terminals

        return (100.0 * cnt) / _total_terminals

#    def verify_tokens(self):
#        cnt = self.num_local_terminals
#        for child in self.children.values():
#            cnt += child.verify_tokens()
#                    
#        return cnt

    def get_nth_join_nodes(self, joins = 1):
        '''Returns all the nodes from the current node that are "joins" joins deep'''
        nodes = []
        if joins == 1:
            for child in self.children.values():
                if child.method == 'get' and child.children:
                    nodes.append(child)
        else:
            for child in self.children.values():
                if child.method == 'get' and child.children:
                    child._get_nth_join_nodes(joins - 1, nodes)
                    
        return nodes

    def _get_nth_join_nodes(self, joins, nodes):

        if (self.method != 'delete'):
            if self.action == 'join' and joins == 1:
                nodes += self.children.values()
            else:
                if self.action == 'join':
                    joins -= 1
                for child in self.children.values():
                    child._get_nth_join_nodes(joins, nodes)


    def get_level_stats(self, joins = 1):
        '''Returns all the states that Cheng and I could think of that start with a get'''
        stats = Counter({'deletes_before_join':0,'terminates_before_join':0,
                         'terminates_at_join':0,'success_at_join':0})
        termination_stats = Counter()
        for node in self.get_nth_join_nodes(joins):
            node._get_level_stats(stats, termination_stats)
        
        ret = {}
        for k in stats.keys():
            ret[k] = (100.0 * stats[k]) / _total_terminals 
        return ret, dict(termination_stats)


    def _get_level_stats(self, stats, termination_stats):
        if self.method == 'delete': # deletes # or  self.action == 'leave'):
            stats['deletes_before_join'] += self.num_terminals
            return
        
        if self.action == 'join':
            stats['terminates_at_join'] += self.num_local_terminals
        else: # self.action != 'join':
            stats['terminates_before_join'] += self.num_local_terminals
            termination_stats[self.resolved_action] += self.num_local_terminals
        
        if self.action == 'join':
            stats['success_at_join'] += self.num_terminals - self.num_local_terminals
        
        else: # self.action != 'join'
            for child in self.children.values():
                child._get_level_stats(stats, termination_stats)

    #====== ADAMS SUGGESTED FUNCTIONS =======================

    def get_stats_instructions(self, instructions):
        '''
        Plug in a set of instructions and get the stats %.

        Instructions = [[resolved_action, code, num_participants]]
        None's match anything

        '''
        cnt = 0
        for child in self.children.values():
            cnt += child._get_stats_instructions(list(instructions))
        return (100.0 * cnt) / _total_terminals

    def _get_stats_instructions(self, instructions):
        cnt = 0
        if not instructions:
            return self.num_terminals
        instruction = instructions[0]
        if  (instruction[0] and    self.is_standalone != instruction[0]) or \
            (instruction[1] and  self.resolved_action != instruction[1]) or \
            (instruction[2] and             self.code != instruction[2]) or \
            (instruction[3] and self.num_participants != instruction[3]):
            return 0
        if instruction is None:
            for child in self.children.values():
                cnt += child._get_stats_instructions(list(instructions))
        instruction = instructions.pop(0)
        for child in self.children.values():
            cnt += child._get_stats_instructions(list(instructions))

        return cnt


    #User creates a room doesn't use it.
    #
    #   Desktop: 200 OK get /rooms/00al4fVp4PQ participants: 0
    #   Desktop: 200 OK join /rooms/00al4fVp4PQ participants: 0
    #   Desktop: 204 OK leave /rooms/00al4fVp4PQ
    def get_created_room_no_use_stats(self):
        instructions = [
                [False, 'get',   200, 0],
                [False, 'join',  200, 0],
                [False, 'leave', 204, None]
            ]
        return self.get_stats_instructions(instructions) 

    #User enters his own room and leaves. No one else joins
    #
    #   Desktop: 200 OK join /rooms/00Dn9nuxcL4 participants: 0
    #   Desktop: 204 OK leave /rooms/00Dn9nuxcL4
    def get_created_room_leave_stats(self):
        instructions = [
                [False, 'get',   200, 0],
                [False, 'leave', 204, None]
            ]
        return self.get_stats_instructions(instructions)

    #Standalone client enters someone's room and leaves. The owner does not join.
    #
    #Standalone: 200 OK join /rooms/08sGp9ugDS8 participants: 0
    #Standalone: 200 OK get /rooms/08sGp9ugDS8 participants: 1
    #Standalone: 204 OK leave /rooms/08sGp9ugDS8
    def get_standalone_enter_leave_stats(self):
        instructions = [
                [True, 'join',  200, 0],
                [True, 'get',   200, 1],
                [True, 'leave', 204, None]
            ]
        return self.get_stats_instructions(instructions) 

    #Both the room owner and the standalone client enter a room.
    #At the same time: Success!
    #At different times: missed connection.
    #
    #   Desktop: 200 OK join /rooms/042FxMYqLaI participants: 0
    #Standalone: 200 OK join /rooms/042FxMYqLaI participants: 1
    #Standalone: 200 OK get /rooms/042FxMYqLaI participants: 2
    #   Desktop: 204 OK leave /rooms/042FxMYqLaI
    #Standalone: 204 OK leave /rooms/042FxMYqLaI
    def get_success_stats(self):
        instructions = [
                [False, 'join',  200, 0],
                [True,  'join',  200, 1],
                [True,  'get',   200, 2],
                [False, 'leave', 204, None],
                [True,  'leave', 204, None]
            ]
        return self.get_stats_instructions(instructions) 



#====== END ADAMS SUGGESTED FUNCTIONS ===================

#    def get_bad_joins(self, acceptable_delay_sec = 1):
#        acceptable_delay_nano = acceptable_delay_sec * 1000000000
#        stats = self._get_bad_joins(acceptable_delay_nano)
#        #tokens.sort(key=lambda x: x[1], reverse=True)
#
#        return stats
#
#    def _get_bad_joins(self, acceptable_delay_nano, prev_logs = {}, 
#                       token_stats = {'slow_joins':     [],
#                                      'non_joins':      [],
#                                      'num_good_joins': 0, 
#                                      'num_slow_joins': 0, 
#                                      'num_non_joins':  0, 
#                                      'num_joins':      0}):
#        prev_logs = prev_logs.copy()
#        logs = self.logs
#        if prev_logs:
#            if self.method == 'get' and not self.is_error:
#                prev_logs_keys = set(prev_logs.keys())
#                logs_keys      = set(logs.keys())
#                intersection = prev_logs_keys & logs_keys
#                for log_key in intersection:
#                    timediff = logs[log_key].get_timestamp() - \
#                            prev_logs[log_key].get_timestamp()
#                    if timediff > acceptable_delay_nano:
#                        token_stats['slow_joins'].append([logs[log_key].get_token(), timediff])
#                        token_stats['num_slow_joins'] += 1
#                    else:
#                        token_stats['num_good_joins'] += 1
#                    del prev_logs[log_key]
#
#        if self.action == 'join' and not self.is_error:
#            prev_logs.update(logs)
#            token_stats['num_joins'] += len(logs)
#        if self.children:
#            for child in self.children.values():
#                child._get_bad_joins(acceptable_delay_nano, prev_logs, token_stats)
#        else:
#            for log in prev_logs.values():
#                #token_stats['non_joins'].append(log.get_token())
#                token_stats['num_non_joins'] += 1



    @staticmethod
    def compute_key(method, action, code, num_participants):
        return '-'.join([
                str(method)           if method           else '',
                str(action)           if action           else '',
                str(code)             if code             else '',
                str(num_participants) if num_participants else '0'
            ])
  




    
class Log(object):
    """
    
    """
    
    def __init__(self, token, uuid, uid, timestamp, prev_timestamp = None, key=None):
        self.token     = token
        self.uuid      = uuid
        self.uid       = uid
        self.timestamp = timestamp
        if timestamp and prev_timestamp and timestamp == prev_timestamp:
            print 'SHIT!!!'
            print [timestamp, prev_timestamp]
        self.timediff  = timestamp - prev_timestamp if prev_timestamp else 0
        if key is None:
            self.key   = Log.compute_key(token,uid)

        self.is_complete = None not in [token, uuid, uid, timestamp, prev_timestamp]

    def get_key(self):
        return self.key

    def get_token(self):
        return self.token

    def get_timestamp(self):
        return self.timestamp

    def print_related_logs(self):
        cmd = 'grep \'"Token":"%s"' % self.token
        print check_output(cmd, shell=True)

    @staticmethod
    def compute_key(token, uid):
        return '-'.join([
                str(token) if token else '',
                str(uid)   if uid   else '',
            ])


if __name__ == '__main__':
    main()