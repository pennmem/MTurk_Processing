import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import relationship


Base = declarative_base()

# class BonusTracker(Base):
#     __tablename__ = "bonus_tracker"
#     uniqueid = sql.Column(sql.String(128), primary_key=True, nullable=False)
#     assignmentid = sql.Column(sql.String(128), nullable=False)
#     workerid = sql.Column(sql.String(128), sql.ForeignKey("master_list.workerid"), nullable=False)
#     bonus = sql.Column(sql.Float, default=0)
#     date_to_send = sql.Column(sql.Date)
#     date_sent = sql.Column(sql.Date)
#     sent = sql.Column(sql.Boolean, default=False)
#     requestid = sql.Column(sql.Integer)

class SubjectTracker(Base):
    __abstract__ = True
    assignmentid = sql.Column(sql.String(128), nullable=False)
    workerid = sql.Column(sql.String(128), nullable=False)
    hitid = sql.Column(sql.String(128), nullable=False)
    ipaddress = sql.Column(sql.String(128), nullable=False)
    browser = sql.Column(sql.String(128), nullable=False)
    platform = sql.Column(sql.String(128), nullable=False)
    language = sql.Column(sql.String(128), nullable=False)
    cond = sql.Column(sql.Integer, nullable=False)
    counterbalance = sql.Column(sql.Integer, nullable=False)
    codeversion = sql.Column(sql.String(128))
    beginhit = sql.Column(sql.Date)
    beginexp = sql.Column(sql.Date)
    endhit = sql.Column(sql.Date)
    bonus = sql.Column(sql.Float)
    status = sql.Column(sql.Integer)
    mode = sql.Column(sql.String(128))
    datastring = sql.Column(sql.Text(4294967295))

    @declared_attr
    def uniqueid(cls):
        return sql.Column(sql.String(128), sql.ForeignKey("acceptance.uniqueid"), primary_key=True, nullable=False)

    @declared_attr
    def parent(cls):
        return relationship("AcceptanceTracker")

    def as_dict(self):
        return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

class ErrorTracker(SubjectTracker):
    __tablename__ = "error_HIT"

class CodeMapping(Base):
    __tablename__ = "master_list"
    anonymousid = sql.Column(sql.Integer, default=-1, autoincrement=True, primary_key=True) 
    workerid = sql.Column(sql.String(128), nullable=False, unique=True)

class AcceptanceTracker(Base):
    __tablename__ = "acceptance"
    uniqueid = sql.Column(sql.String(128), primary_key=True, nullable=False)
    assignmentid = sql.Column(sql.String(128), nullable=False)
    workerid = sql.Column(sql.String(128), nullable=False)
    hitid = sql.Column(sql.String(128), nullable=False)
    accepted = sql.Column(sql.Boolean, nullable=False, default=False)
    paid = sql.Column(sql.Boolean, nullable=False, default=False)
    excluded = sql.Column(sql.Boolean, nullable=False, default=False)
    experiment = sql.Column(sql.String(128))

def get_class_by_tablename(tablename):
    """Return class reference mapped to table.

    :param tablename: String with name of table.
    :return: Class reference or None.
    """
    for c in Base._decl_class_registry.values():
        if hasattr(c, '__tablename__') and c.__tablename__ == tablename:
            return c

    return type(tablename, (SubjectTracker,), {'__tablename__': tablename})


