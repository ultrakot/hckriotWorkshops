from flask_sqlalchemy import SQLAlchemy
import enum

db = SQLAlchemy()


class UserRole(enum.Enum):
    ADMIN = ('admin', 3)
    WORKSHOP_LEADER = ('workshop_leader', 2)
    PARTICIPANT = ('participant', 1)

    def __init__(self, role_name, level):
        self.role_name = role_name
        self.level = level

    def __ge__(self, other):
        return self.level >= other.level


class Users(db.Model):
    __tablename__ = 'Users'
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.Text, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    Role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PARTICIPANT)

    # Role checking methods
    def has_role_level(self, min_role):
        """Check if user has at least the specified role level"""
        return self.Role >= min_role

    def can_manage_workshops(self):
        """Check if user can create/manage workshops"""
        return self.Role >= UserRole.WORKSHOP_LEADER

    def is_admin(self):
        """Check if user is admin"""
        return self.Role == UserRole.ADMIN

    def is_workshop_leader_for(self, workshop_id):
        """Check if user is a leader for a specific workshop"""
        return db.session.query(WorkshopLeader).filter_by(
            LeaderId=self.UserId,
            WorkshopId=workshop_id
        ).first() is not None

    def can_manage_workshop(self, workshop_id):
        """Check if user can manage a specific workshop (admin or assigned leader)"""
        return self.is_admin() or self.is_workshop_leader_for(workshop_id)

    # other methods
    def get_led_workshops(self):
        """Get all workshops this user leads"""
        return db.session.query(Workshop).join(WorkshopLeader).filter(
            WorkshopLeader.LeaderId == self.UserId
        ).all()

    CreatedDate = db.Column(db.Text, nullable=False, default=db.text("datetime('now')"))
    SupabaseId = db.Column(db.Text, unique=True, nullable=True)  # For Supabase integration
    AvatarUrl = db.Column(db.Text, nullable=True)  # For Google profile pictures

    # Relationships
    registrations = db.relationship('Registration', back_populates='user')
    skills = db.relationship('UserSkill', back_populates='user')
    led_workshops = db.relationship('WorkshopLeader', back_populates='leader')


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
    StartTime = db.Column(db.Text, nullable=False)  # 'HH:MM:SS'
    DurationMin = db.Column(db.Integer, nullable=False)
    MaxCapacity = db.Column(db.Integer, nullable=False)

    # Relationships
    registrations = db.relationship('Registration', back_populates='workshop')
    skills = db.relationship('WorkshopSkill', back_populates='workshop')
    leaders = db.relationship('WorkshopLeader', back_populates='workshop')


class WorkshopLeader(db.Model):
    __tablename__ = 'WorkshopLeader'
    # composite key
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'),  primary_key=True, index=True)
    LeaderId = db.Column(db.Integer, db.ForeignKey('Users.UserId'),  primary_key=True, index=True)
    AssignedAt = db.Column(db.Text, nullable=False, default=db.text("datetime('now')"))

    # Relationships
    workshop = db.relationship('Workshop', back_populates='leaders')
    leader = db.relationship('Users', back_populates='led_workshops')

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