from __future__ import print_function
import sqlite3
import traceback
import os
import collections
import itertools
from itertools import imap
from itertools import chain


class S3Con(object):
    '''
    Copied from Nickel with slight changes.
    It has some debug printing facilities which should be in a common
    module anyway.
    todo : merge them together and put them in Zinc.Python (?)
    '''
    log = None

    @classmethod
    def log(cls, *args, **kwargs):
        if cls.log:
            cls.log(*args, **kwargs)

    def __init__(self, dbpath):
        self.dbpath = dbpath

    def __enter__(self):
        #self.log( 2, "Opening db " + self.dbpath )
        self.conn = sqlite3.connect(self.dbpath)
        self.conn.row_factory = sqlite3.Row
        #This will make sqlite3 return bytestrings. The bytestrings will
        #be encoded in UTF-8.
        #self.conn.text_factory = str
        self.cur = self.conn.cursor()
        return self

    def __exit__(self, _type, _value, _tb):
        to_rethrow = True
        self.conn.commit()
        self.cur.close()
        self.conn.close()
        if _type is None:
            #placeholder for some cleanup action
            return True 
        elif issubclass(_type, sqlite3.Error): 
            self.log(2,"sqlite3.Error")
            #Dont raise this
        elif issubclass(_type, Exception):
            self.log(2,"General Exception.")
        else:
            self.log(1,"Caught exception")
        self._formatEx(_type, _value, _tb)
        return not to_rethrow

    def _formatEx(self, _type= None, _val = None, _tb = None, 
            _tbl=5):
        '''
        todo: refactor the cobalt one to make that more generic
        and then use that from everywhere
        '''
        if _type:
            excName = _type.__name__
        traceback_frames = traceback.extract_tb(_tb, _tbl)
        fileName = traceback_frames[0][0]
        lineNo = traceback_frames[0][1]
        excTrace = ''
        for frame in traceback.format_list(traceback_frames):
            excTrace += frame
        fileName = os.path.basename(fileName)
        debugStr = '%s:%s ::%s: %s: \n%s'%(fileName, lineNo, excName, 
                str(_val), excTrace)
        self.log(4, "%s"%(str(debugStr)))