class DBManager(object):

    '''
    NOT_ACCEPTED = 0
    ALLOCATED = 1
    STARTED = 2
    COMPLETED = 3
    SUBMITTED = 4
    CREDITED = 5
    QUITEARLY = 6
    BONUSED = 7
    '''

    def __init__(self, db_url, verbose_sql=False):
        self.engine = sql.create_engine(db_url)
        self.Session = sql.orm.sessionmaker(bind=self.engine)
        self.verbose_sql = verbose_sql
        Base.metadata.create_all(self.engine)

    def __enter__(self):
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, value, trace):
        self.session.close()
        self.session = None


    def get_complete_subjects(self, experiment, class_exp=False):
        if class_exp:
            complete_statuses=[2, 3, 4, 5, 7]
            modes = ["prolific", "live", "debug"]
        else:
            complete_statuses=[3, 4, 5, 7]
            modes = ["prolific", "live"]
        TableClass = get_class_by_tablename(experiment)
        rows = self.session.query(TableClass).filter(sql.and_(TableClass.status.in_(complete_statuses),\
                                                         TableClass.mode.in_(modes))).all()
        return rows


    def get_worker_id(self, anonymousid):
        workerid = self.session.query(CodeMapping.workerid).filter_by(anonymousid=anonymousid).first()

        # row is None if not existing
        return workerid[0] if workerid else workerid


    def get_anonymous_id(self, workerid):
        anonymousid = self.session.query(CodeMapping.anonymousid).filter_by(workerid=workerid).first()

        # row is None if not existing
        return f"MTK{anonymousid[0]:05d}" if anonymousid else anonymousid


    def get_assignment_record(self, uniqueid):
        assignment = self.session.query(AcceptanceTracker).get(uniqueid)
        TableClass = get_class_by_tablename(assignment.experiment)
        record = self.session.query(TableClass).get(uniqueid)

        return record


    def get_assignments_for_worker(self, workerid):
        assignments = self.session.query(AcceptanceTracker).filter(AcceptanceTracker.workerid == workerid).all()

        return assignments


    def add_workers_from_experiment(self, experiment):
        print('---------------------------------')
        print('Adding workers from', experiment)
        print('---------------------------------')

        TableClass = get_class_by_tablename(experiment)
        master_list = Base.metadata.tables['master_list']
        acceptance = Base.metadata.tables['acceptance']


        # unique key added to master_list.workerid, so filter not needed.
        #new_subjects = self.session.query(TableClass.workerid) \
        #                      .filter(sql.and_(~sql.sql.exists() \
        #                                           .where(CodeMapping.workerid == TableClass.workerid),\
        #                                       TableClass.mode.in_(["live", "prolific"])))
        
        new_subjects = self.session.query(TableClass.workerid) \
                          .filter(TableClass.mode.in_(["live", "prolific"]))
        
        #print(TableClass, new_subjects)
        insert_stmnt = master_list.insert().from_select(names=['workerid'], 
            select=new_subjects).prefix_with('IGNORE')
        print('insert_stmnt', insert_stmnt)
        self.session.execute(insert_stmnt)

        #print('Done')
        new_subjects = self.session.query(TableClass.workerid,
                                     TableClass.uniqueid, 
                                     TableClass.assignmentid, 
                                     TableClass.hitid, 
                                     sql.literal(experiment)) \
                              .filter(sql.and_(~sql.sql.exists() \
                                                   .where(AcceptanceTracker.uniqueid == TableClass.uniqueid),
                                               TableClass.mode.in_(["live", "prolific"])))

        #print(TableClass, new_subjects)

        insert_stmnt = acceptance.insert() \
          .from_select(names=['workerid', 'uniqueid', 'assignmentid', 'hitid', 'experiment'], \
            select=new_subjects, include_defaults=True)
        print(insert_stmnt)
        self.session.execute(insert_stmnt)

        
        self.update_acceptance_tracker(experiment)

        self.session.commit()

    def get_records_for_task(self, experiment):
        TableClass = get_class_by_tablename(experiment)
        records = self.session.query(TableClass).all()

        return records


    def get_assignments_for_task(self, experiment):
        session = self.Session()
        TableClass = get_class_by_tablename(experiment)

        assignments = self.session.query(AcceptanceTracker).filter(TableClass.workerid == AcceptanceTracker.workerid).all()
        
        return assignments


    def update_acceptance_tracker(self, experiment):
        TableClass = get_class_by_tablename(experiment)

        # update paid and accepted columns
        # 5 = credited, 7 = bonused
        pre_accepted = self.session.query(TableClass.uniqueid).filter(TableClass.status.in_([5,7])).subquery()
        error_paid = self.session.query(ErrorTracker.datastring).filter(ErrorTracker.status == 7).subquery()

        self.session.query(AcceptanceTracker) \
               .filter(AcceptanceTracker.assignmentid.in_(error_paid)) \
               .update({"paid": True, "accepted": True}, synchronize_session="fetch")

        self.session.query(AcceptanceTracker) \
               .filter(AcceptanceTracker.uniqueid.in_(pre_accepted)) \
               .update({"paid": True, "accepted": True}, synchronize_session="fetch")

        self.session.commit()


    def update_payment_status(self, uniqueid, paid):
        '''
        payment reflects payment status set by mturk or manual payment
        '''

        if self.session.query(AcceptanceTracker.uniqueid).filter(AcceptanceTracker.uniqueid == uniqueid).scalar() is not None:
            self.session.query(AcceptanceTracker).filter(AcceptanceTracker.uniqueid == uniqueid).update({"paid": paid})

        self.session.commit()


    def update_acceptance_status(self, uniqueid, accept):
        '''
        acceptance reflects the payment status set by psiturk
        '''

        if self.session.query(AcceptanceTracker.uniqueid).filter(AcceptanceTracker.uniqueid == uniqueid).scalar() is not None:
            self.session.query(AcceptanceTracker).filter(AcceptanceTracker.uniqueid == uniqueid).update({"accepted": accept})

        self.session.commit()


    def update_excluded_status(self, uniqueid, exclude):

        if self.session.query(AcceptanceTracker.uniqueid).filter(AcceptanceTracker.uniqueid == uniqueid).scalar() is not None:
            self.session.query(AcceptanceTracker).filter(AcceptanceTracker.uniqueid == uniqueid).update({"excluded": exclude})

        self.session.commit()
