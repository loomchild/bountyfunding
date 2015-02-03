#This is future data access layer

from bountyfunding.api.models import db, User

def retrieve_user(project_id, name):
	user = User.query.filter_by(project_id=project_id, name=name).first()
	return user


