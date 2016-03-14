from ryu.app.qos.dbconnection import DBConnection

class ReservationManager:

    def __init__(self, db_path):
        self.db = DBConnection(db_path)


    def add_reservation(self, res_info):
        # Check if such a reservation already exists
        exists = self.db.get_reservation_for_src_dst(res_info["src"], res_info["dst"])
        if exists:
            return exists.id

        # Check if such a reservation is possible
        if self.is_reservation_possible(res_info["src"], res_info["dst"], res_info["bw"]):
            reservation = self.db.add_reservation(res_info)
            return reservation.id

        # Return null if reservation isn't possible
        return None


    def update_reservation(self, res_id, new_bw):
        res = self.db.get_reservation_for_id(res_id)
        if not res:
            return None

        if new_bw > res.bw:
            # If the new bw is greater then we need to check if it's possible
            if not self.is_reservation_possible(res.src, res.dst, new_bw):
                return None

        res = self.db.upate_bw_for_reservation(res.id, new_bw)
        if not res:
            return None

        return res.id


    def is_reservation_possible(self, src, dst, bw):
        # TODO: implement this
        return True