class LiteTable(object):
    '''
    All the strings are manipulated normal python way, as we are
    not expecting any sqlinjection attack on fakes.
    '''
    def __init__(self, dbName, tableName, cols, logging_fn):
        '''
        If cols is a dictionary, key is the column name and the value 
        is any metadata you may want push when you are creating a table.
        So cols is either {'colname1' : 'tablemetadata1', 'colname2':'tm2'}
        self.someTable = LiteTable(self.path_to_db_file, 'table_name',
                dict(bookingReference = 'integer primary key autoincrement',
                    title = 'text',
                    synopsis = 'text',
                    identifier = 'text',
                    bookingType = 'integer',
                    priority = 'integer',
                    ))
        '''
        self.log = logging_fn
        S3Con.log = logging_fn
        self.dbName = dbName
        self.tableName = tableName
        self.cols = cols
        #Or self.__dict__.update(map(lambda k:(k,k), self.cols))
        for col in cols:
            self.__dict__[col]= col

    def _create_insertstr2(self, **args):
        ''' itertools version. '''
        isAutoPrimary = (lambda (x,y):('primary' in y.lower())
                and ('autoincrement' in y.lower()))
        def transform((col, coltype)):
            istext = (True if ('text' in coltype.lower() 
                        or 'varchar' in coltype.lower())
                    else False)
            #get the val
            if col in args:
                val = args[col]
            elif istext:
                val = ""
            else:
                val = 0
            #stringify the val
            val = '"%s"'%(str(val)) if istext else str(val)
            return val
        #########################
        #dont need to insert the autoincrement fields
        i1 = itertools.ifilterfalse(isAutoPrimary, self.cols.iteritems())
        i2, i3 = itertools.tee(i1)
        colstr = ','.join((x for (x,y) in i2))
        valstr = ','.join(itertools.imap(transform, i3))
        q = 'insert or rollback into %s (%s) values (%s)'%(self.tableName,
                colstr, valstr)
        return q

    def _create_insertstr1(self, **args):
        ''' for loop version. '''
        valStr = ''
        colStr = ''
        lasti = len(self.cols) - 1
        #todo should we support varchar ??
        def istextt(col):
            return ('text' in self.cols[col].lower() or 
                    'text' in self.cols[col].lower())
        istext = (lambda col: ('text' in self.cols[col].lower()) or 
                ('varchar' in self.cols[col].lower()))
        isAutoPrimary = (lambda col: ('primary' in self.cols[col].lower())
                and ('autoincrement' in self.cols[col].lower()))
        i1 = itertools.ifilterfalse(isAutoPrimary, self.cols.iterkeys())
        for i, col in enumerate(self.cols):
            #get val
            if isAutoPrimary(col):
                continue
            if col in args:
                val = args[col]
            elif istext(col):
                val =""
            else:
                val = 0
            #strigify the val
            val = '"%s"'%(str(val)) if istext(col) else str(val)
            if i == lasti:
                valStr += '%s'%(val) 
                colStr += '%s'%(col)
            else:
                valStr += '%s,'%(val)
                colStr += '%s,'%(col)
        q = 'insert into %s (%s) values (%s)'%(self.tableName, colStr, 
                valStr)
        return q

    def insert(self, **args):
        '''
        insert(col1 = 'val1', col2 = val2})
        We will fill it with our own default values for unvalued cols.
        '''
        #list(dict_instance) works would make it work with list as well
        if not set(args.keys()) <= set(list(self.cols)):
            raise Exception("col in insert does not exist in the table")
        q = self._create_insertstr2(**args)
        self.log(2, q)
        rowid = None
        with S3Con(self.dbName) as db:
            db.cur.execute(q)
            rowid = db.cur.lastrowid
        return rowid


    def create(self, ifNotExists = True):
        '''
        As you may use an already created table, we dont 
        automatically call this for you so call this explicitly
        if you need to use this.
        Types should correspond to 
        '''
        q = ''
        lasti = len(self.cols) - 1
        # dict.iteritems => [(k1, v1), (k2, v2)]
        # mergeKV((k1,v1)) => 'k1 v1'
        # imap(mergeKV, d.iteritems()) => ['k1 v1', 'k2 v2']
        # ','.join(imap(mergeKV, d.iteritems())) => 'k1 v1, k2 v2'
        mergeKV = lambda kvtup:' '.join([str(kvtup[0]),str(kvtup[1])])
        q = ','.join(imap(mergeKV, self.cols.iteritems()))
        '''
        for i, col in enumerate(self.cols):
            if i == lasti:
                q += '%s %s'%(col, self.cols[col])
            else:
                q += '%s %s,'%(col, self.cols[col])
        '''
        ifNotExistsStr = ('if not exists' if ifNotExists else '')
        q = 'create table %s %s (%s)'%(ifNotExistsStr, self.tableName, q)
        self.log(2, q)
        with S3Con(self.dbName) as db:
            db.cur.execute(q)

    def select1(self, *args, **kargs):
        '''
        Returns single row for the condition.
        (val1, val2) = tbl.select1('col1', 'col2', col = val)
        todo : if required we can easily extend this to support multiple
        conditions 'or'-ed or 'and'-ed.
        Returns None if nothing found.
        '''
        if not args:
            raise Exception("There are no columns to be returned in select1")
        all = True if args[0] == '*' else False
        columns = args
        # At the moment we just support one condition
        if len(kargs) != 1:
            raise Exception("Wrong number of conditional clauses in select1")
        cond_col = kargs.keys()[0]
        if col not in self.cols:
            raise Exception("col(%s) in select1 does not exist in the table")
        if 'text' in self.cols[cond_col] or 'varchar' in self.cols[cond_col]:
            whereClause = '%s="%s"'%(cond_col, kargs[cond_col])
        else:
            whereClause = '%s=%s'%(cond_col, kargs[cond_col])
        rows = self.select(columns, whereClause)
        if not rows:
            return None
        #just the first row
        if all:
            vals = [rows[0][colname] for colname in self.cols.keys()]
        else:
            vals = [rows[0][colname] for colname in columns]
        return vals


    def select_raw(self, what_part, end_part=''):
        ''' 
        '''
        r = None
        q = 'select %s from %s %s'%(what_part, self.tableName, end_part)
        self.log(2, q)
        with S3Con(self.dbName) as db:
            db.cur.execute(q)
            r = db.cur.fetchall()
            self.log(2, str(r))
        return r

    def select(self, what, whereClause = None):
        ''' 
        select((table_instance.col1, table_instance.col2), "col3='stupid'")
        or select('*'). 
        
        In 'where clause' we use "col3=<value>" rather than
        "LitTableObject.col3=<value>".  LiteTableObject.col1 is only good
        because you don't need quotes, but as in  'where clause' we need quotes
        anyway, we have to type less without the instance name.  As return
        value select gives a list of sqlite3.Row object back, Row is nice and
        we dont reinvent wheels.  
        '''
        r = None
        if what != '*' and not set(what) <= set(list(self.cols)):
            raise Exception("cols(%s) in select does not exist in the table(%s)"%(
                str(what), str(self.cols)))
        if isinstance(what, collections.Iterable):
            what = ','.join(what)
            self.log(2, what)
        if whereClause:
            q = 'select %s from %s where %s'%(what, self.tableName, 
                    whereClause)
        else:
            q = 'select %s from %s'%(what, self.tableName)
        self.log(2, q)
        with S3Con(self.dbName) as db:
            db.cur.execute(q)
            r = db.cur.fetchall()
            self.log(2, str(r))
        return r

    def delete(self, whereClause):
        '''
        delete("col3='stupid'")
        '''
        q = 'delete from %s where %s'%(self.tableName, whereClause)
        with S3Con(self.dbName) as db:
            db.cur.execute(q)

    def update(self, uclause):
        '''
        update("col1=val1, col2=val2 where some_col=someval")
        '''
        q = 'update %s set %s'%(self.tableName, uclause)
        with S3Con(self.dbName) as db:
            db.cur.execute(q)

