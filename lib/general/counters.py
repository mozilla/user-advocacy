#!/usr/local/bin/python
from collections import defaultdict
from warnings import warn

class ItemCounterDelta(object):
    """
    This stores a base and after ItemCounter and provides ways of accessing the
    differences between them.
    
    To insert into base or after Counters, use self.base.insert() or self.after.insert()
    methods.
    
    For computations, after (or before if you know it) you have inserted the values,
    use set_potential() and set_thresholds() to set the potential userbase and thresholds
    for significance.
    """
    
    def __init__(self, key=None, diff_pct=0, diff_abs=0):
        """
        key is the unique ID for this item (such as a stemmed or limitized word or an
        add-on ID.)
    
        diff_pct and diff_abs are the percentage increase and absolute increase 
        (in per 1000) that would both need to be reached to trigger item.is_significant 
        to return true
        """
    
        self.key                = key
        self.base               = ItemCounter(key)
        self.after              = ItemCounter(key)
        self.base_potential     = -1 # potential number (negative to allow dividing)
        self.after_potential    = -1 # potential number (negative to allow dividing)
        self.diff_pct_threshold = diff_pct 
        self.diff_abs_threshold = diff_abs
        

    
    def set_potentials(self, base = None, after = None):
        """
        Set the total number of processed entries for before and after (needed for
        calculations)
        """
        if not base is None:
            self.base_potential = base
        if not after is None:
            self.after_potential = after

    def set_thresholds(self, diff_pct = None, diff_abs = None):
        """
        Set the total number of processed entries for before and after (needed for
        calculations)
        """
        if not diff_pct is None:
            self.diff_pct_threshold = diff_pct
        if not diff_abs is None:
            self.diff_abs_threshold = diff_abs

    @property
    def base_pct (self):
        return self.base.count / float(self.base_potential) * 100
    
    @property
    def after_pct (self):
        return self.after.count / float(self.after_potential) * 100

    @property
    def diff_pct (self):
        return self.after_pct / self.base_pct * 100 - 100
    
    @property
    def diff_abs
        return self.after_pct - self.base_pct

    @property
    def is_significant(self):
        if (self.diff_abs >= self.diff_abs_threshold and \
            self.diff_pct >= self.diff_pct_threshold):
            return True
        return False

    @property
    def total_count(self):
        return self.base.count + self.after.count

    def __str__(self):
        return 'ItemCounterDelta object with key %s and %d items' % (
                self.key,
                self.total_count,
            )



class ItemCounter(object):
    """
    This is a smart counter object. You insert() stuff into this counter and it tracks
    the following: 
    * links (a deduped set of items that are relevant to this counter)
    * metadata (a dict of subtypes of data -- such as version numbers or real versions
        of stemmed words -- with counts to find the most frequently referenced version
        or most frequently referenced word)
    """
    
    def __init__(self, key = None):
        self.key             = key
        self.count           = 0
        self.metadata        = defaultdict(int) # stuff like versions, real words etc.
        self.link_list       = set() # can be comment IDs, or URLs of other things

    def insert(self, link = None, meta = None, key = None):
        
        if (not key is None):
            if self.key is None:
                self.key = key
            elif self.key != key:
                warn("Redefining key in ItemCounter from " + self.key + " to " + key)
                self.key = key
            
        if isinstance(meta, dict):
            for (k,v) in meta.iteritems():
                self.metadata[k] += v
        elif isinstance(meta, (set, list)):
            for i in meta:
                self.metadata[i] += 1
        else:
            self.metadata[meta] += 1
            
        if isinstance(link, (set, list)):
            for i in link:
                self.link_list.add(i)
        else:
            self.link_list.add(link)

        self.count += 1

    def __str__(self):
        return 'Item with key %s, count %d' % (
                self.key,
                self.count
            )

    @property
    def sorted_metadata(self):
        return sorted(self.metadata, key=self.metadata.__getitem__, reverse=True)
