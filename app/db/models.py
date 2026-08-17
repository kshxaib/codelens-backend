from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

# USER MODEL: Ye table CodeLens ke users ko store karti hai.
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(    # CodeLens ka internal user ID
        primary_key=True,
        autoincrement=True 
    ) 

    github_id: Mapped[int] = mapped_column(     # GitHub ACCOUNT/User ki unique I
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )

    username: Mapped[str] = mapped_column(      # GitHub username
        String(255),
        nullable=False
    )

    avatar_url: Mapped[str | None] = mapped_column(    # GitHub profile picture URL
        String(500),
        nullable=True
    )

    github_access_token: Mapped[str | None] = mapped_column(    # GitHub OAuth access token
        String(500),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(   # CodeLens database mein user record kab create hua
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(       # User record last time kab update hua
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )



# REPOSITORY MODEL: Ye table GitHub repositories ki information store karti hai.
class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(    # CodeLens database me repository ki unique ID
        primary_key=True,
        autoincrement=True
    )

    github_id: Mapped[int] = mapped_column(     # GitHub ki unique repository ID
        BigInteger,
        unique=True,
        nullable=False,
        index=True
    )

    owner: Mapped[str] = mapped_column(    # Repository owner ka username
        String(255),
        nullable=False
    )

    name: Mapped[str] = mapped_column(     # Repository ka naam
        String(255),
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(     # owner/repository_name
        String(500),
        nullable=False
    )

    html_url: Mapped[str] = mapped_column(    # GitHub repo URL
        String(500),
        nullable=False
    )

    clone_url: Mapped[str] = mapped_column(    # git@github.com:owner/repo.git
        String(500),
        nullable=False
    )

    private: Mapped[bool] = mapped_column(    # public/private
        nullable=False,
        default=False
    )

    default_branch: Mapped[str | None] = mapped_column(    # main/master
        String(255),
        nullable=True
    )

    description: Mapped[str | None] = mapped_column(    # repo description
        String(1000),
        nullable=True
    )

    # Repository indexing ki current state: not_indexed, indexing, indexed, failed
    index_status: Mapped[str] = mapped_column(
        String(50),
        default="not_indexed",
        nullable=False
    )

    # Last indexed Git commit ka SHA
    # Isse pata chalega repository ka kaunsa version index hua tha
    last_indexed_commit: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    # Repository last kab index hui
    last_indexed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    # Indexing ke time kitne files scan hue
    file_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # Indexing ke time kitne symbols mile
    # Example: functions, classes, methods etc.
    # Initially 0, later indexing/parsing ke baad actual count
    symbol_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(   # CodeLens database mein repository record kab create hua
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(   # Repository record last time kab update hua
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )



# REPOSITORY ACCESS MODEL: Kaunsa user kis repository ko access kar sakta hai?
#USER <-> REPOSITORY ACCESS
#Repository table sirf repository ki information rakhti hai.
#Ye check karta hai ki CURRENT USER ko is repository ka access hai ya nahi.
class RepositoryAccess(Base):
    __tablename__ = "repository_access"
    
    id: Mapped[int] = mapped_column(    # Access record ki unique ID
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(    # Kis user ko repository ka access hai
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    repository_id: Mapped[int] = mapped_column(    # Kis repository ka access hai
        ForeignKey(
            "repositories.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    permission: Mapped[str] = mapped_column(    # User ke paas repository me kya permission hai: read, write, admin
        String(50),
        default="read",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(   # Access record kab create hua
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(   # Access record last kab update hua
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Same user + same repository ka duplicate access record create nahi hone dena
    # Example: user_id = 1 and repository_id = 5
    # Ye combination sirf ek baar allowed hai
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "repository_id",
            name="uq_user_repository_access"
        ),
    )