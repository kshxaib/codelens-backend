from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


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



class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(    # CodeLens ka internal repository ID
        primary_key=True,
        autoincrement=True
    )

    github_id: Mapped[int] = mapped_column(     # GitHub repository ki unique ID
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