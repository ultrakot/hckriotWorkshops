import enum

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()


class UserRole(str, enum.Enum):
    ADMIN = 'ADMIN'
    WORKSHOP_LEADER = 'WORKSHOP_LEADER'
    PARTICIPANT = 'PARTICIPANT'

    @property
    def level(self) -> int:
        """Returns the level for the role."""
        level_map = {
            UserRole.ADMIN: 100,
            UserRole.WORKSHOP_LEADER: 2,
            UserRole.PARTICIPANT: 1
        }
        return level_map[self]

    def __ge__(self, other):
        """Enable hierarchical comparison (e.g., ADMIN >= PARTICIPANT)."""
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.level >= other.level


class RegistrationStatus(str, enum.Enum):
    """Possible statuses for a workshop registration."""
    REGISTERED = 'REGISTERED'
    WAITLISTED = 'WAITLISTED'
    CANCELLED = 'CANCELLED'


class Users(db.Model):
    __tablename__ = 'Users'
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.Text, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    Role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.PARTICIPANT)
    CreatedDate = db.Column(db.DateTime, nullable=False, default=func.now())
    SupabaseId = db.Column(db.Text, unique=True, nullable=True)
    AvatarUrl = db.Column(db.Text, nullable=True)

    # skills questionnaire
    HasFilledSkillsQuestionnaire = db.Column(db.Boolean, nullable=False, default=False)

    # for workshop leaders
    # LinkedinUrl = db.Column(db.Text, nullable=True, default="")
    # ImageUrl = db.Column(db.Text, nullable=True, default="")
    JobTitle = db.Column(db.Text, nullable=True, default="")

    # Relationships
    registrations = db.relationship('Registration', back_populates='user', lazy='selectin')
    skills = db.relationship('UserSkill', back_populates='user', lazy='selectin')
    led_workshops = db.relationship('WorkshopLeader', back_populates='leader')

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
    Grade = db.Column(db.Integer, nullable=False)

    # Relationships
    user = db.relationship('Users', back_populates='skills')
    skill = db.relationship('Skill', back_populates='user_skills', lazy='joined')


class Workshop(db.Model):
    __tablename__ = 'Workshop'
    WorkshopId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Title = db.Column(db.Text, nullable=False)
    Description = db.Column(db.Text, nullable=False, default="")
    SessionDateTime = db.Column(db.DateTime(timezone=True), nullable=False)
    DurationMin = db.Column(db.Integer, nullable=False)
    MaxCapacity = db.Column(db.Integer, nullable=False)
    Prerequisite = db.Column(db.Text, nullable=False, default="")
    RequiredInstallations = db.Column(db.Text, nullable=False, default="")
    Track = db.Column(db.Text, nullable=False, default="")

    # Relationships
    registrations = db.relationship('Registration', back_populates='workshop')
    skills = db.relationship('WorkshopSkill', back_populates='workshop')
    leaders = db.relationship('WorkshopLeader', back_populates='workshop')


class WorkshopLeader(db.Model):
    __tablename__ = 'WorkshopLeader'
    # composite key
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), primary_key=True, index=True)
    LeaderId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), primary_key=True, index=True)
    AssignedAt = db.Column(db.Text, nullable=False, default=db.text("datetime('now')"))

    # Relationships
    workshop = db.relationship('Workshop', back_populates='leaders', lazy='joined')
    leader = db.relationship('Users', back_populates='led_workshops', lazy='joined')


class WorkshopSkill(db.Model):
    __tablename__ = 'WorkshopSkill'
    WorkshopSkillId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), nullable=False)
    SkillId = db.Column(db.Integer, db.ForeignKey('Skill.SkillId'), nullable=False)

    # Relationships
    workshop = db.relationship('Workshop', back_populates='skills', lazy='joined')
    skill = db.relationship('Skill', back_populates='workshop_skills', lazy='joined')


class Registration(db.Model):
    __tablename__ = 'Registration'
    __table_args__ = (
        db.UniqueConstraint('UserId', 'WorkshopId', name='unique_user_workshop_registration'),
        db.Index('idx_registration_workshop_status', 'WorkshopId', 'Status'),
    )

    RegistrationId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), nullable=False)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    RegisteredAt = db.Column(db.Text, nullable=False, default=db.text("datetime('now')"))
    Status = db.Column(db.Enum(RegistrationStatus), nullable=False)

    # Relationships
    workshop = db.relationship('Workshop', back_populates='registrations', lazy='joined')
    user = db.relationship('Users', back_populates='registrations')
