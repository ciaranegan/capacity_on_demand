from sqlalchemy import create_engine

class QoSTracker:

    def __init__(self):
        self.engine = create_engine('sqlite:///my_db.sqlite')
        print "HELLO THERE"
