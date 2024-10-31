# class User:
#     def __init__(self, id, username, password, role):
#         self.id = id
#         self.username = username
#         self.password = password
#         self.role = role

#     def __repr__(self):
#         return f"<User {self.id}>"

# class Portfolio:
#     def __init__(self, id, user_id, title, content, created_at):
#         self.id = id
#         self.user_id = user_id
#         self.title = title
#         self.content = content
#         self.created_at = created_at

#     def __repr__(self):
#         return f"<Portfolio {self.id}>"
    
class User:
    def __init__(self, id, username, password, role, student_number=None, name=None, grade=None, graduation_year=None, bio=None):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.student_number = student_number
        self.name = name
        self.grade = grade
        self.graduation_year = graduation_year
        self.bio = bio

    def __repr__(self):
        return f"<User {self.id}>"

class Portfolio:
    def __init__(self, id, user_id, title, content, created_at):
        self.id = id
        self.user_id = user_id
        self.title = title
        self.content = content
        self.created_at = created_at

    def __repr__(self):
        return f"<Portfolio {self.id}>"