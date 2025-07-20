from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'Users'
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.Text, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    CreatedDate = db.Column(db.Text, nullable=False, default=db.text("datetime('now')"))
    SupabaseId = db.Column(db.Text, unique=True, nullable=True)  # For Supabase integration
    AvatarUrl = db.Column(db.Text, nullable=True)  # For Google profile pictures
    
    # Relationships
    registrations = db.relationship('Registration', back_populates='user')
    skills = db.relationship('UserSkill', back_populates='user')

class Skill(db.Model):
    __tablename__ = 'Skill'
    SkillId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.Text, unique=True, nullable=False)
    
    # Relationships
    user_skills = db.relationship('UserSkill', back_populates='skill')
    workshop_skills = db.relationship('WorkshopSkill', back_populates='skill')

class UserSkill(db.Model):
    __tablename__ = 'UserSkill'
    UserSkillId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    SkillId = db.Column(db.Integer, db.ForeignKey('Skill.SkillId'), nullable=False)
    Grade = db.Column(db.Integer, nullable=False)  # CHECK constraint handled at DB level
    
    # Relationships
    user = db.relationship('Users', back_populates='skills')
    skill = db.relationship('Skill', back_populates='user_skills')

class Workshop(db.Model):
    __tablename__ = 'Workshop'
    WorkshopId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.Text, nullable=False)
    Description = db.Column(db.Text, nullable=True)
    SessionDate = db.Column(db.Text, nullable=False)  # 'YYYY-MM-DD'
    StartTime = db.Column(db.Text, nullable=False)    # 'HH:MM:SS'
    DurationMin = db.Column(db.Integer, nullable=False)
    MaxCapacity = db.Column(db.Integer, nullable=False)
    
    # Relationships
    registrations = db.relationship('Registration', back_populates='workshop')
    skills = db.relationship('WorkshopSkill', back_populates='workshop')

class WorkshopSkill(db.Model):
    __tablename__ = 'WorkshopSkill'
    WorkshopSkillId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), nullable=False)
    SkillId = db.Column(db.Integer, db.ForeignKey('Skill.SkillId'), nullable=False)
    
    # Relationships
    workshop = db.relationship('Workshop', back_populates='skills')
    skill = db.relationship('Skill', back_populates='workshop_skills')

class Registration(db.Model):
    __tablename__ = 'Registration'
    RegistrationId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), nullable=False)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    RegisteredAt = db.Column(db.Text, nullable=False, default=db.text("datetime('now')"))
    Status = db.Column(db.Text, nullable=False)  # CHECK constraint handled at DB level
    
    # Relationships
    workshop = db.relationship('Workshop', back_populates='registrations')
    user = db.relationship('Users', back_populates='registrations') 