def create_record_table(db_full_path, log_fn):
    table = LiteTable(db_full_path, "WorkRecord",
            dict( id = 'integer primary key autoincrement',
                from_timestamp = 'integer unique',
                to_timestamp = 'integer unique',
                num_interruptions = 'integer',
                num_distractions = 'integer',
                work_type = 'text',
                day_type = 'text',
                task = 'text'
                ), log_fn)
    table.create()
    return table

def create_goal_table(db_full_path, log_fn):
    table = LiteTable(db_full_path, "Goals",
            dict( id = 'integer primary key autoincrement',
                start_timestamp = 'integer',
                end_timestamp = 'integer',
                num_hours = 'integer',
                work_type = 'text',
                name = 'text unique'
                ), log_fn)
    table.create()
    return table




def main():
    t1 = LiteTable("/tmp/db", 'Table1', 
            dict(id='integer primary key autoincrement', 
                title = 'text',
                value = 'integer')) 
    t1.create()
    r = t1.insert(title="Great Title", value=89)
    print(2, "rowid : %s"%(r))
    rows = t1.select((t1.id, t1.title), 'rowid==%s'%(r))
    assert rows[0]['id'] == r
    r = t1.insert(title="Bad Title", value=99999)
    print(2, "rowid : %s"%(r))
    t1.select('*')
    t1.select((t1.id, t1.title), 'value==89')
    t1.select( (t1.title,), 'value==89')
    t1.delete('value==89')
    t1.select((t1.title,), 'value==89')


if __name__ == "__main__":
    main()
