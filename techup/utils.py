
def user_can_access(user, project):
    if user == project.user or user.profile.is_staff or user.profile.is_admin:
        return True
    
    return False
