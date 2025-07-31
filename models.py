"""
Cleaned Models - Removed unnecessary lookup tables
"""
import enum
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
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
    REGISTERED = 'Registered'
    WAITLISTED = 'Waitlisted'
    CANCELLED = 'Cancelled'
    
    @property
    def status_id(self) -> int:
        """Returns the integer ID for the status."""
        status_map = {
            RegistrationStatus.REGISTERED: 1,
            RegistrationStatus.WAITLISTED: 2,
            RegistrationStatus.CANCELLED: 3
        }
        return status_map[self]


class Users(db.Model):
    __tablename__ = 'Users'
    UserId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.Text, nullable=False)
    Email = db.Column(db.Text, unique=True, nullable=False)
    _role = db.Column('Role', db.Integer, nullable=False, default=1)
    CreatedDate = db.Column(db.DateTime, nullable=False, default=func.now())
    SupabaseId = db.Column(db.Text, unique=True, nullable=True)
    AvatarUrl = db.Column(db.Text, nullable=True)

    # Hybrid property for Role conversion
    @hybrid_property
    def Role(self):
        """Convert integer role to UserRole enum."""
        role_mapping = {
            1: UserRole.PARTICIPANT,
            2: UserRole.WORKSHOP_LEADER,
            100: UserRole.ADMIN
        }
        return role_mapping.get(self._role, UserRole.PARTICIPANT)
    
    @Role.setter
    def Role(self, value):
        """Set role from UserRole enum or integer."""
        if isinstance(value, UserRole):
            enum_to_int = {
                UserRole.PARTICIPANT: 1,
                UserRole.WORKSHOP_LEADER: 2,
                UserRole.ADMIN: 100
            }
            self._role = enum_to_int[value]
        elif isinstance(value, int):
            self._role = value
        else:
            raise ValueError(f"Role must be UserRole enum or integer, got {type(value)}")

    # Relationships
    registrations = db.relationship('Registration', back_populates='user')
    skills = db.relationship('UserSkill', back_populates='user')
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

    # Relationships
    registrations = db.relationship('Registration', back_populates='workshop')
    skills = db.relationship('WorkshopSkill', back_populates='workshop')
    leaders = db.relationship('WorkshopLeader', back_populates='workshop')


class WorkshopLeader(db.Model):
    __tablename__ = 'WorkshopLeader'
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), primary_key=True, index=True)
    LeaderId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), primary_key=True, index=True)
    AssignedAt = db.Column(db.DateTime, nullable=False, default=func.now())

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
    __table_args__ = (
        db.UniqueConstraint('UserId', 'WorkshopId', name='unique_user_workshop_registration'),
        db.Index('idx_registration_workshop_status', 'WorkshopId', 'Status'),
    )
    
    RegistrationId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WorkshopId = db.Column(db.Integer, db.ForeignKey('Workshop.WorkshopId'), nullable=False)
    UserId = db.Column(db.Integer, db.ForeignKey('Users.UserId'), nullable=False)
    RegisteredAt = db.Column(db.DateTime, nullable=False, default=func.now())
    _status = db.Column('Status', db.Integer, nullable=False, default=1)

    # Hybrid property for Status conversion
    @hybrid_property
    def Status(self):
        """Convert integer status to RegistrationStatus enum."""
        status_mapping = {
            1: RegistrationStatus.REGISTERED,
            2: RegistrationStatus.WAITLISTED,
            3: RegistrationStatus.CANCELLED
        }
        return status_mapping.get(self._status, RegistrationStatus.REGISTERED)
    
    @Status.setter
    def Status(self, value):
        """Set status from RegistrationStatus enum or integer."""
        if isinstance(value, RegistrationStatus):
            enum_to_int = {
                RegistrationStatus.REGISTERED: 1,
                RegistrationStatus.WAITLISTED: 2,
                RegistrationStatus.CANCELLED: 3
            }
            self._status = enum_to_int[value]
        elif isinstance(value, int):
            self._status = value
        else:
            raise ValueError(f"Status must be RegistrationStatus enum or integer, got {type(value)}")

    # Relationships
    workshop = db.relationship('Workshop', back_populates='registrations')
    user = db.relationship('Users', back_populates='registrations')

# REMOVED: RoleTypes and StatusTypes tables (unused lookup tables)