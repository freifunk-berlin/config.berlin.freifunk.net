from datetime import datetime, timedelta
from app.utils import get_api
from app.models import db, IPRequest

def delete_unconfirmed_requests(hours):
    current_time = datetime.utcnow()
    two_days_ago = current_time - timedelta(hours=hours)
    qry = IPRequest.query.filter(IPRequest.created_at <
        two_days_ago).filter(IPRequest.verified == False)

    print("Found %d outdated entries." % qry.count())
    for r in qry.all():
        print("\t * %s ...\t DELETED" % r.email)
        db.session.delete(r)

    db.session.commit()

def delete_orphaned_prefixes():
  # get all ids of requests
  ids = [x.id for x in IPRequest.query.all()]
  max_id = max(ids)
  print("We have %d entries with %d as max id" % (len(ids), max_id))

  # ids are auto incremting integers, get all deleted ids
  deleted_ids = [i for i in range(0,max_id) if i not in ids]

  # check if we still have them (not deleted prefixes)
  deleted_prefixes = [(i, get_api().get_prefixes_for_id(i)) for i in deleted_ids]
  prefixes_not_deleted = [(i,prefixes) for i,prefixes in deleted_prefixes if len(prefixes) > 0]

  if len(prefixes_not_deleted) > 0:
    print("Deleting %s orphaned prefixes (%d deleted prefixes):" % (len(prefixes_not_deleted), len(deleted_ids)))

    for i, prefixes in prefixes_not_deleted:
      get_api().delete_prefixes_by_id(i)
      print("\t%d. %s" % (i, ', '.join(prefixes)))

