"""
LeaderboardSnapshot Model
Leaderboard rankings at different time periods
"""

import uuid

from app import db


class LeaderboardSnapshot(db.Model):
    """
    LeaderboardSnapshot model for tracking leaderboard rankings over time.

    Attributes:
        snapshot_id: UUID primary key
        user_id: Foreign key to User
        rank: Rank position
        points: Points at snapshot time
        timeframe: ENUM(daily, weekly, monthly, all_time)
        snapshot_date: Date of snapshot
    """

    __tablename__ = "leaderboard_snapshots"

    # Primary Key
    snapshot_id = db.Column(
        db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False
    )

    # Foreign Key
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    # Ranking Data
    rank = db.Column(db.Integer, nullable=True)
    points = db.Column(db.Integer, nullable=True)

    # Timeframe
    timeframe = db.Column(
        db.Enum("daily", "weekly", "monthly", "all_time"), nullable=False, index=True
    )
    snapshot_date = db.Column(db.Date, nullable=True, index=True)

    def __repr__(self):
        return f"<LeaderboardSnapshot {self.snapshot_id} - Rank {self.rank}>"

    def to_dict(self):
        """Convert snapshot to dictionary for JSON serialization."""
        return {
            "snapshot_id": self.snapshot_id,
            "user_id": self.user_id,
            "rank": self.rank,
            "points": self.points,
            "timeframe": self.timeframe,
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
        }
